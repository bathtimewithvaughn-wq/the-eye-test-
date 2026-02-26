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
        
        self.bars_normalized = []  # Store as normalized 0-1 coordinates
        self.current_bar = None
        self.start_pos = None
        self.on_bar_added = None  # Callback when bar is added
        
        self.update_geometry()
    
    def update_geometry(self):
        """Position overlay over video widget"""
        if self.video_frame:
            self.setGeometry(self.video_frame.rect())
            self.raise_()
            self.show()
    
    def _get_video_rect(self):
        """Get the actual pixel rect where the video is rendering inside the view"""
        if not hasattr(self, 'video_frame') or not hasattr(self.video_frame, 'video_item'):
            return self.rect()
            
        view = self.video_frame
        item = view.video_item
        
        # Get the DISPLAY size (what the user actually sees)
        display_rect = item.boundingRect()
        display_width = int(display_rect.width())
        display_height = int(display_rect.height())
        
        if display_width <= 0 or display_height <= 0:
            return self.rect()
        
        # Calculate aspect ratio from display size
        video_ratio = display_width / display_height if display_height > 0 else 16/9
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
    
    def paintEvent(self, event):
        if not self.bars_normalized and not self.current_bar:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        video_rect = self._get_video_rect()
        
        # Draw stored bars - convert normalized to widget coords fresh each time
        for bar in self.bars_normalized:
            widget_x = int(bar['x'] * video_rect.width()) + video_rect.x()
            widget_y = int(bar['y'] * video_rect.height()) + video_rect.y()
            widget_w = int(bar['width'] * video_rect.width())
            widget_h = int(bar['height'] * video_rect.height())
            widget_bar = QRect(widget_x, widget_y, widget_w, widget_h)
            
            painter.fillRect(widget_bar, QColor(0, 0, 0, 220))
            painter.setPen(QPen(QColor(255, 255, 0), 2))
            painter.drawRect(widget_bar)
        
        # Draw current dragging bar (already in widget coords)
        if self.current_bar:
            painter.fillRect(self.current_bar, QColor(0, 255, 0, 100))
            painter.setPen(QPen(QColor(255, 255, 0), 2, Qt.DashLine))
            painter.drawRect(self.current_bar)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and len(self.bars_normalized) < 5:
            self.start_pos = event.pos()
            self.current_bar = QRect(self.start_pos, self.start_pos)
        elif event.button() == Qt.RightButton and self.bars_normalized:
            self.bars_normalized.pop()
            self.update()
            if self.on_bar_added:
                self.on_bar_added(len(self.bars_normalized))
    
    def mouseMoveEvent(self, event):
        if self.start_pos:
            self.current_bar = QRect(self.start_pos, event.pos()).normalized()
            self.repaint()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.current_bar:
            if self.current_bar.width() > 5 and self.current_bar.height() > 5:
                # Convert to normalized immediately and store
                video_rect = self._get_video_rect()
                norm_bar = {
                    'x': (self.current_bar.x() - video_rect.x()) / video_rect.width(),
                    'y': (self.current_bar.y() - video_rect.y()) / video_rect.height(),
                    'width': self.current_bar.width() / video_rect.width(),
                    'height': self.current_bar.height() / video_rect.height()
                }
                self.bars_normalized.append(norm_bar)
                
                if hasattr(self, 'on_bar_added') and self.on_bar_added:
                    self.on_bar_added(len(self.bars_normalized))
            self.current_bar = None
            self.start_pos = None
            self.repaint()
    
    def clear_bars(self):
        self.bars_normalized.clear()
        self.update()
    
    def get_bars(self):
        """Return bars as normalized coordinates"""
        return self.bars_normalized.copy()
    
    def set_bars(self, bars):
        """Load bars from normalized coordinates"""
        self.bars_normalized = bars.copy() if bars else []
        self.update()
    
    def undo_last(self):
        if self.bars_normalized:
            self.bars_normalized.pop()
            self.update()
