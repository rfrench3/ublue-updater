#!/usr/bin/env python3

"""
Created in 2025 by rfrench3 (TealMango) - https://github.com/rfrench3

Licensed under the GNU GPLv3 only. See LICENSE file in the project root for full license information.
"""



import sys
import os
import subprocess

# locating other application files
sys.path.insert(0, "/app/share/ublue-updater") # flatpak path
from program_file_locator import DATA_DIR
from widget_manager import app_icon, load_widget, load_message_box

#PySide6, Qt Designer UI files
from PySide6.QtWidgets import QApplication, QPushButton, QTextBrowser, QStatusBar #Import widgets here as needed
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QFont

# Edit the .ui file using Qt Designer
ui_main = os.path.join(DATA_DIR, "main.ui")

# Worker thread for running shell scripts
class ShellWorker(QThread):
    output_ready = Signal(str)
    finished_signal = Signal()
    
    def __init__(self, script_command):
        super().__init__()
        self.script_command = script_command
    
    def run(self):
        try:
            # Run the shell script and capture output in real-time
            process = subprocess.Popen(
                self.script_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Read output line by line as it comes
            if process.stdout:
                for line in process.stdout:
                    self.output_ready.emit(line.rstrip())
            
            process.wait()
            self.finished_signal.emit()
            
        except Exception as e:
            self.output_ready.emit(f"Error running script: {str(e)}")
            self.finished_signal.emit()

# logic for the main window

class MainWindow():
    def __init__(self, window): 
        self.window = window
        self.worker = None

        self.current_task: str = ''

        # connect ui elements to code
        self.update = self.window.findChild(QPushButton,"update")
        self.change_logs = self.window.findChild(QPushButton,"change_logs")
        self.reboot = self.window.findChild(QPushButton,"reboot")
        self.exit = self.window.findChild(QPushButton,"exit")
        self.text = self.window.findChild(QTextBrowser,"text")
        self.status = self.window.findChild(QStatusBar,"statusbar")

        self.text.setFont(QFont("monospace"))

        # Connect actions to slots or functions
        self.update.clicked.connect(self.activate_update)
        self.change_logs.clicked.connect(self.open_logs) 
        self.reboot.clicked.connect(self.reboot_system)
        self.exit.clicked.connect(app.quit)
        
    def activate_update(self):
        """Updates the system."""

        self.current_task = 'update'
        
        self.text.clear()
        
        # Disable update button while running
        self.update.setEnabled(False)
        self.update.setText("Updating...")
        
        # Create and start worker thread
        self.worker = ShellWorker("flatpak update -y") #TODO: use ujust update when ready
        self.worker.output_ready.connect(self.append_output)
        self.worker.finished_signal.connect(self.script_finished)
        self.worker.start()
    
    def reboot_system(self):
        """Reboots the system so the updates can apply."""
        self.reboot.setEnabled(False)
        self.reboot.setText("Rebooting...")
        try:
            subprocess.Popen(["systemctl", "reboot"])
        except Exception as e:
            self.append_output(f"Error rebooting: {str(e)}")
            self.reboot.setEnabled(True)
            self.reboot.setText("Reboot")

    def open_logs(self):
        """Opens the change logs using ujust changelogs."""

        self.current_task = 'changelogs'

        self.text.clear()
        
        script_command = "ujust changelogs"
        
        # Create and start worker thread
        self.worker = ShellWorker(script_command)
        self.worker.output_ready.connect(self.append_output)
        self.worker.finished_signal.connect(self.script_finished)
        self.worker.start()


    # Used by QThread/Signal

    def append_output(self, line):
        """Append a line of output to the text browser"""
        self.text.append(line)
        self.status.showMessage(line)

        
    
    def script_finished(self):
        """Called when the script execution is complete."""
        self.status.showMessage("Complete!")
        if self.current_task == 'update':
            self.update.setText("Update Complete!")
            self.reboot.setEnabled(True)
        elif self.current_task == 'changelogs':
            cursor = self.text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.text.setTextCursor(cursor)
        self.current_task = ''

        

# Logic that loads the main window
app = QApplication([])

window_main = load_widget(
    ui_main,
    "System Update",
    app_icon # defaults to app_icon if not specified, this only needs to be set for custom icons
    )
logic = MainWindow(window_main)

window_main.show()
app.exec()