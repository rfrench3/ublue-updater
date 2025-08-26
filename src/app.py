#!/usr/bin/env python3

"""
Created in 2025 by rfrench3 (TealMango) - https://github.com/rfrench3

Licensed under the GNU GPLv3 only. See LICENSE file in the project root for full license information.

#TODO:
- package into an RPM so it can be layered/integrated
- set a better icon
- get colors working like they do in the terminal

IN KDE NEON DISTROBOX WITH PYSIDE6 INSTALLED: python3 -m src.ublue_updater.app

"""


import subprocess
import importlib.resources
import sys
import os
import signal

#PySide6, QML
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtQuick import QQuickView
from PySide6.QtCore import QThread, Signal, QTimer, QObject, Property, Slot
import time
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine


braille_spinner: list[str] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
spinner_index: int = 0

def get_spinner_element() -> str:
    """Get the current spinner element and advance to next"""
    global spinner_index
    element = braille_spinner[spinner_index]
    spinner_index = (spinner_index + 1) % len(braille_spinner)
    return element


def load_message_box(parent_window,title:str,  text:str,  icon:QMessageBox.Icon=QMessageBox.Icon.Information,  standard_buttons:QMessageBox.StandardButton=QMessageBox.StandardButton.Ok) -> QMessageBox.StandardButton:
    """Loads a QMessageBox, returns the result of exec()."""
    msg = QMessageBox(parent_window)
    msg.setIcon(icon)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(standard_buttons)
    return msg.exec() #type:ignore

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

class SystemUpdater(QObject):
    """Backend class that will be exposed to QML"""
    
    # Signals to communicate with QML
    outputChanged = Signal(str)
    taskFinished = Signal()
    statusChanged = Signal(str)
    isRunningChanged = Signal(bool)
    updateCompletedChanged = Signal(bool)
    showPopupMessage = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.current_task: str = ''
        self.last_status_message: str = ''
        self._output_text: str = ''
        self._is_running: bool = False
        self._update_completed: bool = False
        
        # Setup status bar spinner timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_spinner)
        self.status_timer.setInterval(250)  # 0.25 seconds
        
        # Reboot needs to be clicked twice before rebooting
        self._reboots_clicked = False
    
    def _get_output_text(self):
        return self._output_text
    
    def _set_output_text(self, text):
        if self._output_text != text:
            self._output_text = text
            self.outputChanged.emit(text)
    
    outputText = Property(str, _get_output_text, _set_output_text, notify=outputChanged)
    
    def _get_is_running(self):
        return self._is_running
    
    def _set_is_running(self, running):
        if self._is_running != running:
            self._is_running = running
            self.isRunningChanged.emit(running)
    
    isRunning = Property(bool, _get_is_running, _set_is_running, notify=isRunningChanged)
    
    def _get_update_completed(self):
        return self._update_completed
    
    def _set_update_completed(self, completed):
        if self._update_completed != completed:
            self._update_completed = completed
            self.updateCompletedChanged.emit(completed)
    
    updateCompleted = Property(bool, _get_update_completed, _set_update_completed, notify=updateCompletedChanged)
        
    def update_status_spinner(self):
        """Update the status with spinner when a task is running"""
        if self.current_task:
            status_msg = f'{get_spinner_element()} {self.last_status_message}'
            self.statusChanged.emit(status_msg)
    
    @Slot()
    def activate_update(self):
        """Updates the system."""
        self.current_task = 'update'
        self.last_status_message = 'Starting update...'
        self._set_is_running(True)
        
        self._set_output_text('')
        
        # Start the status spinner timer
        self.status_timer.start()
        
        # Create and start worker thread
        self.worker = ShellWorker("ujust update")
        self.worker.output_ready.connect(self.append_output)
        self.worker.finished_signal.connect(self.script_finished)
        self.worker.start()
    
    @Slot()
    def reboot_system(self):
        """Reboots the system on second click so the updates can apply."""
        if not self._reboots_clicked:
            self._reboots_clicked = True
            self.append_output("Click reboot again to confirm...")
            return

        self.append_output("Rebooting system...")
        time.sleep(1)
        try:
            subprocess.Popen(["systemctl", "reboot"])
        except Exception as e:
            self.append_output(f"Error rebooting: {str(e)}")

    @Slot()
    def open_logs(self):
        """Opens the change logs using ujust changelogs."""
        self.current_task = 'changelogs'
        self.last_status_message = 'Loading changelogs...'
        self._set_is_running(True)

        self._set_output_text('')
        
        # Start the status spinner timer
        self.status_timer.start()
        
        script_command = "ujust changelogs"
        
        # Create and start worker thread
        self.worker = ShellWorker(script_command)
        self.worker.output_ready.connect(self.append_output)
        self.worker.finished_signal.connect(self.script_finished)
        self.worker.start()

    @Slot()
    def exit_app(self):
        """Exit the application."""
        # Don't allow exit while tasks are running
        if self._is_running:
            self.showPopupMessage.emit("Cannot close while a task is running. Please wait for completion.")
            return
        QApplication.quit()
    
    @Slot(result=bool)
    def can_close_app(self):
        """Check if the app can be closed (no tasks running)."""
        if self._is_running:
            self.showPopupMessage.emit("Cannot close while a task is running. Please wait for completion.")
            return False
        return True

    def append_output(self, line):
        """Append a line of output to the text"""
        current_text = self._get_output_text()
        new_text = current_text + line + "\n"
        self._set_output_text(new_text)
        
        # Store the message for the spinner timer to use
        self.last_status_message = line
    
    def script_finished(self):
        """Called when the script execution is complete."""
        # Stop the spinner timer
        self.status_timer.stop()
        
        self.statusChanged.emit("Complete!")
        if self.current_task == 'update':
            self.append_output("Update Complete!")
            self._set_update_completed(True)
        
        self.current_task = ''
        self._set_is_running(False)
        self.taskFinished.emit()

def main():
    # Logic that loads the main window
    app = QApplication(sys.argv)

    # Create QML engine and load QML file
    engine = QQmlApplicationEngine()
    
    if not os.environ.get("QT_QUICK_CONTROLS_STYLE"):
        os.environ["QT_QUICK_CONTROLS_STYLE"] = "org.kde.desktop"


    # Create and register the backend instance
    backend = SystemUpdater()
    engine.rootContext().setContextProperty("backend", backend)
    
    #script_dir = os.path.dirname(os.path.abspath(__file__))
    qml_path = importlib.resources.files(__package__).joinpath("qml", "Main.qml")
    engine.load(QUrl.fromLocalFile(str(qml_path)))

    if not engine.rootObjects():
        return -1
    
    sys.exit(app.exec())




if __name__ == "__main__":
    main()