"""
Main Controller - Core orchestrator for StudyVault application.

Handles all user interactions: CRUD operations, search, import, tasks, and media preview.
Connects services (library, search, import) to the UI (views/widgets).
Implements animations, dialogs, and error handling.
"""

from typing import Optional, List
from pathlib import Path
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QLabel,
    QMessageBox, QDialog, QDialogButtonBox, QGridLayout, QVBoxLayout,
    QHBoxLayout, QSlider, QFileDialog, QDateEdit
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QDate
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from studyvault.models.item import Item
from studyvault.models.task import Task
from studyvault.services.library_service import LibraryService
from studyvault.services.search_service import SearchService
from studyvault.services.import_service import ImportService
from studyvault.repositories.library_repository import LibraryData
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)


class MainController:
    """
    Main application controller.
    
    Connects UI widgets to business logic services. Handles all user actions
    including CRUD operations, search, import, task management, and media preview.
    
    Architecture:
    - Services: LibraryService (items/tasks), SearchService (indexing), ImportService (file scan)
    - UI: PyQt6 widgets passed in constructor
    - Data flow: User action → Controller → Service → Model → Controller → UI update
    
    Example:
        >>> controller = MainController(table, search_field, task_label)
        >>> controller.initialize()
    """
    
    def __init__(
        self,
        items_table: QTableWidget,
        search_field: QLineEdit,
        task_count_label: QLabel,
        add_button: QPushButton,
        edit_button: QPushButton,
        delete_button: QPushButton,
        undo_button: QPushButton,
        search_button: QPushButton,
        import_button: QPushButton,
        add_task_button: QPushButton,
        view_task_button: QPushButton,
        preview_button: QPushButton
    ):
        """
        Initialize main controller with UI widgets.
        
        Args:
            items_table: QTableWidget for displaying items
            search_field: QLineEdit for search input
            task_count_label: QLabel showing task count
            *_button: Various QPushButton widgets for actions
        """
        # UI Widgets
        self.items_table = items_table
        self.search_field = search_field
        self.task_count_label = task_count_label
        
        # Buttons (store for potential enable/disable)
        self.add_button = add_button
        self.edit_button = edit_button
        self.delete_button = delete_button
        self.undo_button = undo_button
        self.search_button = search_button
        self.import_button = import_button
        self.add_task_button = add_task_button
        self.view_task_button = view_task_button
        self.preview_button = preview_button
        
        # Services
        self.library_service = LibraryService()
        self.search_service = SearchService()
        self.import_service = ImportService()
        
        # Media player (for preview)
        self.media_player: Optional[QMediaPlayer] = None
        
        logger.debug("MainController initialized")
    
    def initialize(self) -> None:
        """
        Initialize controller - setup table, connect signals, load data.
        
        Call this after construction to set up the UI.
        """
        # Setup table columns
        self._setup_table()
        
        # Connect button signals to handlers
        self._connect_signals()
        
        # Add fade-in animation for table
        self._animate_fade_in(self.items_table, duration=800)
        
        logger.info("MainController initialized and ready")
    
    def _setup_table(self) -> None:
        """Configure table columns and settings."""
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            "Title", "Category", "Type", "Rating", "Tags"
        ])
        
        # Enable sorting
        self.items_table.setSortingEnabled(True)
        
        # Set column widths
        self.items_table.setColumnWidth(0, 200)  # Title
        self.items_table.setColumnWidth(1, 150)  # Category
        self.items_table.setColumnWidth(2, 100)  # Type
        self.items_table.setColumnWidth(3, 80)   # Rating
        self.items_table.setColumnWidth(4, 200)  # Tags
    
    def _connect_signals(self) -> None:
        """Connect button clicks to handler methods."""
        self.add_button.clicked.connect(self.handle_add)
        self.edit_button.clicked.connect(self.handle_edit)
        self.delete_button.clicked.connect(self.handle_delete)
        self.undo_button.clicked.connect(self.handle_undo)
        self.search_button.clicked.connect(self.handle_search)
        self.import_button.clicked.connect(self.handle_import)
        self.add_task_button.clicked.connect(self.handle_add_task)
        self.view_task_button.clicked.connect(self.handle_view_next_task)
        self.preview_button.clicked.connect(self.handle_preview)
        
        # Search on Enter key
        self.search_field.returnPressed.connect(self.handle_search)
    
    # ===== CRUD Operations =====
    
    def handle_add(self) -> None:
        """
        Handle Add button click.
        
        Creates a test item for now. In full app, would open dialog for user input.
        """
        # Create sample item (TODO: Replace with dialog)
        new_item = Item("Sample Note", "Study", "note")
        new_item.set_rating(4)
        
        # Add to service
        self.library_service.add_item(new_item)
        
        # Update table
        self._refresh_table()
        
        # Animate
        self._animate_fade_in(self.items_table, duration=400, start_opacity=0.5)
        
        logger.info(f"Item added: {new_item.title}")
        self._show_alert("Success", "Item added successfully!")
    
    def handle_edit(self) -> None:
        """
        Handle Edit button click.
        
        Opens dialog to edit selected item's properties.
        """
        # Get selected item
        selected_item = self._get_selected_item()
        if not selected_item:
            self._show_alert("No Selection", "Please select an item to edit.")
            return
        
        # Create edit dialog
        dialog = QDialog()
        dialog.setWindowTitle("Edit Item")
        dialog.resize(400, 300)
        
        # Add scale animation on show
        dialog.showEvent = lambda event: self._animate_scale(dialog, duration=200)
        
        # Create form layout
        layout = QGridLayout()
        layout.setSpacing(10)
        
        # Title field
        title_label = QLabel("Title:")
        title_field = QLineEdit(selected_item.title)
        layout.addWidget(title_label, 0, 0)
        layout.addWidget(title_field, 0, 1)
        
        # Category field
        category_label = QLabel("Category:")
        category_field = QLineEdit(selected_item.category)
        layout.addWidget(category_label, 1, 0)
        layout.addWidget(category_field, 1, 1)
        
        # Tags field
        tags_label = QLabel("Tags (comma separated):")
        tags_field = QLineEdit(", ".join(selected_item.tags))
        layout.addWidget(tags_label, 2, 0)
        layout.addWidget(tags_field, 2, 1)
        
        # Rating slider
        rating_label = QLabel("Rating:")
        rating_slider = QSlider(Qt.Orientation.Horizontal)
        rating_slider.setMinimum(1)
        rating_slider.setMaximum(5)
        rating_slider.setValue(selected_item.rating)
        rating_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        rating_slider.setTickInterval(1)
        layout.addWidget(rating_label, 3, 0)
        layout.addWidget(rating_slider, 3, 1)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box, 4, 0, 1, 2)
        
        dialog.setLayout(layout)
        
        # Show dialog and handle result
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update item
            selected_item.title = title_field.text()
            selected_item.category = category_field.text()
            selected_item.set_rating(rating_slider.value())
            
            # Parse tags
            selected_item.tags.clear()
            for tag in tags_field.text().split(','):
                tag_clean = tag.strip()
                if tag_clean:
                    selected_item.add_tag(tag_clean)
            
            # Refresh table
            self._refresh_table()
            
            logger.info(f"Item edited: {selected_item.title}")
            self._show_alert("Success", "Item updated successfully!")
    
    def handle_delete(self) -> None:
        """Handle Delete button click."""
        selected_item = self._get_selected_item()
        if not selected_item:
            self._show_alert("No Selection", "Please select an item to delete.")
            return
        
        # Delete from service (creates memento for undo)
        self.library_service.delete_item(selected_item)
        
        # Refresh table
        self._refresh_table()
        
        logger.info(f"Item deleted: {selected_item.title}")
        self._show_alert("Success", "Item deleted!")
    
    def handle_undo(self) -> None:
        """Handle Undo button click."""
        if not self.library_service.can_undo():
            self._show_alert("Nothing to Undo", "No actions to undo.")
            return
        
        # Undo last operation
        self.library_service.undo()
        
        # Refresh table
        self._refresh_table()
        
        logger.info("Undo completed")
        self._show_alert("Success", "Undo completed!")
    
    # ===== Search Operations =====
    
    def handle_search(self) -> None:
        """
        Handle Search button click or Enter key in search field.
        
        Searches items by keyword and updates table with results.
        """
        query = self.search_field.text().strip()
        
        # If empty, show all items
        if not query:
            self._refresh_table()
            return
        
        logger.info(f"Searching for: {query}")
        
        # Build index if not already built
        self.search_service.build_index(self.library_service.get_items())
        
        # Create item map for search
        item_map = {item.id: item for item in self.library_service.get_items()}
        
        # Search
        result_ids = self.search_service.search(query, item_map)
        
        # Get items from IDs
        results = [item_map[item_id] for item_id in result_ids if item_id in item_map]
        
        # Update table with results
        self._refresh_table(results)
        
        # Animate
        self._animate_fade_in(self.items_table, duration=300, start_opacity=0.3)
        
        logger.info(f"Search found {len(results)} results")
        self._show_alert("Search Results", f"Found {len(results)} matching items")
    
    # ===== Import Operations =====
    
    def handle_import(self) -> None:
        """
        Handle Import button click.
        
        Opens directory picker and imports all supported files.
        """
        # Show directory picker
        directory = QFileDialog.getExistingDirectory(
            None,
            "Select Folder to Import",
            str(Path.home())
        )
        
        if not directory:
            return  # User cancelled
        
        dir_path = Path(directory)
        logger.info(f"Importing from: {dir_path}")
        
        # Import files
        imported_items = self.import_service.import_from_directory(dir_path)
        
        # Add to library
        for item in imported_items:
            self.library_service.add_item(item)
        
        # Refresh table
        self._refresh_table()
        
        logger.info(f"Import complete: {len(imported_items)} items")
        self._show_alert(
            "Import Complete",
            f"Imported {len(imported_items)} items from folder!"
        )
    
    # ===== Task Operations =====
    
    def handle_add_task(self) -> None:
        """
        Handle Add Task button click.
        
        Creates a task for the selected item.
        """
        selected_item = self._get_selected_item()
        if not selected_item:
            self._show_alert("No Selection", "Please select an item to create a task for.")
            return
        
        # Create task dialog
        dialog = QDialog()
        dialog.setWindowTitle("Add Task")
        dialog.resize(400, 250)
        
        # Add scale animation
        dialog.showEvent = lambda event: self._animate_scale(dialog, duration=200)
        
        layout = QGridLayout()
        layout.setSpacing(10)
        
        # Description field
        desc_label = QLabel("Description:")
        desc_field = QLineEdit()
        layout.addWidget(desc_label, 0, 0)
        layout.addWidget(desc_field, 0, 1)
        
        # Priority slider
        priority_label = QLabel("Priority (1-10):")
        priority_slider = QSlider(Qt.Orientation.Horizontal)
        priority_slider.setMinimum(1)
        priority_slider.setMaximum(10)
        priority_slider.setValue(5)
        priority_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        priority_slider.setTickInterval(1)
        layout.addWidget(priority_label, 1, 0)
        layout.addWidget(priority_slider, 1, 1)
        
        # Deadline picker
        deadline_label = QLabel("Deadline:")
        deadline_picker = QDateEdit()
        deadline_picker.setDate(QDate.currentDate().addDays(7))
        deadline_picker.setCalendarPopup(True)
        layout.addWidget(deadline_label, 2, 0)
        layout.addWidget(deadline_picker, 2, 1)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box, 3, 0, 1, 2)
        
        dialog.setLayout(layout)
        
        # Show dialog and create task
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Convert QDate to datetime
            q_date = deadline_picker.date()
            deadline = datetime(q_date.year(), q_date.month(), q_date.day())
            
            # Create task
            task = Task(
                item_id=selected_item.id,
                priority=priority_slider.value(),
                deadline=deadline,
                description=desc_field.text()
            )
            
            # Add to service
            self.library_service.add_task(task)
            
            # Update task count
            self._update_task_count()
            
            logger.info(f"Task created: priority={task.priority}")
            self._show_alert("Success", f"Task created with priority {task.priority}")
    
    def handle_view_next_task(self) -> None:
        """
        Handle View Next Task button click.
        
        Shows the highest priority task and removes it from queue.
        """
        next_task = self.library_service.get_next_task()
        
        if not next_task:
            self._show_alert("No Tasks", "Task queue is empty!")
            return
        
        # Find the item for this task
        item = self.library_service.find_item_by_id(next_task.item_id)
        item_title = item.title if item else "Unknown Item"
        
        # Show task details
        message = (
            f"Item: {item_title}\n"
            f"Priority: {next_task.priority}\n"
            f"Deadline: {next_task.deadline.date()}\n"
            f"Description: {next_task.description}"
        )
        
        self._show_alert("Next Task", message, title_prefix="Highest Priority Task:")
        
        # Update task count
        self._update_task_count()
        
        logger.info(f"Retrieved next task: priority={next_task.priority}")
    
    def _update_task_count(self) -> None:
        """Update task count label."""
        count = len(self.library_service.get_all_tasks())
        self.task_count_label.setText(f"Tasks: {count}")
    
    # ===== Media Preview =====
    
    def handle_preview(self) -> None:
        """
        Handle Preview button click.
        
        Opens media player for audio/video files.
        """
        selected_item = self._get_selected_item()
        if not selected_item:
            self._show_alert("No Selection", "Please select an item to preview.")
            return
        
        file_path = selected_item.file_path
        if not file_path:
            self._show_alert("No File", "This item has no associated file.")
            return
        
        path = Path(file_path)
        if not path.exists():
            self._show_alert("File Not Found", f"File does not exist:\n{file_path}")
            return
        
        item_type = selected_item.type
        
        if item_type in ["audio", "video"]:
            self._preview_media(path, item_type)
        else:
            self._show_alert(
                "Preview",
                f"Preview for type '{item_type}' not yet implemented.\n\nFile: {file_path}"
            )
    
    def _preview_media(self, file_path: Path, media_type: str) -> None:
        """
        Open media player for audio/video preview.
        
        Args:
            file_path: Path to media file
            media_type: "audio" or "video"
        """
        try:
            # Create media player
            self.media_player = QMediaPlayer()
            audio_output = QAudioOutput()
            self.media_player.setAudioOutput(audio_output)
            
            # Create preview window
            dialog = QDialog()
            dialog.setWindowTitle(f"Media Preview: {file_path.name}")
            dialog.resize(640, 480)
            
            layout = QVBoxLayout()
            
            # Add video widget if video
            if media_type == "video":
                video_widget = QVideoWidget()
                self.media_player.setVideoOutput(video_widget)
                layout.addWidget(video_widget)
            else:
                # Audio: just show label
                audio_label = QLabel(f"🎵 Playing Audio: {file_path.name}")
                audio_label.setStyleSheet("font-size: 16px;")
                audio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(audio_label)
            
            # Control buttons
            controls_layout = QHBoxLayout()
            
            play_button = QPushButton("▶ Play")
            pause_button = QPushButton("⏸ Pause")
            stop_button = QPushButton("⏹ Stop")
            
            play_button.clicked.connect(self.media_player.play)
            pause_button.clicked.connect(self.media_player.pause)
            stop_button.clicked.connect(lambda: [self.media_player.stop(), dialog.close()])
            
            controls_layout.addWidget(play_button)
            controls_layout.addWidget(pause_button)
            controls_layout.addWidget(stop_button)
            
            layout.addLayout(controls_layout)
            dialog.setLayout(layout)
            
            # Set source and play
            self.media_player.setSource(file_path.as_uri())
            self.media_player.play()
            
            # Cleanup on close
            dialog.finished.connect(lambda: self.media_player.stop())
            
            dialog.exec()
            
            logger.info(f"Media preview opened: {file_path.name}")
        
        except Exception as e:
            logger.error(f"Media preview error: {e}", exc_info=True)
            self._show_alert("Media Error", f"Error playing media file:\n{str(e)}")
    
    # ===== Data Persistence =====
    
    def load_data(self, data: LibraryData) -> None:
        """
        Load library data from repository.
        
        Args:
            data: LibraryData object from repository
        """
        # Clear current items
        self.library_service.items.clear()
        
        # Load items
        for item in data.items:
            self.library_service.add_item(item)
        
        # Rebuild search index
        self.search_service.build_index(data.items)
        
        # Refresh table
        self._refresh_table()
        
        logger.info(f"Loaded {len(data.items)} items from repository")
    
    def get_data(self) -> LibraryData:
        """
        Get library data for saving to repository.
        
        Returns:
            LibraryData object ready for serialization
        """
        data = LibraryData()
        
        # Get items
        data.items = self.library_service.get_items().copy()
        
        # Get tasks
        data.tasks = self.library_service.get_all_tasks().copy()
        
        # Get indexes
        data.keyword_index = self.search_service.get_keyword_index()
        data.tag_frequency = self.search_service.get_tag_frequency()
        
        logger.debug(f"Prepared data for saving: {len(data.items)} items")
        
        return data
    
    # ===== UI Helper Methods =====
    
    def _refresh_table(self, items: Optional[List[Item]] = None) -> None:
        """
        Refresh table with items.
        
        Args:
            items: List of items to display (default: all items from service)
        """
        if items is None:
            items = self.library_service.get_items()
        
        # Clear table
        self.items_table.setRowCount(0)
        
        # Add items
        for item in items:
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            
            # Store item object in first column for retrieval
            title_item = QTableWidgetItem(item.title)
            title_item.setData(Qt.ItemDataRole.UserRole, item)  # Store Item object
            self.items_table.setItem(row, 0, title_item)
            
            self.items_table.setItem(row, 1, QTableWidgetItem(item.category))
            self.items_table.setItem(row, 2, QTableWidgetItem(item.type))
            self.items_table.setItem(row, 3, QTableWidgetItem(str(item.rating)))
            self.items_table.setItem(row, 4, QTableWidgetItem(", ".join(item.tags)))
    
    def _get_selected_item(self) -> Optional[Item]:
        """
        Get the currently selected item from table.
        
        Returns:
            Selected Item, or None if no selection
        """
        selected_rows = self.items_table.selectedItems()
        if not selected_rows:
            return None
        
        # Get Item object from first column
        row = self.items_table.currentRow()
        title_item = self.items_table.item(row, 0)
        
        if title_item:
            return title_item.data(Qt.ItemDataRole.UserRole)
        
        return None
    
    def _show_alert(self, title: str, message: str, title_prefix: str = "") -> None:
        """
        Show alert dialog.
        
        Args:
            title: Dialog title
            message: Message text
            title_prefix: Optional prefix for title
        """
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(title_prefix + "\n" + message if title_prefix else message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()
    
    # ===== Animations =====
    
    def _animate_fade_in(
        self,
        widget,
        duration: int = 800,
        start_opacity: float = 0.0
    ) -> None:
        """
        Fade-in animation for widget.
        
        Args:
            widget: QWidget to animate
            duration: Animation duration in milliseconds
            start_opacity: Starting opacity (0.0 to 1.0)
        """
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(start_opacity)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
    
    def _animate_scale(self, widget, duration: int = 200) -> None:
        """
        Scale animation for dialogs (appears to grow from center).
        
        Args:
            widget: QWidget to animate
            duration: Animation duration in milliseconds
        """

        self._animate_fade_in(widget, duration=duration, start_opacity=0.8)
