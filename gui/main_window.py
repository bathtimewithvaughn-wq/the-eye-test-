"""
Main application window
"""

import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QMessageBox, QStackedWidget, QApplication, QProgressBar,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap

from gui.video_widget import VideoWidget
from gui.black_bar_editor import BlackBarEditor
from gui.controls import ControlsPanel
from processor.downloader import VideoDownloader
import json
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """Get correct path for resources, works for bundled and development"""
    if getattr(sys, 'frozen', False):
        # Bundled - use exe directory
        base_path = Path(sys.executable).parent
    else:
        # Development - use module directory
        base_path = Path(__file__).parent.parent
    return base_path / relative_path


class DownloadThread(QThread):
    """Background thread for video downloads"""
    
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, downloader, url, quality):
        super().__init__()
        self.downloader = downloader
        self.url = url
        self.quality = quality
    
    def run(self):
        try:
            path = self.downloader.download(self.url, self.quality)
            if path:
                self.finished.emit(path)
            else:
                self.error.emit("Download failed after 3 attempts. Try updating yt-dlp: pip install -U yt-dlp")
        except Exception as e:
            self.error.emit(str(e))


class ProcessThread(QThread):
    """Background thread for video processing"""
    
    progress = pyqtSignal(int)  # percentage
    finished = pyqtSignal(str)  # output path
    error = pyqtSignal(str)
    
    def __init__(self, processor):
        super().__init__()
        self.processor = processor
    
    def run(self):
        try:
            output_path = self.processor.run(self._on_progress)
            if output_path:
                self.finished.emit(output_path)
            else:
                self.error.emit("Processing failed")
        except Exception as e:
            self.error.emit(str(e))
    
    def _on_progress(self, percent):
        self.progress.emit(percent)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Eye Test")
        self.setMinimumSize(1200, 700)
        
        # Apply dark theme to entire app
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            QWidget {
                background-color: #1a1a2e;
                color: #ffffff;
            }
            QProgressBar {
                background-color: #0f0f23;
                border: none;
                border-radius: 8px;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #6366f1;
                border-radius: 8px;
            }
            QMessageBox {
                background-color: #1a1a2e;
                color: #ffffff;
            }
            QMessageBox QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #5558e8;
            }
        """)
        
        self.preview_path = None
        self.output_path = None
        self.downloader = VideoDownloader("temp")
        self.download_thread = None
        self.process_thread = None
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Left side: Video preview (stacked widget)
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Logo placeholder
        self.logo_label = QLabel()
        logo_path = get_resource_path("assets/logo.jpg")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            self.logo_label.setPixmap(pixmap.scaled(640, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("background-color: #1a1a1a;")
        self.logo_label.setMinimumSize(320, 180)
        self.logo_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.logo_label.setScaledContents(False)
        
        # Video widget
        self.video_widget = VideoWidget()
        
        # Black bar editor - created when video loads
        self.bar_editor = None
        
        self.stack.addWidget(self.logo_label)
        self.stack.addWidget(self.video_widget)
        
        # Give stack stretch factor 3 (video takes 75%)
        layout.addWidget(self.stack, stretch=3)
        
        # Right side: Controls with status and progress
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        
        # Status label at top
        self.status_label = QLabel("Ready. Enter a YouTube URL.")
        self.status_label.setStyleSheet("color: #fff; padding: 8px; font-size: 13px; background-color: #333; border-radius: 5px;")
        self.status_label.setWordWrap(True)
        right_layout.addWidget(self.status_label)
        
        # Controls
        self.controls = ControlsPanel()
        self.controls.download_requested.connect(self._on_download_requested)
        self.controls.bars_cleared.connect(self._on_clear_bars)
        self.controls.undo_bar.connect(self._on_undo_bar)
        self.controls.process_requested.connect(self._on_process)
        self.controls.setMinimumWidth(350)
        self.controls.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(self.controls)
        
        # Progress bar at bottom
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        right_layout.addWidget(self.progress_bar)
        
        layout.addWidget(right_panel, stretch=1)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update bar editor position to track graphics view
        if self.bar_editor:
            self.bar_editor.update_geometry()
        
        # Scale logo pixmap to fit available space
        if hasattr(self, 'logo_label') and self.logo_label.pixmap():
            logo_path = get_resource_path("assets/logo.jpg")
            if logo_path.exists():
                pixmap = QPixmap(str(logo_path))
                scaled = pixmap.scaled(
                    self.logo_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.logo_label.setPixmap(scaled)
    
    def showEvent(self, event):
        super().showEvent(event)
        if self.bar_editor:
            self.bar_editor.setGeometry(self.video_widget.video_frame.rect())
    
    def _on_bar_created(self, bar):
        # No longer used - bar count updated directly
        pass
    
    def _on_clear_bars(self):
        if self.bar_editor:
            self.bar_editor.clear_bars()
            self.controls.set_bar_count(0)
    
    def _on_undo_bar(self):
        if self.bar_editor:
            self.bar_editor.undo_last()
            self.controls.set_bar_count(len(self.bar_editor.bars))
    
    def _update_bar_count(self):
        """Update bar count display"""
        if self.bar_editor:
            self.controls.set_bar_count(len(self.bar_editor.bars))
    
    def _on_download_requested(self, url, quality):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setFormat("Downloading...")
        self.controls.set_processing_state(False, False)
        self.status_label.setText("Downloading preview video...")
        
        self.download_thread = DownloadThread(self.downloader, url, quality)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.error.connect(self._on_download_error)
        self.download_thread.start()
    
    def _on_download_finished(self, path):
        self.progress_bar.setVisible(False)
        self.preview_path = path
        
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Error", f"Download failed - no file found.")
            self.status_label.setText("Download failed.")
            return
        
        # Switch to video page and process events so it's visible BEFORE loading video
        self.stack.setCurrentIndex(1)
        QApplication.processEvents()
        
        if self.video_widget.load_video(path):
            self.controls.set_processing_state(False, True)
            self.status_label.setText("Draw black bars on video. Trim only applies during processing.")
            
            # Create bar editor overlay
            QApplication.processEvents()
            
            # Delete old bar editor if exists
            if self.bar_editor:
                self.bar_editor.deleteLater()
            
            # Create new bar editor overlaying the video frame directly
            self.bar_editor = BlackBarEditor(self.video_widget.video_frame)
            self.bar_editor.on_bar_added = lambda count: self.controls.set_bar_count(count)
            
            # Restore saved bars if any
            if hasattr(self, '_saved_bars') and self._saved_bars:
                self.bar_editor.set_bars(self._saved_bars)
                self.controls.set_bar_count(len(self._saved_bars))
            
            self.bar_editor.update_geometry()
        else:
            QMessageBox.warning(self, "Error", "Failed to load video. The file may be corrupted.")
            self.status_label.setText("Failed to load video.")
    
    def _on_download_error(self, error):
        self.progress_bar.setVisible(False)
        self.controls.set_processing_state(False, False)
        self.status_label.setText("Download failed.")
        QMessageBox.warning(self, "Download Error", error)
    
    def _on_process(self):
        """Start video processing"""
        if not self.preview_path:
            QMessageBox.warning(self, "Error", "No video loaded. Load a preview first.")
            return
        
        # Get settings
        bars = self.bar_editor.get_bars() if self.bar_editor else []
        trim_seconds = self.controls.get_trim_seconds()
        filter_name = self.controls.get_filter()
        output_folder = self.controls.get_output_folder()
        mirror = True  # Always mirror output
        
        print(f"[DEBUG] Processing with filter: {filter_name}, mirror: {mirror}, bars: {len(bars)}")
        
        # Create processor
        from processor.encoder import VideoProcessor
        self.video_processor = VideoProcessor(
            input_path=self.preview_path,
            output_folder=output_folder,
            bars=bars,
            trim_seconds=trim_seconds,
            filter_name=filter_name,
            original_url=self.controls.get_url(),
            mirror=mirror
        )
        
        # Start processing in background
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Processing: %p%")
        self.controls.set_processing_state(True, True)
        self.status_label.setText("Processing video...")
        self.video_widget.pause()
        
        self.process_thread = ProcessThread(self.video_processor)
        self.process_thread.progress.connect(self._on_process_progress)
        self.process_thread.finished.connect(self._on_process_finished)
        self.process_thread.error.connect(self._on_process_error)
        self.process_thread.start()
    
    def _on_process_progress(self, percent):
        self.progress_bar.setValue(percent)
    
    def _on_process_finished(self, output_path):
        self.progress_bar.setVisible(False)
        self.output_path = output_path
        self.controls.set_processing_state(False, True)
        self.status_label.setText(f"Done! Output: {output_path}")
        
        # Show success with option to open folder
        reply = QMessageBox.question(
            self, "Processing Complete",
            f"Video saved to:\n{output_path}\n\nOpen output folder?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            import subprocess
            subprocess.run(['explorer', '/select,', output_path])
    
    def _on_process_error(self, error):
        self.progress_bar.setVisible(False)
        self.controls.set_processing_state(False, True)
        self.status_label.setText("Processing failed.")
        QMessageBox.warning(self, "Processing Error", error)
    
    def _load_settings(self):
        try:
            with open("config/settings.json", "r") as f:
                settings = json.load(f)
            if settings.get("last_url"):
                self.controls.url_input.setText(settings["last_url"])
            if settings.get("last_trim_seconds"):
                self.controls.trim_spin.setValue(settings["last_trim_seconds"])
            if settings.get("last_filter"):
                idx = self.controls.filter_combo.findText(settings["last_filter"])
                if idx >= 0:
                    self.controls.filter_combo.setCurrentIndex(idx)
            if settings.get("output_folder"):
                self.controls.output_path.setText(settings["output_folder"])
            # Bars will be restored when video loads
            self._saved_bars = settings.get("black_bars", [])
        except:
            self._saved_bars = []
    
    def closeEvent(self, event):
        # Save settings
        bars = self.bar_editor.get_bars() if self.bar_editor else []
        settings = {
            "last_url": self.controls.get_url(),
            "last_trim_seconds": self.controls.get_trim_seconds(),
            "last_filter": self.controls.get_filter(),
            "output_folder": self.controls.get_output_folder(),
            "black_bars": bars
        }
        try:
            with open("config/settings.json", "w") as f:
                json.dump(settings, f, indent=2)
        except:
            pass
        
        # Clean up temp files
        try:
            self.downloader.cleanup_preview()
        except:
            pass
        
        event.accept()
