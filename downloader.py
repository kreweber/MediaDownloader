"""
Download engine — yt-dlp wrapper running in a QThread.
Supports YouTube, TikTok, Instagram, Pinterest (photos + videos).
Always downloads in the best available quality.
"""

import os
import re
import time
import glob
from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp


def _find_ffmpeg() -> str | None:
    """Find bundled ffmpeg binary next to this script/executable."""
    import sys
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    ffmpeg_dir = os.path.join(base_dir, 'ffmpeg')
    # Look for ffmpeg.exe recursively
    matches = glob.glob(os.path.join(ffmpeg_dir, '**', 'ffmpeg.exe'), recursive=True)
    if matches:
        return os.path.dirname(matches[0])
    # Fallback — maybe it's in system PATH
    return None


FFMPEG_DIR = _find_ffmpeg()


PLATFORM_PATTERNS = {
    'youtube': r'(youtube\.com|youtu\.be)',
    'tiktok': r'tiktok\.com',
    'instagram': r'instagram\.com',
    'pinterest': r'pinterest\.(com|ru|co\.uk|de|fr|ca)',
}


def detect_platform(url: str) -> str:
    """Return platform name based on URL pattern."""
    for platform, pattern in PLATFORM_PATTERNS.items():
        if re.search(pattern, url, re.IGNORECASE):
            return platform
    return 'other'


class DownloadWorker(QThread):
    """Worker thread that downloads media via yt-dlp."""

    # Signals
    progress = pyqtSignal(dict)       # {percent, speed, eta, downloaded, total}
    status_update = pyqtSignal(str)   # status message
    info_ready = pyqtSignal(dict)     # {title, thumbnail, platform, duration, ...}
    finished_ok = pyqtSignal(str)     # final file path
    error = pyqtSignal(str)           # error message

    def __init__(self, url: str, output_dir: str, parent=None):
        super().__init__(parent)
        self.url = url.strip()
        self.output_dir = output_dir
        self._is_cancelled = False

    # ── progress hook ────────────────────────────────────────────
    def _progress_hook(self, d: dict):
        if self._is_cancelled:
            raise Exception("Download cancelled by user")

        status = d.get('status', '')

        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0) or 0
            eta = d.get('eta', 0) or 0

            if total > 0:
                percent = downloaded / total * 100
            else:
                percent = 0

            self.progress.emit({
                'percent': percent,
                'speed': speed,
                'eta': eta,
                'downloaded': downloaded,
                'total': total,
                'status': 'downloading',
            })

        elif status == 'finished':
            self.progress.emit({
                'percent': 100,
                'speed': 0,
                'eta': 0,
                'downloaded': d.get('total_bytes', 0),
                'total': d.get('total_bytes', 0),
                'status': 'merging',
            })
            self.status_update.emit('Processing file...')

    # ── main run ─────────────────────────────────────────────────
    def run(self):
        try:
            platform = detect_platform(self.url)
            self.status_update.emit(f'Getting info ({platform})...')

            outtmpl = os.path.join(self.output_dir, '%(title)s.%(ext)s')

            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'outtmpl': outtmpl,
                'progress_hooks': [self._progress_hook],
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30,
                'retries': 3,
                'fragment_retries': 3,
            }

            # Use bundled ffmpeg if available
            if FFMPEG_DIR:
                ydl_opts['ffmpeg_location'] = FFMPEG_DIR

            # Platform-specific tweaks
            if platform == 'instagram':
                ydl_opts['cookiesfrombrowser'] = None  # may need cookies
            if platform == 'tiktok':
                ydl_opts['format'] = 'best'  # TikTok usually has single stream

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(self.url, download=False)
                if info:
                    self.info_ready.emit({
                        'title': info.get('title', 'Untitled'),
                        'thumbnail': info.get('thumbnail', ''),
                        'platform': platform,
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', ''),
                        'ext': info.get('ext', 'mp4'),
                        'is_photo': info.get('ext', '') in ('jpg', 'jpeg', 'png', 'webp'),
                    })

                # Now download
                self.status_update.emit('Downloading...')
                ydl.download([self.url])

            # Find the downloaded file
            final_path = outtmpl
            if info:
                title = info.get('title', 'download')
                # sanitize filename
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                ext = 'mp4'
                final_path = os.path.join(self.output_dir, f"{safe_title}.{ext}")

            self.finished_ok.emit(final_path)

        except Exception as e:
            err_msg = str(e)
            if "cancelled" in err_msg.lower():
                self.status_update.emit('Cancelled')
            else:
                self.error.emit(err_msg)

    def cancel(self):
        self._is_cancelled = True
