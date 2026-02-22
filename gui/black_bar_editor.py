"""
Black bar editor as separate window tracking video position
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen


class BlackBarEditor(QWidget):
    """Overlay window for drawing black bars on video"""
    
    def __init__(self, video_frame):
        super().__init__(video_frame)
        self.video_frame = video_frame
        
        self.setStyleSheet("background: transparent;")
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        
        self.setGeometry(video_frame.rect())
        self.show()
        self.raise_()
        
        self.bars = []  # List of QRect
        self.current_bar = None
        self.start_pos = None
        self.on_bar_added = None  # Callback when bar is added
        
        # Track video widget position
        self.update_geometry()
    
    def update_geometry(self):
        """Position overlay over video widget"""
        if self.video_frame:
            self.setGeometry(self.video_frame.rect())
            self.raise_()
            self.show()
    
    def paintEvent(self, event):
        # Only paint if there are bars or currently drawing
        if not self.bars and not self.current_bar:
            return  # Don't paint anything - keep completely transparent
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw existing bars
        for bar in self.bars:
            painter.fillRect(bar, QColor(0, 0, 0, 220))
            painter.setPen(QPen(QColor(255, 255, 0), 2))
            painter.drawRect(bar)
        
        # Draw current dragging bar
        if self.current_bar:
            painter.fillRect(self.current_bar, QColor(0, 255, 0, 100))  # Green semi-transparent while drawing
            painter.setPen(QPen(QColor(255, 255, 0), 2, Qt.DashLine))
            painter.drawRect(self.current_bar)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and len(self.bars) < 5:  # Max 5 bars
            self.start_pos = event.pos()
            self.current_bar = QRect(self.start_pos, self.start_pos)
        elif event.button() == Qt.RightButton and self.bars:
            # Delete last bar on right-click
            self.bars.pop()
            self.update()
            if self.on_bar_added:
                self.on_bar_added(len(self.bars))
    
    def mouseMoveEvent(self, event):
        if self.start_pos:
            self.current_bar = QRect(self.start_pos, event.pos()).normalized()
            self.repaint()  # Force immediate repaint
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.current_bar:
            if self.current_bar.width() > 5 and self.current_bar.height() > 5:
                self.bars.append(self.current_bar)
                # Emit bar count changed
                if hasattr(self, 'on_bar_added') and self.on_bar_added:
                    self.on_bar_added(len(self.bars))
            self.current_bar = None
            self.start_pos = None
            self.repaint()  # Force immediate repaint
    
    def clear_bars(self):
        self.bars.clear()
        self.update()
    
    def _get_video_rect(self):
        """Get the actual pixel rect where the video is rendering inside the view"""
        if not hasattr(self, 'video_frame') or not hasattr(self.video_frame, 'video_item'):
            return self.rect()
            
        view = self.video_frame
        item = view.video_item
        rect = item.boundingRect()
        
        # QGraphicsVideoItem maintains aspect ratio
        video_ratio = 16 / 9  # Standard HD ratio
        view_ratio = view.width() / view.height() if view.height() > 0 else video_ratio
        
        if view_ratio > video_ratio:
            # View is wider than video (pillarboxing)
            actual_height = view.height()
            actual_width = actual_height * video_ratio
            x_offset = (view.width() - actual_width) / 2
            y_offset = 0
        else:
            # View is taller than video (letterboxing)
            actual_width = view.width()
            actual_height = actual_width / video_ratio
            x_offset = 0
            y_offset = (view.height() - actual_height) / 2
            
        return QRect(int(x_offset), int(y_offset), int(actual_width), int(actual_height))
    
    def get_bars(self):
        """Return bars as normalized coordinates relative to actual video"""
        normalized = []
        video_rect = self._get_video_rect()
        
        for bar in self.bars:
            # Map bar from full widget coordinates to video-only coordinates
            x_rel = max(0, bar.x() - video_rect.x())
            y_rel = max(0, bar.y() - video_rect.y())
            
            # Normalize based on the actual video width/height
            norm_x = x_rel / video_rect.width()
            norm_y = y_rel / video_rect.height()
            norm_w = bar.width() / video_rect.width()
            norm_h = bar.height() / video_rect.height()
            
            normalized.append({
                'x': max(0.0, min(1.0, norm_x)),
                'y': max(0.0, min(1.0, norm_y)),
                'width': max(0.01, min(1.0, norm_w)),
                'height': max(0.01, min(1.0, norm_h))
            })
            
        return normalized
    
    def set_bars(self, bars):
        """Load bars from normalized coordinates relative to actual video"""
        self.bars.clear()
        video_rect = self._get_video_rect()
        
        for bar in bars:
            # Map normalized video coordinates back to full widget pixel coordinates
            actual_x = int((bar['x'] * video_rect.width()) + video_rect.x())
            actual_y = int((bar['y'] * video_rect.height()) + video_rect.y())
            actual_w = int(bar['width'] * video_rect.width())
            actual_h = int(bar['height'] * video_rect.height())
            
            rect = QRect(actual_x, actual_y, actual_w, actual_h)
            self.bars.append(rect)
        self.update()
    
    def undo_last(self):
        if self.bars:
            self.bars.pop()
            self.update()
