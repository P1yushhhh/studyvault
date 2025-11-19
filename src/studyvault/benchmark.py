#!/usr/bin/env python
"""
StudyVault Benchmark Harness

Measures:
- ImportService.import_from_directory
- SearchService.build_index
- SearchService.search (avg across queries)
- LibraryRepository.save_library / load_library

Generates synthetic datasets by file type & size profile.

USAGE (from project root):
  python benchmark_studyvault.py --scales 100 500 1000 --profile small --reps 2 --mem

Notes:
- No external deps. Uses stdlib only.
- Creates benchmark artifacts under data/benchmarks/<timestamp>/
- Cleans synthetic dataset by default (use --keep to preserve)
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import shutil
import string
import sys
import tempfile
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Iterable, Optional

# --- Make sure 'src' is importable when run as a script from project root ---
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# --- StudyVault imports (assumes your package is in src/studyvault) ---
from studyvault.services.import_service import ImportService
from studyvault.services.search_service import SearchService
from studyvault.repositories.library_repository import LibraryRepository, LibraryData
from studyvault.models.item import Item

try:
    import tracemalloc  # optional
    TRACEMALLOC_AVAILABLE = True
except Exception:
    TRACEMALLOC_AVAILABLE = False


# ---------------------------
# Synthetic data generation
# ---------------------------

TEXT_EXTS = [".txt", ".md"]
DOC_EXTS = [".pdf", ".docx", ".ppt"]
MEDIA_EXTS = [".mp3", ".mp4"]

ALL_EXTS = TEXT_EXTS + DOC_EXTS + MEDIA_EXTS

SIZE_PROFILES = {
    # Average target sizes per type (bytes)
    # (min, max) sampled uniformly for a bit of variance
    "small": {
        ".txt":  (1_000, 4_000),
        ".md":   (1_000, 4_000),
        ".pdf":  (40_000, 80_000),
        ".docx": (40_000, 80_000),
        ".ppt": (60_000, 120_000),
        ".mp3":  (150_000, 300_000),
        ".mp4":  (300_000, 800_000),
    },
    "medium": {
        ".txt":  (4_000, 16_000),
        ".md":   (4_000, 16_000),
        ".pdf":  (200_000, 500_000),
        ".docx": (200_000, 500_000),
        ".ppt": (300_000, 800_000),
        ".mp3":  (1_000_000, 2_000_000),
        ".mp4":  (3_000_000, 8_000_000),
    },
    "large": {
        ".txt":  (20_000, 80_000),
        ".md":   (20_000, 80_000),
        ".pdf":  (2_000_000, 5_000_000),
        ".docx": (2_000_000, 5_000_000),
        ".ppt": (3_000_000, 10_000_000),
        ".mp3":  (5_000_000, 12_000_000),
        ".mp4":  (12_000_000, 40_000_000),
    },
}


def _rand_bytes(n: int) -> bytes:
    # Random but compressible-ish bytes; for text we generate readable text separately.
    return os.urandom(n)


def _rand_text(n: int) -> str:
    words = ["ai", "ml", "dl", "nlp", "cv", "study", "vault", "notes", "lecture", "assignment",
             "python", "cloud", "agent", "vector", "search", "index", "tag", "benchmark", "import"]
    out: List[str] = []
    total = 0
    while total < n:
        w = random.choice(words)
        out.append(w)
        total += len(w) + 1
    return " ".join(out)


def _write_file(path: Path, size_range: Tuple[int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lo, hi = size_range
    target = random.randint(lo, hi)
    if path.suffix in TEXT_EXTS:
        text = _rand_text(target)
        path.write_text(text[:target], encoding="utf-8", errors="ignore")
    else:
        path.write_bytes(_rand_bytes(target))


def generate_dataset(root: Path, total_files: int, profile: str) -> Dict[str, int]:
    """
    Create a synthetic directory tree with mixed file types & sizes.
    Returns a count per extension actually generated.
    """
    if profile not in SIZE_PROFILES:
        raise ValueError(f"Unknown profile '{profile}'. Choose from {list(SIZE_PROFILES.keys())}.")
    size_map = SIZE_PROFILES[profile]

    # Heuristic distribution across types (adjustable)
    # ~40% text, 35% docs, 25% media
    text_target = int(total_files * 0.40)
    doc_target = int(total_files * 0.35)
    media_target = total_files - text_target - doc_target

    counts = defaultdict(int)

    def make_files(count: int, exts: List[str], subdir: str):
        for i in range(count):
            ext = random.choice(exts)
            # create nested dirs for realism
            sub = root / subdir / f"batch_{i // 50}" / f"group_{i % 50}"
            fname = f"item_{i:05d}{ext}"
            _write_file(sub / fname, size_map[ext])
            counts[ext] += 1

    make_files(text_target, TEXT_EXTS, "notes")
    make_files(doc_target, DOC_EXTS, "documents")
    make_files(media_target, MEDIA_EXTS, "media")
    return dict(counts)


# ---------------------------
# Timing helpers
# ---------------------------

@dataclass
class BenchResult:
    scale: int
    profile: str
    rep: int
    imported: int
    t_import_ms: float
    t_index_ms: float
    t_search_avg_ms: float
    t_save_ms: float
    t_load_ms: float
    peak_mb: Optional[float] = None


def _ms(start: float, end: float) -> float:
    return (end - start) * 1000.0


def measure_memory_start(enable: bool):
    if enable and TRACEMALLOC_AVAILABLE:
        tracemalloc.start()
        return True
    return False


def measure_memory_stop(enabled: bool) -> Optional[float]:
    if enabled and TRACEMALLOC_AVAILABLE:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return peak / (1024 * 1024)
    return None


# ---------------------------
# Benchmark steps
# ---------------------------

def run_benchmark_once(
    work_dir: Path,
    scale: int,
    profile: str,
    rep: int,
    search_queries: Iterable[str],
    data_dir: Path,
    measure_mem: bool
) -> BenchResult:
    dataset_dir = work_dir / f"dataset_{scale}_{profile}_rep{rep}"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    # 1) Generate dataset
    generate_dataset(dataset_dir, scale, profile)

    # 2) Import
    mem_on = measure_memory_start(measure_mem)
    t0 = time.perf_counter()
    importer = ImportService()
    items = importer.import_from_directory(dataset_dir)
    t1 = time.perf_counter()

    # 3) Index
    search = SearchService()
    t2 = time.perf_counter()
    search.build_index(items)
    t3 = time.perf_counter()

    # 4) Search (average over queries)
    item_map = {it.id: it for it in items}
    search_times = []
    for q in search_queries:
        s0 = time.perf_counter()
        _ = search.search(q, item_map)
        s1 = time.perf_counter()
        search_times.append(_ms(s0, s1))
    avg_search_ms = sum(search_times) / max(1, len(search_times))

    # 5) Save / Load
    repo = LibraryRepository(data_file=data_dir / f"library_{scale}_{profile}_rep{rep}.dat")

    t4 = time.perf_counter()
    repo.save_library(LibraryData(items=items))
    t5 = time.perf_counter()

    t6 = time.perf_counter()
    _ = repo.load_library()
    t7 = time.perf_counter()

    peak_mb = measure_memory_stop(mem_on)

    return BenchResult(
        scale=scale,
        profile=profile,
        rep=rep,
        imported=len(items),
        t_import_ms=_ms(t0, t1),
        t_index_ms=_ms(t2, t3),
        t_search_avg_ms=avg_search_ms,
        t_save_ms=_ms(t4, t5),
        t_load_ms=_ms(t6, t7),
        peak_mb=peak_mb
    )


# ---------------------------
# CLI / Orchestration
# ---------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Benchmark StudyVault import/index/search/save-load with synthetic datasets."
    )
    p.add_argument("--scales", type=int, nargs="+", default=[100, 500, 1000],
                   help="Total files per dataset to generate (e.g., 100 500 1000).")
    p.add_argument("--profile", choices=list(SIZE_PROFILES.keys()),nargs="+", default="small",
                   help="Size profile for generated files.")
    p.add_argument("--reps", type=int, default=1, help="Repetitions per scale.")
    p.add_argument("--keep", action="store_true", help="Keep synthetic datasets after run.")
    p.add_argument("--mem", action="store_true", help="Measure peak memory via tracemalloc.")
    p.add_argument("--queries", nargs="*", default=["ai", "notes", "lecture", "python", "tag"],
                   help="Queries to run for the search benchmark.")
    return p.parse_args()


def ensure_dirs() -> Tuple[Path, Path]:
    bench_root = PROJECT_ROOT / "data" / "benchmarks" / datetime.now().strftime("%Y%m%d_%H%M%S")
    bench_root.mkdir(parents=True, exist_ok=True)
    data_dir = bench_root / "artifacts"
    data_dir.mkdir(parents=True, exist_ok=True)
    return bench_root, data_dir


def write_csv(results: List[BenchResult], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        header = ["scale", "profile", "rep", "imported",
                  "t_import_ms", "t_index_ms", "t_search_avg_ms",
                  "t_save_ms", "t_load_ms", "peak_mb"]
        w.writerow(header)
        for r in results:
            w.writerow([
                r.scale, r.profile, r.rep, r.imported,
                f"{r.t_import_ms:.2f}", f"{r.t_index_ms:.2f}", f"{r.t_search_avg_ms:.2f}",
                f"{r.t_save_ms:.2f}", f"{r.t_load_ms:.2f}",
                f"{r.peak_mb:.2f}" if r.peak_mb is not None else ""
            ])


def print_summary(results: List[BenchResult]) -> None:
    # Simple text table without external deps
    def row(cols, widths):
        return " | ".join(str(c).ljust(w) for c, w in zip(cols, widths))

    header = ["Scale", "Prof", "Rep", "Items", "Import(ms)", "Index(ms)", "SearchAvg(ms)", "Save(ms)", "Load(ms)", "PeakMB"]
    widths = [6, 5, 3, 6, 11, 10, 14, 8, 8, 7]
    print("\n" + row(header, widths))
    print("-" * (sum(widths) + 3 * (len(widths) - 1)))
    for r in results:
        cols = [
            r.scale, r.profile[:5], r.rep, r.imported,
            f"{r.t_import_ms:.1f}",
            f"{r.t_index_ms:.1f}",
            f"{r.t_search_avg_ms:.2f}",
            f"{r.t_save_ms:.1f}",
            f"{r.t_load_ms:.1f}",
            f"{r.peak_mb:.1f}" if r.peak_mb is not None else "-"
        ]
        print(row(cols, widths))


def main():
    args = parse_args()
    bench_root, data_dir = ensure_dirs()

    print(f"[StudyVault Benchmark]")
    print(f"- Output dir: {bench_root}")
    print(f"- Scales: {args.scales} | Profiles: {args.profile} | Reps: {args.reps}")
    print(f"- Queries: {args.queries}")
    print(f"- Keep datasets: {args.keep} | Mem: {args.mem}\n")

    results: List[BenchResult] = []
    datasets_to_cleanup: List[Path] = []

    try:
        for scale in args.scales:
            for profile in args.profile:  # <-- loop over profiles
                for rep in range(1, args.reps + 1):
                    work_dir = bench_root / f"work_{scale}_{profile}_rep{rep}"
                    work_dir.mkdir(parents=True, exist_ok=True)
                    datasets_to_cleanup.append(work_dir)

                    res = run_benchmark_once(
                        work_dir=work_dir,
                        scale=scale,
                        profile=profile,  # <-- pass correct single value
                        rep=rep,
                        search_queries=args.queries,
                        data_dir=data_dir,
                        measure_mem=args.mem
                    )
                    results.append(res)
                    print(
                        f"✓ scale={scale} profile={profile} rep={rep}: "
                        f"items={res.imported} import={res.t_import_ms:.1f}ms "
                        f"index={res.t_index_ms:.1f}ms search_avg={res.t_search_avg_ms:.2f}ms "
                        f"save={res.t_save_ms:.1f}ms load={res.t_load_ms:.1f}ms "
                        f"peak={'{:.1f}MB'.format(res.peak_mb) if res.peak_mb is not None else '-'}"
                    )

        out_csv = bench_root / "results.csv"
        write_csv(results, out_csv)
        print_summary(results)
        print(f"\nCSV written: {out_csv}")

    finally:
        if not args.keep:
            for wd in datasets_to_cleanup:
                shutil.rmtree(wd, ignore_errors=True)



if __name__ == "__main__":
    main()
