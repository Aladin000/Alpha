"""
alpha.py

Main entry point for the Alpha Personal Finance Management application.
Initializes and launches the PySide6 GUI application.
"""

import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.mainwindow import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('alpha.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """
    Main application entry point.
    Initializes the PySide6 application and shows the main window.
    """
    try:
        # Create QApplication instance
        app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName("Alpha")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Alpha Finance")
        
        # Set high DPI support
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        
        logger.info("Starting Alpha Personal Finance Manager")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        logger.info("Main window displayed successfully")
        
        # Start the application event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"Error starting Alpha application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 