#!/usr/bin/env python3

"""
Created in 2025 by rfrench3 (TealMango) - https://github.com/rfrench3

Licensed under the GNU GPLv3 only. See LICENSE file in the project root for full license information.
"""



import sys
import os

# locating other application files
sys.path.insert(0, "/app/share/ublue-updater") # flatpak path
from program_file_locator import DATA_DIR
from widget_manager import app_icon, load_widget, load_message_box

#PySide6, Qt Designer UI files
from PySide6.QtWidgets import QApplication, QPushButton #Import widgets here as needed

# Edit the .ui file using Qt Designer
ui_main = os.path.join(DATA_DIR, "main.ui")

# logic for the main window

class MainWindow():
    def __init__(self, window): 
        self.window = window

        # connect ui elements to code
        self.update = self.window.findChild(QPushButton,"update")

        # Connect actions to slots or functions
        self.update.clicked.connect(self.activate_update)
        
    def activate_update(self):
        load_message_box(
            self.window,
            "message box title!",
            "message box text!"
        )

# Logic that loads the main window
app = QApplication([])

window_main = load_widget(
    ui_main,
    "Application Main Window",
    app_icon # defaults to app_icon if not specified, this only needs to be set for custom icons
    )
logic = MainWindow(window_main)

window_main.show()
app.exec()