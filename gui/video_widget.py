"""
Video widget using PyQt5's native QMediaPlayer.
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSlider, QLabel, QSizePolicy, QStyle, QGraphicsView, QGraphicsScene
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QUrl, QRectF
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem


class VideoGraphicsView(QGraphicsView):
    """Custom graphics view that resizes its video item to fit"""
    def __init__(self, scene, video_item):
        super().__init__(scene)
        self.video_item = video_item
        self.setStyleSheet("background: black; border: none;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(640, 360)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setSceneRect(0, 0, self.width(), self.height())
        self.video_item.setSize(QRectF(0, 0, self.width(), self.height()).size())


class VideoWidget(QWidget):
    """Video player widget using QMediaPlayer."""
    
    # Signals
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    playback_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = None
        self.video_frame = None
        self.video_item = None
        self.is_playing = False
        self.is_muted = True  # Start muted
        self.duration = 0
        self.current_file = None
        self.slider_dragging = False
        
        self._setup_player()
        self._setup_ui()
    
    def _setup_player(self):
        """Initialize QMediaPlayer."""
        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.player.stateChanged.connect(self._on_state_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.error.connect(self._on_error)
        
    def _setup_ui(self):
        """Setup the user interface."""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Video display frame using QGraphicsVideoItem for overlay support
        self.video_item = QGraphicsVideoItem()
        self.scene = QGraphicsScene(self)
        self.scene.addItem(self.video_item)
        
        self.video_frame = VideoGraphicsView(self.scene, self.video_item)
        self.video_frame.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.video_frame.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.player.setVideoOutput(self.video_item)
        layout.addWidget(self.video_frame, 1)
        
        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(5, 5, 5, 5)
        
        # Play button
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_btn.clicked.connect(self.toggle_play)
        self.play_btn.setMaximumWidth(40)
        controls_layout.addWidget(self.play_btn)
        
        # Mute button
        self.mute_btn = QPushButton("🔇")
        self.mute_btn.setMaximumWidth(40)
        self.mute_btn.setToolTip("Toggle mute")
        self.mute_btn.clicked.connect(self.toggle_mute)
        controls_layout.addWidget(self.mute_btn)
        
        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.setValue(0)
        self.position_slider.sliderPressed.connect(self._on_slider_pressed)
        self.position_slider.sliderReleased.connect(self._on_slider_released)
        controls_layout.addWidget(self.position_slider)
        
        # Time label
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(100)
        controls_layout.addWidget(self.time_label)
        
        layout.addLayout(controls_layout)
        
        # Mute by default for the player as well
        self.player.setMuted(True)
    
    def load_video(self, file_path):
        """Load and play a video file."""
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            return False
        
        try:
            print(f"[DEBUG] Loading video with QMediaPlayer: {file_path}")
            self.current_file = file_path
            self.stop()
            
            # Create media and set it
            media_content = QMediaContent(QUrl.fromLocalFile(file_path))
            self.player.setMedia(media_content)
            
            # Start playback immediately
            self.player.play()
            
            print(f"[DEBUG] QMediaPlayer started playback successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load video: {e}")
            return False
    
    def toggle_play(self):
        """Toggle between play and pause."""
        if self.player.state() == QMediaPlayer.PlayingState:
            self.pause()
        else:
            self.play()
    
    def play(self):
        """Start or resume playback."""
        self.player.play()
    
    def pause(self):
        """Pause playback."""
        self.player.pause()
    
    def stop(self):
        """Stop playback."""
        self.player.stop()
        self.is_playing = False
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.position_slider.setValue(0)
        self._update_time_label(0, 0)
    
    def toggle_mute(self):
        """Toggle mute state."""
        self.is_muted = not self.player.isMuted()
        self.player.setMuted(self.is_muted)
        self.mute_btn.setText("🔇" if self.is_muted else "🔊")
    
    def set_position(self, position_ms):
        """Seek to position in milliseconds."""
        self.player.setPosition(int(position_ms))
    
    def _on_state_changed(self, state):
        """Handle player state changes."""
        if state == QMediaPlayer.PlayingState:
            self.is_playing = True
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        elif state == QMediaPlayer.PausedState or state == QMediaPlayer.StoppedState:
            self.is_playing = False
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            if state == QMediaPlayer.StoppedState and self.player.position() == self.player.duration():
                # Reached end
                self.playback_finished.emit()
    
    def _on_position_changed(self, current_time):
        """Update UI with current playback position."""
        if self.slider_dragging:
            return
            
        if self.duration > 0:
            position_ratio = current_time / self.duration
            self.position_slider.blockSignals(True)
            self.position_slider.setValue(int(position_ratio * 1000))
            self.position_slider.blockSignals(False)
            
            self._update_time_label(current_time, self.duration)
            self.position_changed.emit(current_time)
            
    def _on_duration_changed(self, duration):
        """Handle duration changes (e.g., when media is loaded)."""
        self.duration = duration
        self.duration_changed.emit(duration)
        self._update_time_label(self.player.position(), duration)
    
    def _update_time_label(self, current_ms, total_ms):
        """Update the time display label."""
        current_str = self._format_time(current_ms)
        total_str = self._format_time(total_ms)
        self.time_label.setText(f"{current_str} / {total_str}")
    
    def _format_time(self, ms):
        """Format milliseconds to MM:SS."""
        if ms < 0:
            ms = 0
        seconds = int(ms / 1000)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def _on_slider_pressed(self):
        self.slider_dragging = True
    
    def _on_slider_released(self):
        self.slider_dragging = False
        if self.duration > 0:
            ratio = self.position_slider.value() / 1000.0
            target_time = int(ratio * self.duration)
            self.player.setPosition(target_time)
    
    def _on_error(self):
        """Handle QMediaPlayer errors."""
        err = self.player.errorString()
        print(f"[ERROR] QMediaPlayer occurred: {err}")
        self.error_occurred.emit(err)
        
    def cleanup(self):
        """Clean up QMediaPlayer resources."""
        if self.player:
            self.player.stop()
