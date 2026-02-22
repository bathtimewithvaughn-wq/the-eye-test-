"""
Control panel widgets - Redesigned UI
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QComboBox, QFileDialog, QGroupBox,
    QFrame, QCheckBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt, QUrl
from PyQt5.QtGui import QFont, QCursor
import webbrowser


class ClickableLabel(QLabel):
    """Label that opens a URL when clicked"""
    def __init__(self, text, url, parent=None):
        super().__init__(text, parent)
        self.url = url
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
    def mousePressEvent(self, event):
        if self.url:
            webbrowser.open(self.url)


class ControlsPanel(QWidget):
    """Side panel with all video processing controls - Redesigned"""

    # Signals
    url_changed = pyqtSignal(str)
    download_requested = pyqtSignal(str, str)  # url, quality
    process_requested = pyqtSignal()
    bars_cleared = pyqtSignal()
    undo_bar = pyqtSignal()

    # Color scheme
    WARM_COLOR = "#ff9500"
    COOL_COLOR = "#00aaff"
    ACCENT_COLOR = "#6366f1"  # Purple/indigo
    BG_DARK = "#1a1a2e"
    BG_CARD = "#16213e"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a0a0a0"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_styles()
        self._setup_ui()

    def _setup_styles(self):
        """Setup common styles"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.BG_DARK};
                color: {self.TEXT_PRIMARY};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QGroupBox {{
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #333;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 20px;
                background-color: {self.BG_CARD};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: {self.TEXT_PRIMARY};
            }}
            QLineEdit {{
                background-color: #0f0f23;
                border: 2px solid #333;
                border-radius: 8px;
                padding: 10px;
                color: {self.TEXT_PRIMARY};
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {self.ACCENT_COLOR};
            }}
            QPushButton {{
                background-color: #2d2d4a;
                border: none;
                border-radius: 8px;
                padding: 10px 15px;
                color: {self.TEXT_PRIMARY};
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #3d3d5c;
            }}
            QPushButton:pressed {{
                background-color: #4d4d6a;
            }}
            QPushButton:disabled {{
                background-color: #1a1a2e;
                color: #555;
            }}
            QComboBox {{
                background-color: #0f0f23;
                border: 2px solid #333;
                border-radius: 8px;
                padding: 8px;
                color: {self.TEXT_PRIMARY};
                font-size: 14px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid {self.TEXT_PRIMARY};
                margin-right: 10px;
            }}
            QSpinBox {{
                background-color: #0f0f23;
                border: 2px solid #333;
                border-radius: 8px;
                padding: 8px;
                color: {self.TEXT_PRIMARY};
                font-size: 14px;
            }}
            QLabel {{
                color: {self.TEXT_PRIMARY};
            }}
        """)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # === HEADER ===
        header = QVBoxLayout()
        title = QLabel("THE EYE TEST")
        title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {self.ACCENT_COLOR};
            letter-spacing: 3px;
        """)
        title.setAlignment(Qt.AlignCenter)
        header.addWidget(title)
        
        subtitle = QLabel("Football Video Processor")
        subtitle.setStyleSheet(f"font-size: 12px; color: {self.TEXT_SECONDARY};")
        subtitle.setAlignment(Qt.AlignCenter)
        header.addWidget(subtitle)
        
        layout.addLayout(header)
        layout.addSpacing(10)

        # === VIDEO SOURCE ===
        url_group = QGroupBox("📹 VIDEO SOURCE")
        url_layout = QVBoxLayout(url_group)
        url_layout.setSpacing(10)

        url_input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube URL...")
        self.url_input.setMinimumHeight(42)
        self.url_input.returnPressed.connect(self._on_load_preview)
        url_input_layout.addWidget(self.url_input)

        self.browse_btn = QPushButton("📁")
        self.browse_btn.setFixedWidth(50)
        self.browse_btn.setMinimumHeight(42)
        self.browse_btn.setToolTip("Browse local file")
        self.browse_btn.clicked.connect(self._browse_file)
        url_input_layout.addWidget(self.browse_btn)

        url_layout.addLayout(url_input_layout)

        self.load_preview_btn = QPushButton("▶  LOAD PREVIEW")
        self.load_preview_btn.setMinimumHeight(45)
        self.load_preview_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ACCENT_COLOR};
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #5558e8;
            }}
        """)
        self.load_preview_btn.clicked.connect(self._on_load_preview)
        url_layout.addWidget(self.load_preview_btn)

        layout.addWidget(url_group)

        # === BLACK BARS ===
        bars_group = QGroupBox("⬛ BLACK BARS")
        bars_layout = QVBoxLayout(bars_group)
        bars_layout.setSpacing(10)

        self.instruction_label = QLabel("Click & drag on video to draw bars")
        self.instruction_label.setStyleSheet(f"color: {self.TEXT_SECONDARY}; font-style: italic; font-size: 13px;")
        bars_layout.addWidget(self.instruction_label)

        self.bar_count_label = QLabel("0 / 5")
        self.bar_count_label.setAlignment(Qt.AlignCenter)
        self.bar_count_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {self.ACCENT_COLOR};")
        bars_layout.addWidget(self.bar_count_label)

        bar_btns = QHBoxLayout()
        self.undo_bar_btn = QPushButton("↩ Undo")
        self.undo_bar_btn.setMinimumHeight(40)
        self.undo_bar_btn.clicked.connect(self._on_undo_bar)
        bar_btns.addWidget(self.undo_bar_btn)

        self.clear_bars_btn = QPushButton("🗑 Clear")
        self.clear_bars_btn.setMinimumHeight(40)
        self.clear_bars_btn.clicked.connect(self._on_clear_bars)
        bar_btns.addWidget(self.clear_bars_btn)

        bars_layout.addLayout(bar_btns)
        layout.addWidget(bars_group)

        # === SETTINGS ===
        settings_group = QGroupBox("⚙️ SETTINGS")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(12)

        # Filter selection
        filter_row = QHBoxLayout()
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("font-size: 14px;")
        filter_row.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("🌞 WARM", "WARM")
        self.filter_combo.addItem("❄️ COOL", "COOL")
        self.filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.filter_combo)
        settings_layout.addLayout(filter_row)

        # Filter description
        self.filter_desc = QLabel("Warm tones, boosted saturation")
        self.filter_desc.setStyleSheet(f"color: {self.WARM_COLOR}; font-style: italic; font-size: 12px;")
        settings_layout.addWidget(self.filter_desc)

        # Trim time
        trim_row = QHBoxLayout()
        trim_label = QLabel("Skip first:")
        trim_label.setStyleSheet("font-size: 14px;")
        trim_row.addWidget(trim_label)
        
        self.trim_spin = QSpinBox()
        self.trim_spin.setRange(0, 3600)
        self.trim_spin.setValue(0)
        self.trim_spin.setSuffix(" sec")
        self.trim_spin.setMinimumWidth(100)
        trim_row.addWidget(self.trim_spin)
        trim_row.addStretch()
        settings_layout.addLayout(trim_row)

        # Output folder
        output_row = QHBoxLayout()
        output_label = QLabel("Output:")
        output_label.setStyleSheet("font-size: 14px;")
        output_row.addWidget(output_label)
        
        self.output_path = QLineEdit()
        self.output_path.setText("output")  # Default to output folder
        self.output_path.setReadOnly(True)
        self.output_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        output_row.addWidget(self.output_path)
        
        self.output_btn = QPushButton("📁")
        self.output_btn.setFixedWidth(40)
        self.output_btn.clicked.connect(self._select_output)
        output_row.addWidget(self.output_btn)
        settings_layout.addLayout(output_row)

        layout.addWidget(settings_group)

        # === PROCESS BUTTON ===
        layout.addSpacing(10)
        
        self.process_btn = QPushButton("🎬 PROCESS VIDEO")
        self.process_btn.setEnabled(False)
        self.process_btn.setMinimumHeight(60)
        self.process_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.process_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #10b981;
                color: white;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
            QPushButton:disabled {{
                background-color: #374151;
                color: #6b7280;
            }}
        """)
        self.process_btn.clicked.connect(self._on_process)
        layout.addWidget(self.process_btn)

        # === SPACER ===
        layout.addStretch()

        # === KO-FI LINK ===
        kofi_frame = QFrame()
        kofi_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.BG_CARD};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        kofi_layout = QVBoxLayout(kofi_frame)
        kofi_layout.setContentsMargins(10, 10, 10, 10)
        
        kofi_label = ClickableLabel(
            "☕ Support on Ko-fi",
            "https://ko-fi.com/dariusstone"
        )
        kofi_label.setAlignment(Qt.AlignCenter)
        kofi_label.setStyleSheet(f"""
            font-size: 14px;
            color: #ff5e5b;
            font-weight: bold;
            padding: 8px;
        """)
        kofi_layout.addWidget(kofi_label)
        
        layout.addWidget(kofi_frame)

        # Set initial filter description
        self._on_filter_changed(0)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "",
            "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*)"
        )
        if path:
            self.url_input.setText(path)

    def _on_load_preview(self):
        url = self.url_input.text().strip()
        if url:
            self.download_requested.emit(url, "480")

    def _on_clear_bars(self):
        self.bars_cleared.emit()

    def _on_undo_bar(self):
        self.undo_bar.emit()

    def _on_filter_changed(self, index):
        filter_name = self.filter_combo.currentData()
        if filter_name == "WARM":
            self.filter_desc.setText("Warm tones, boosted saturation")
            self.filter_desc.setStyleSheet(f"color: {self.WARM_COLOR}; font-style: italic; font-size: 12px;")
        else:
            self.filter_desc.setText("Cool tones, reduced saturation")
            self.filter_desc.setStyleSheet(f"color: {self.COOL_COLOR}; font-style: italic; font-size: 12px;")

    def _select_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_path.setText(folder)

    def _on_process(self):
        self.process_requested.emit()

    def set_bar_count(self, count):
        """Update bar count display"""
        self.bar_count_label.setText(f"{count} / 5")

        if count >= 5:
            self.bar_count_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: #ef4444;")
        elif count > 0:
            self.bar_count_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: #10b981;")
        else:
            self.bar_count_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {self.ACCENT_COLOR};")

    def set_processing_state(self, processing: bool, preview_loaded: bool):
        """Enable/disable controls during processing"""
        self.process_btn.setEnabled(preview_loaded and not processing)
        self.load_preview_btn.setEnabled(not processing)
        self.trim_spin.setEnabled(not processing)
        self.filter_combo.setEnabled(not processing)
        self.output_btn.setEnabled(not processing)
        self.browse_btn.setEnabled(not processing)

        if processing:
            self.process_btn.setText("⏳ PROCESSING...")
            self.process_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #f59e0b;
                    color: white;
                    border-radius: 12px;
                    font-size: 16px;
                    font-weight: bold;
                }}
            """)
        else:
            self.process_btn.setText("🎬 PROCESS VIDEO")
            self.process_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #10b981;
                    color: white;
                    border-radius: 12px;
                    font-size: 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #059669;
                }}
                QPushButton:disabled {{
                    background-color: #374151;
                    color: #6b7280;
                }}
            """)

    def get_url(self):
        return self.url_input.text().strip()

    def get_trim_seconds(self):
        return self.trim_spin.value()

    def get_filter(self):
        return self.filter_combo.currentData()

    def get_output_folder(self):
        return self.output_path.text() or "output"
