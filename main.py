# main.py
import sys
import os
import traceback
from PyQt6 import QtWidgets
from utils.logging_config import logger

sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))



def main():
    try:
        logger.info("Starting application...")

        from ui.mainwindow import MainApp

        app = QtWidgets.QApplication(sys.argv)
        logger.info("QApplication created")

        window = MainApp()
        logger.info("Main window created")

        window.show()
        logger.info("Main window shown")

        logger.info("Entering application event loop")
        exit_code = app.exec()
        logger.info(f"Application exited with code: {exit_code}")

        return exit_code

    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())