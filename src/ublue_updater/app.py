#!/usr/bin/env python3

"""
Created in 2025 by rfrench3 (TealMango) - https://github.com/rfrench3

Licensed under the GNU GPLv3 only. See LICENSE file in the project root for full license information.

#TODO:
- package into an RPM so it can be layered/integrated
- set a better icon
- get colors working like they do in the terminal

~/Code_Projects/ublue-updater/.venv/bin/ublue-updater

"""


import subprocess
import importlib.resources

from .widget_manager import app_icon, load_widget

#PySide6, Qt Designer UI files
from PySide6.QtWidgets import QApplication, QPushButton, QTextBrowser, QStatusBar, QMainWindow, QMessageBox
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtGui import QFont
import time


braille_spinner: list[str] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
spinner_index: int = 0

def get_spinner_element() -> str:
    """Get the current spinner element and advance to next"""
    global spinner_index
    element = braille_spinner[spinner_index]
    spinner_index = (spinner_index + 1) % len(braille_spinner)
    return element

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
                stdin=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Read output line by line as it comes
            if process.stdout:
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    
                    line = line.rstrip()
                    self.output_ready.emit(line)
                    
                    # Auto-respond to quit prompt
                    if "(Q)uit" in line:
                        #TODO: make the process end gracefully, this currently causes no issues though
                        process.terminate()
                        break
            
            process.wait()
            self.finished_signal.emit()
            
        except Exception as e:
            self.output_ready.emit(f"Error running script: {str(e)}")
            self.finished_signal.emit()

# Main window class that handles close events
class UpdaterMainWindow(QMainWindow):
    def __init__(self, ui_main, app):
        super().__init__()
        self.logic = None  # type: MainWindow | None
        self.app = app
        
        # Load the UI from the .ui file
        self.ui_widget = load_widget(ui_main)
        self.setCentralWidget(self.ui_widget)
        self.setWindowTitle("System Update")
        self.setWindowIcon(app_icon)
        
        # Adapt the window size based on the screen
        screen = self.app.primaryScreen().availableGeometry()
        
        width = max(800, min(1200, int(screen.width() * 0.5)))
        height = max(600, min(800, int(screen.height() * 0.8)))
        
        self.resize(width, height)
        
        # Center the window on screen
        self.move(
            (screen.width() - width) // 2,
            (screen.height() - height) // 2
        )
        
    def closeEvent(self, event):
        """Handle window close event - prevent closing during updates"""
        if self.logic and (self.logic.current_task == 'update'):
            # Prevent closing during active tasks
            QMessageBox.warning(
                self,
                "Update in Progress",
                f"Cannot close the window while system update is running.\n\n"
                "Please wait for the operation to complete before closing.",
                QMessageBox.StandardButton.Ok
            )
            event.ignore()
            return
        
        # Allow the window to close when no task is running
        event.accept()

# logic for the main window
class MainWindow():
    def __init__(self, window, app): 
        self.window = window
        self.worker = None
        self.app = app

        self.current_task: str = ''
        self.last_status_message: str = ''

        # connect ui elements to code
        self.update = self.window.findChild(QPushButton,"update")
        self.change_logs = self.window.findChild(QPushButton,"change_logs")
        self.reboot = self.window.findChild(QPushButton,"reboot")
        self.exit = self.window.findChild(QPushButton,"exit")
        self.text = self.window.findChild(QTextBrowser,"text")
        self.status = self.window.findChild(QStatusBar,"statusbar")

        self.text.setFont(QFont("monospace"))

        # Setup status bar spinner timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_spinner)
        self.status_timer.setInterval(250)  # 0.25 seconds

        # Connect actions to slots or functions
        self.update.clicked.connect(self.activate_update)
        self.change_logs.clicked.connect(self.open_logs) 
        self.reboot.clicked.connect(self.reboot_system)
        self.exit.clicked.connect(self.app.quit)

        # Reboot needs to be clicked twice before rebooting
        self._reboots_clicked = False
        
    def update_status_spinner(self):
        """Update the status bar with spinner when a task is running"""
        if self.current_task:
            self.status.showMessage(f'{get_spinner_element()} {self.last_status_message}')
        
    def activate_update(self):
        """Updates the system."""

        self.current_task = 'update'
        self.last_status_message = 'Starting update...'
        
        self.text.clear()
        
        # Start the status spinner timer
        self.status_timer.start()
        
        # Disable update button while running
        self.update.setEnabled(False)
        self.change_logs.setEnabled(False)
        self.exit.setEnabled(False)

        self.update.setText("Updating...")
        
        # Create and start worker thread
        self.worker = ShellWorker("ujust update") #TODO: use ujust update when ready
        self.worker.output_ready.connect(self.append_output)
        self.worker.finished_signal.connect(self.script_finished)
        self.worker.start()
    
    def reboot_system(self):
        """Reboots the system on second click so the updates can apply."""

        if not self._reboots_clicked:
            self._reboots_clicked = True
            self.reboot.setText("Click again to confirm")
            return


        self.reboot.setEnabled(False)
        self.reboot.setText("Rebooting...")
        time.sleep(1)
        try:
            subprocess.Popen(["systemctl", "reboot"])
        except Exception as e:
            self.append_output(f"Error rebooting: {str(e)}")
            self.reboot.setEnabled(True)
            self.reboot.setText("Reboot")

    def open_logs(self):
        """Opens the change logs using ujust changelogs."""

        self.current_task = 'changelogs'
        self.last_status_message = 'Loading changelogs...'

        self.text.clear()
        
        # Start the status spinner timer
        self.status_timer.start()
        
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
        # Store the message for the spinner timer to use
        self.last_status_message = line

        
    
    def script_finished(self):
        """Called when the script execution is complete."""
        # Stop the spinner timer
        self.status_timer.stop()
        
        self.status.showMessage("Complete!")
        if self.current_task == 'update':
            self.update.setText("Update Complete!")
            self.reboot.setEnabled(True)
            self.change_logs.setEnabled(True)
            self.exit.setEnabled(True)
        elif self.current_task == 'changelogs':
            cursor = self.text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.text.setTextCursor(cursor)
        self.current_task = ''

        

def main():
    # Logic that loads the main window
    app = QApplication([])

    with importlib.resources.path("ublue_updater", "main.ui") as ui_main_path:
        # ui_main_path is now the correct path to main.ui in your installed package
        window_main = UpdaterMainWindow(str(ui_main_path), app)

    logic = MainWindow(window_main.ui_widget, app)
    window_main.logic = logic  # Give the window access to the logic

    window_main.show()
    app.exec()


if __name__ == "__main__":
    main()