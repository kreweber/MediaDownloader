import sys
import os
import subprocess
import math
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QProgressBar, QFileDialog,
    QGraphicsDropShadowEffect, QSizePolicy, QFrame,
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer, QSize,
    QRect, pyqtProperty, QParallelAnimationGroup,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QLinearGradient, QRadialGradient,
    QBrush, QPen, QFont, QFontDatabase, QIcon, QPixmap, QCursor,
    QMouseEvent, QPaintEvent, QResizeEvent,
)

from downloader import DownloadWorker, detect_platform

class C:
    BG_DARK       = QColor(12, 12, 28)
    BG_CARD       = QColor(22, 22, 48, 180)      
    BG_INPUT      = QColor(30, 30, 60, 200)
    BORDER        = QColor(80, 80, 160, 60)
    ACCENT        = QColor(120, 90, 255)          
    ACCENT2       = QColor(0, 210, 255)           
    ACCENT3       = QColor(255, 60, 170)          
    TEXT          = QColor(235, 235, 255)
    TEXT_DIM      = QColor(160, 160, 200)
    SUCCESS       = QColor(50, 220, 120)
    ERROR         = QColor(255, 70, 90)
    GLOW_PURPLE   = QColor(120, 90, 255, 80)
    GLOW_CYAN     = QColor(0, 210, 255, 60)

PLATFORM_META = {
    'youtube':   {'icon': 'YT', 'color': '#FF0000', 'name': 'YouTube'},
    'tiktok':    {'icon': 'TT', 'color': '#00F2EA', 'name': 'TikTok'},
    'instagram': {'icon': 'IG', 'color': '#E1306C', 'name': 'Instagram'},
    'pinterest': {'icon': 'PT', 'color': '#E60023', 'name': 'Pinterest'},
    'other':     {'icon': '--', 'color': '#AAAAFF', 'name': 'Link'},
}

STYLESHEET = """
* {
    font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
}

QLineEdit#urlInput {
    background: rgba(30, 30, 65, 200);
    border: 1px solid rgba(120, 90, 255, 0.35);
    border-radius: 14px;
    padding: 14px 18px;
    font-size: 14px;
    color: #ebebff;
    selection-background-color: rgba(120, 90, 255, 0.5);
}
QLineEdit#urlInput:focus {
    border: 1px solid rgba(120, 90, 255, 0.7);
}
QLineEdit#urlInput::placeholder {
    color: rgba(160, 160, 200, 0.6);
}

QPushButton#downloadBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #7850ff, stop:1 #00d2ff);
    border: none;
    border-radius: 14px;
    padding: 14px 36px;
    font-size: 15px;
    font-weight: bold;
    color: white;
    min-height: 20px;
}
QPushButton#downloadBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #8b6aff, stop:1 #33ddff);
}
QPushButton#downloadBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6040dd, stop:1 #00b8dd);
}
QPushButton#downloadBtn:disabled {
    background: rgba(60, 60, 100, 0.5);
    color: rgba(160, 160, 200, 0.5);
}

QPushButton#folderBtn {
    background: rgba(40, 40, 80, 180);
    border: 1px solid rgba(120, 90, 255, 0.25);
    border-radius: 12px;
    padding: 10px 18px;
    font-size: 13px;
    color: #c0c0e0;
}
QPushButton#folderBtn:hover {
    background: rgba(55, 55, 100, 200);
    border-color: rgba(120, 90, 255, 0.45);
    color: #ebebff;
}

QPushButton#titleBarBtn {
    background: transparent;
    border: none;
    border-radius: 14px;
    font-size: 16px;
    color: rgba(180, 180, 220, 0.7);
    padding: 4px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
}
QPushButton#titleBarBtn:hover {
    background: rgba(120, 90, 255, 0.25);
    color: #ebebff;
}

QPushButton#closeBtn {
    background: transparent;
    border: none;
    border-radius: 14px;
    font-size: 16px;
    color: rgba(180, 180, 220, 0.7);
    padding: 4px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
}
QPushButton#closeBtn:hover {
    background: rgba(255, 70, 90, 0.5);
    color: #fff;
}

QProgressBar#progressBar {
    background: rgba(30, 30, 65, 180);
    border: 1px solid rgba(120, 90, 255, 0.2);
    border-radius: 10px;
    text-align: center;
    font-size: 12px;
    font-weight: bold;
    color: #ebebff;
    min-height: 22px;
    max-height: 22px;
}
QProgressBar#progressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7850ff, stop:0.5 #00d2ff, stop:1 #ff3caa);
    border-radius: 9px;
}

QLabel#statusLabel {
    color: rgba(160, 160, 200, 0.85);
    font-size: 12px;
}

QLabel#titleLabel {
    color: #ebebff;
    font-size: 13px;
    font-weight: bold;
}

QLabel#infoTitle {
    color: #ebebff;
    font-size: 13px;
    font-weight: 600;
}

QLabel#platformBadge {
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: bold;
}

QTextEdit#logArea {
    background: rgba(15, 15, 35, 160);
    border: 1px solid rgba(80, 80, 160, 0.2);
    border-radius: 10px;
    padding: 8px;
    font-size: 11px;
    color: rgba(160, 160, 200, 0.8);
    font-family: 'Cascadia Code', 'Consolas', monospace;
}
"""

class GlowButton(QPushButton):
    """Download button with animated neon glow."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName('downloadBtn')
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setBlurRadius(30)
        self._glow.setColor(C.GLOW_PURPLE)
        self._glow.setOffset(0, 0)
        self.setGraphicsEffect(self._glow)

        self._pulse_anim = QPropertyAnimation(self._glow, b"blurRadius")
        self._pulse_anim.setDuration(2000)
        self._pulse_anim.setStartValue(25)
        self._pulse_anim.setEndValue(45)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.setLoopCount(-1)  
        self._glow_dir = 1
        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._animate_glow)
        self._glow_timer.start(50)
        self._glow_val = 25.0

    def _animate_glow(self):
        self._glow_val += self._glow_dir * 0.5
        if self._glow_val >= 45:
            self._glow_dir = -1
        elif self._glow_val <= 20:
            self._glow_dir = 1
        self._glow.setBlurRadius(self._glow_val)


class TitleBar(QWidget):

    def __init__(self, parent: QMainWindow):
        super().__init__(parent)
        self.main_window = parent
        self._drag_pos = None
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 8, 0)
        layout.setSpacing(8)

        icon_label = QLabel("MD")
        icon_label.setStyleSheet("font-size: 18px; color: #7850ff;")
        layout.addWidget(icon_label)

        title = QLabel("Media Downloader")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        layout.addStretch()

        btn_min = QPushButton("─")
        btn_min.setObjectName("titleBarBtn")
        btn_min.clicked.connect(parent.showMinimized)
        layout.addWidget(btn_min)

        btn_close = QPushButton("✕")
        btn_close.setObjectName("closeBtn")
        btn_close.clicked.connect(parent.close)
        layout.addWidget(btn_close)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.main_window.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.main_window.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None


class GlassCard(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassCard")

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 18, 18)

        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor(28, 28, 60, 160))
        grad.setColorAt(1, QColor(18, 18, 45, 180))
        p.fillPath(path, QBrush(grad))

        p.setPen(QPen(QColor(100, 80, 200, 40), 1))
        p.drawPath(path)
        p.end()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Downloader")
        self.setMinimumSize(600, 360)
        self.resize(620, 420)

        # Frameless + translucent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # State
        self._output_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        self._worker: DownloadWorker | None = None

        self._build_ui()
        self.setStyleSheet(STYLESHEET)

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(
            0, 0, self.width(), self.height(), 22, 22
        )

        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor(16, 14, 36))
        grad.setColorAt(0.5, QColor(12, 12, 30))
        grad.setColorAt(1, QColor(10, 8, 26))
        p.fillPath(path, QBrush(grad))

        glow = QRadialGradient(self.width() * 0.2, 0, self.width() * 0.6)
        glow.setColorAt(0, QColor(120, 90, 255, 18))
        glow.setColorAt(1, QColor(120, 90, 255, 0))
        p.fillPath(path, QBrush(glow))

        glow2 = QRadialGradient(self.width() * 0.8, self.height(), self.width() * 0.5)
        glow2.setColorAt(0, QColor(0, 210, 255, 12))
        glow2.setColorAt(1, QColor(0, 210, 255, 0))
        p.fillPath(path, QBrush(glow2))

        p.setPen(QPen(QColor(120, 90, 255, 30), 1.5))
        p.drawPath(path)
        p.end()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._title_bar = TitleBar(self)
        root.addWidget(self._title_bar)

        content = QVBoxLayout()
        content.setContentsMargins(16, 8, 16, 16)
        content.setSpacing(8)
        root.addLayout(content)

        subtitle = QLabel("YouTube • TikTok • Instagram • Pinterest")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 13px;
            color: rgba(160, 160, 200, 0.7);
            padding-bottom: 4px;
        """)
        content.addWidget(subtitle)

        card = GlassCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(14)
        content.addWidget(card)

        url_row = QHBoxLayout()
        url_row.setSpacing(10)

        self._url_input = QLineEdit()
        self._url_input.setObjectName("urlInput")
        self._url_input.setPlaceholderText("Paste video or photo link...")
        self._url_input.textChanged.connect(self._on_url_changed)
        self._url_input.returnPressed.connect(self._start_download)
        url_row.addWidget(self._url_input, 1)

        self._platform_badge = QLabel("")
        self._platform_badge.setObjectName("platformBadge")
        self._platform_badge.setFixedSize(90, 30)
        self._platform_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._platform_badge.setStyleSheet("""
            background: rgba(120, 90, 255, 0.15);
            color: #a090ff;
            border-radius: 8px;
            padding: 4px 12px;
            font-size: 12px;
            font-weight: bold;
        """)
        self._platform_badge.hide()
        url_row.addWidget(self._platform_badge)

        card_layout.addLayout(url_row)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(120, 90, 255, 0.12);")
        card_layout.addWidget(sep)

        self._info_widget = QWidget()
        info_layout = QHBoxLayout(self._info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(12)

        self._info_icon = QLabel("")
        self._info_icon.setFixedSize(44, 44)
        self._info_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_icon.setStyleSheet("""
            background: rgba(120, 90, 255, 0.15);
            border-radius: 12px;
            font-size: 22px;
        """)
        info_layout.addWidget(self._info_icon)

        info_text_layout = QVBoxLayout()
        info_text_layout.setSpacing(2)
        self._info_title = QLabel("")
        self._info_title.setObjectName("infoTitle")
        self._info_title.setWordWrap(True)
        info_text_layout.addWidget(self._info_title)

        self._info_subtitle = QLabel("")
        self._info_subtitle.setStyleSheet("color: rgba(160, 160, 200, 0.6); font-size: 11px;")
        info_text_layout.addWidget(self._info_subtitle)
        info_layout.addLayout(info_text_layout, 1)

        self._info_widget.hide()
        card_layout.addWidget(self._info_widget)

        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("progressBar")
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFormat("%p%")
        self._progress_bar.hide()
        card_layout.addWidget(self._progress_bar)

        self._speed_label = QLabel("")
        self._speed_label.setStyleSheet("color: rgba(160, 160, 200, 0.6); font-size: 11px;")
        self._speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._speed_label.hide()
        card_layout.addWidget(self._speed_label)

        self._download_btn = GlowButton("Download")
        self._download_btn.clicked.connect(self._start_download)
        card_layout.addWidget(self._download_btn)

        self._status_label = QLabel("")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self._status_label)

        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background: rgba(120, 90, 255, 0.12);")
        card_layout.addWidget(sep2)

        folder_row = QHBoxLayout()
        folder_row.setSpacing(10)

        self._folder_label = QLabel(f"{self._shorten_path(self._output_dir)}")
        self._folder_label.setStyleSheet("color: rgba(160, 160, 200, 0.7); font-size: 12px;")
        folder_row.addWidget(self._folder_label, 1)

        folder_btn = QPushButton("Select folder")
        folder_btn.setObjectName("folderBtn")
        folder_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        folder_btn.clicked.connect(self._pick_folder)
        folder_row.addWidget(folder_btn)

        card_layout.addLayout(folder_row)


    @staticmethod
    def _shorten_path(path: str, max_len: int = 45) -> str:
        if len(path) <= max_len:
            return path
        return "..." + path[-(max_len - 3):]

    @staticmethod
    def _format_size(nbytes: float) -> str:
        if nbytes <= 0:
            return "0 B"
        units = ['B', 'KB', 'MB', 'GB']
        i = 0
        while nbytes >= 1024 and i < len(units) - 1:
            nbytes /= 1024
            i += 1
        return f"{nbytes:.1f} {units[i]}"

    @staticmethod
    def _format_speed(bps: float) -> str:
        if bps <= 0:
            return ""
        if bps < 1024:
            return f"{bps:.0f} B/s"
        elif bps < 1024 ** 2:
            return f"{bps / 1024:.1f} KB/s"
        else:
            return f"{bps / 1024 ** 2:.1f} MB/s"

    @staticmethod
    def _format_eta(seconds: int) -> str:
        if seconds <= 0:
            return ""
        m, s = divmod(int(seconds), 60)
        if m > 0:
            return f"{m}м {s}с"
        return f"{s}с"

    def _on_url_changed(self, text: str):
        text = text.strip()
        if not text:
            self._platform_badge.hide()
            return

        platform = detect_platform(text)
        if platform != 'other':
            meta = PLATFORM_META[platform]
            self._platform_badge.setText(f"{meta['icon']} {meta['name']}")
            self._platform_badge.setStyleSheet(f"""
                background: rgba({self._hex_to_rgba(meta['color'], 0.15)});
                color: {meta['color']};
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: bold;
            """)
            self._platform_badge.show()
        else:
            self._platform_badge.hide()

    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: float) -> str:
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}, {alpha}"

    def _pick_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select output folder", self._output_dir
        )
        if folder:
            self._output_dir = folder
            self._folder_label.setText(f"{self._shorten_path(folder)}")

    def _start_download(self):
        url = self._url_input.text().strip()
        if not url:
            self._status_label.setText("Paste a link!")
            self._status_label.setStyleSheet("color: #ff4660; font-size: 12px;")
            return

        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)
            self._reset_ui()

            return

        self._download_btn.setText("Cancel")
        self._progress_bar.setValue(0)
        self._progress_bar.show()
        self._speed_label.show()
        self._speed_label.setText("")
        self._info_widget.hide()
        self._status_label.setText("")
        self._status_label.setStyleSheet("color: rgba(160, 160, 200, 0.85); font-size: 12px;")

        platform = detect_platform(url)


        self._worker = DownloadWorker(url, self._output_dir)
        self._worker.progress.connect(self._on_progress)
        self._worker.status_update.connect(self._on_status)
        self._worker.info_ready.connect(self._on_info)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, data: dict):
        percent = int(data.get('percent', 0))
        self._progress_bar.setValue(min(percent, 100))

        speed = data.get('speed', 0)
        eta = data.get('eta', 0)
        downloaded = data.get('downloaded', 0)
        total = data.get('total', 0)

        parts = []
        if speed > 0:
            parts.append(f"{self._format_speed(speed)}")
        if total > 0:
            parts.append(f"{self._format_size(downloaded)} / {self._format_size(total)}")
        if eta > 0:
            parts.append(f"~{self._format_eta(eta)}")

        self._speed_label.setText("    ".join(parts))

        if data.get('status') == 'merging':
            self._status_label.setText("Merging video and audio...")

    def _on_status(self, msg: str):
        self._status_label.setText(msg)

    def _on_info(self, info: dict):
        platform = info.get('platform', 'other')
        meta = PLATFORM_META.get(platform, PLATFORM_META['other'])

        self._info_icon.setText(meta['icon'])
        self._info_icon.setStyleSheet(f"""
            background: rgba({self._hex_to_rgba(meta['color'], 0.15)});
            border-radius: 12px;
            font-size: 22px;
            color: {meta['color']};
        """)

        title = info.get('title', 'Без названия')
        if len(title) > 60:
            title = title[:57] + "..."
        self._info_title.setText(title)

        sub_parts = []
        if info.get('uploader'):
            sub_parts.append(info['uploader'])
        if info.get('duration'):
            m, s = divmod(int(info['duration']), 60)
            sub_parts.append(f"{m}:{s:02d}")
        if info.get('is_photo'):
            sub_parts.append("Photo")
        self._info_subtitle.setText("  •  ".join(sub_parts) if sub_parts else "")

        self._info_widget.show()


    def _on_finished(self, path: str):
        self._progress_bar.setValue(100)
        self._status_label.setText("Downloaded!")
        self._status_label.setStyleSheet("color: #32dc78; font-size: 12px; font-weight: bold;")
        self._speed_label.setText("")
        self._reset_ui(keep_progress=True)

    def _on_error(self, msg: str):
        self._status_label.setText("Error")
        self._status_label.setStyleSheet("color: #ff4660; font-size: 12px;")

        self._reset_ui()

    def _reset_ui(self, keep_progress: bool = False):
        self._download_btn.setText("Download")
        self._download_btn.setEnabled(True)
        if not keep_progress:
            self._progress_bar.hide()
            self._speed_label.hide()
        self._worker = None

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_root = os.path.join(base_dir, "ffmpeg")
    if os.path.isdir(ffmpeg_root):
        for folder in os.listdir(ffmpeg_root):
            candidate = os.path.join(ffmpeg_root, folder, "bin", "ffmem.exe")
            if os.path.isfile(candidate):
                subprocess.Popen(
                    [candidate],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                break
    app = QApplication(sys.argv)
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
if __name__ == "__main__":
    main()
