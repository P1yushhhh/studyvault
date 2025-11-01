"""
Main Window View - UI definition for StudyVault application.

Creates the main window layout with all widgets (table, buttons, search field).
Programmatic equivalent of main-view.fxml from JavaFX.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QLineEdit, QPushButton, QLabel, QTableWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from studyvault.controllers.main_controller import MainController
from studyvault.utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Creates UI layout matching the JavaFX FXML structure:
    - Top: Search bar + Import button
    - Center: Items table
    - Bottom: Action buttons (Add/Edit/Delete/Undo/Preview) + Task section
    
    Example:
        >>> window = MainWindow()
        >>> window.show()
    """
    
    def __init__(self):
        """Initialize main window and create UI."""
        super().__init__()
        
        self.setWindowTitle("StudyVault - Library Manager")
        self.resize(900, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout (vertical)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create sections
        self._create_top_section(main_layout)
        self._create_center_section(main_layout)
        self._create_bottom_section(main_layout)
        
        # Initialize controller (connects widgets to logic)
        self._init_controller()
        
        logger.info("MainWindow created")
    
    def _create_top_section(self, parent_layout: QVBoxLayout) -> None:
        """
        Create top section: Search bar + Import button.
        
        FXML equivalent:
        <top>
            <HBox spacing="10">
                <TextField fx:id="searchField" promptText="🔍 Search library..."/>
                <Button text="Search" onAction="#handleSearch"/>
                <Button text="Import Folder" onAction="#handleImport"/>
            </HBox>
        </top>
        """
        # Search bar container
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        search_layout.setContentsMargins(10, 10, 10, 10)
        
        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("🔍 Search library...")
        self.search_field.setMinimumWidth(300)
        search_layout.addWidget(self.search_field, stretch=1)
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.setMinimumWidth(80)
        search_layout.addWidget(self.search_button)
        
        # Import button
        self.import_button = QPushButton("Import Folder")
        self.import_button.setMinimumWidth(120)
        search_layout.addWidget(self.import_button)
        
        parent_layout.addLayout(search_layout)
    
    def _create_center_section(self, parent_layout: QVBoxLayout) -> None:
        """
        Create center section: Items table.
        
        FXML equivalent:
        <center>
            <TableView fx:id="itemsTable">
                <columns>
                    <TableColumn text="Title" prefWidth="200"/>
                    <TableColumn text="Category" prefWidth="100"/>
                    <TableColumn text="Type" prefWidth="80"/>
                    <TableColumn text="Rating" prefWidth="80"/>
                    <TableColumn text="Created" prefWidth="150"/>
                </columns>
            </TableView>
        </center>
        """
        # Items table
        self.items_table = QTableWidget()
        self.items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.items_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.items_table.setAlternatingRowColors(True)
        
        # Table will be configured by controller (columns, headers)
        
        parent_layout.addWidget(self.items_table, stretch=1)
    
    def _create_bottom_section(self, parent_layout: QVBoxLayout) -> None:
        """
        Create bottom section: Action buttons + Task section.
        
        FXML equivalent:
        <bottom>
            <VBox spacing="5">
                <HBox spacing="10"> <!-- Item Actions -->
                    <Button text="Add Item" onAction="#handleAdd"/>
                    <Button text="Edit Item" onAction="#handleEdit"/>
                    ...
                </HBox>
                <HBox spacing="10"> <!-- Task Actions -->
                    <Label text="📋 Tasks:"/>
                    <Button text="Add Task" onAction="#handleAddTask"/>
                    ...
                </HBox>
            </VBox>
        </bottom>
        """
        # Bottom container
        bottom_container = QVBoxLayout()
        bottom_container.setSpacing(5)
        bottom_container.setContentsMargins(10, 5, 10, 10)
        
        # Item actions row
        item_actions = QHBoxLayout()
        item_actions.setSpacing(10)
        
        self.add_button = QPushButton("Add Item")
        self.edit_button = QPushButton("Edit Item")
        self.delete_button = QPushButton("Delete Item")
        self.preview_button = QPushButton("Preview")
        self.undo_button = QPushButton("Undo")
        
        # Set minimum widths for consistent button sizes
        for button in [self.add_button, self.edit_button, self.delete_button, 
                      self.preview_button, self.undo_button]:
            button.setMinimumWidth(100)
        
        item_actions.addWidget(self.add_button)
        item_actions.addWidget(self.edit_button)
        item_actions.addWidget(self.delete_button)
        item_actions.addWidget(self.preview_button)
        item_actions.addWidget(self.undo_button)
        item_actions.addStretch()  # Push buttons to left
        
        bottom_container.addLayout(item_actions)
        
        # Task actions row
        task_actions = QHBoxLayout()
        task_actions.setSpacing(10)
        
        task_label = QLabel("📋 Tasks:")
        task_label_font = QFont()
        task_label_font.setBold(True)
        task_label.setFont(task_label_font)
        
        self.add_task_button = QPushButton("Add Task")
        self.view_task_button = QPushButton("View Next Task")
        self.task_count_label = QLabel("(0 tasks)")
        self.task_count_label.setStyleSheet("color: #666;")
        
        self.add_task_button.setMinimumWidth(100)
        self.view_task_button.setMinimumWidth(130)
        
        task_actions.addWidget(task_label)
        task_actions.addWidget(self.add_task_button)
        task_actions.addWidget(self.view_task_button)
        task_actions.addWidget(self.task_count_label)
        task_actions.addStretch()
        
        bottom_container.addLayout(task_actions)
        
        parent_layout.addLayout(bottom_container)
    
    def _init_controller(self) -> None:
        """
        Initialize main controller with all widgets.
        
        Connects UI widgets to business logic via MainController.
        """
        self.controller = MainController(
            items_table=self.items_table,
            search_field=self.search_field,
            task_count_label=self.task_count_label,
            add_button=self.add_button,
            edit_button=self.edit_button,
            delete_button=self.delete_button,
            undo_button=self.undo_button,
            search_button=self.search_button,
            import_button=self.import_button,
            add_task_button=self.add_task_button,
            view_task_button=self.view_task_button,
            preview_button=self.preview_button
        )
        
        # Initialize controller (sets up table, connects signals)
        self.controller.initialize()
        
        logger.debug("MainController initialized with widgets")
    
    def apply_stylesheet(self, stylesheet_path: str = None) -> None:
        """
        Apply QSS stylesheet to the window.
        
        Args:
            stylesheet_path: Path to .qss file (optional)
        """
        if stylesheet_path:
            try:
                with open(stylesheet_path, 'r') as f:
                    self.setStyleSheet(f.read())
                logger.info(f"Stylesheet loaded: {stylesheet_path}")
            except Exception as e:
                logger.warning(f"Could not load stylesheet: {e}")
