"""
Video downloader with yt-dlp library (not subprocess)
"""

import os
import sys
import ctypes
import shutil
from pathlib import Path
import yt_dlp
import subprocess


def get_app_dir():
    """Get the app directory (works for bundled and development)"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


class VideoDownloader:
    """Download videos from YouTube using yt-dlp library"""
    
    def __init__(self, output_dir: str = "temp"):
        app_dir = get_app_dir()
        self.output_dir = app_dir / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def download(self, url: str, quality: str = "480", max_retries: int = 3) -> str | None:
        """
        Download video from URL using yt-dlp library.
        Downloads 480p and re-encodes to WMV for DirectShow preview.
        """
        if os.path.exists(url):
            return url
        
        format_str = "bestvideo[height<=480]+bestaudio/best[height<=480]"
        suffix = "_480p"
        
        output_template = str(self.output_dir / "%(title)s{}.%(ext)s".format(suffix))
        
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Download attempt {attempt + 1}/{max_retries}: {url}")
                
                ydl_opts = {
                    'format': format_str,
                    'outtmpl': output_template,
                    'merge_output_format': 'mp4',
                    'noplaylist': True,
                    'quiet': False,
                    'no_warnings': False,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # Find the downloaded file and re-encode to WMV
                for f in self.output_dir.glob(f"*{suffix}.mp4"):
                    if "_preview.wmv" in str(f):
                        return str(f.resolve())
                    return self._reencode_for_preview(str(f.resolve()))
                
                for f in sorted(self.output_dir.glob("*.mp4"), key=os.path.getmtime, reverse=True):
                    if "_preview.wmv" in str(f):
                        return str(f.resolve())
                    return self._reencode_for_preview(str(f.resolve()))
                
            except Exception as e:
                print(f"[DEBUG] Download error: {e}")
                continue
        
        return None
    
    def _reencode_for_preview(self, input_path: str) -> str:
        """Re-encode video to WMV for DirectShow compatibility"""
        if "_preview.wmv" in input_path:
            return input_path
        
        output_path = input_path.replace(".mp4", "_preview.wmv")
        
        ffmpeg_path = self._find_ffmpeg()
        if not ffmpeg_path:
            print("[DEBUG] ffmpeg not found, returning original file")
            return input_path
            
        cmd = [
            ffmpeg_path,
            "-i", input_path,
            "-c:v", "wmv2",
            "-q:v", "3",
            "-r", "30",
            "-s", "854x480",
            "-an",
            "-y", output_path
        ]
        print("[DEBUG] Re-encoding to WMV for DirectShow")
        
        if sys.platform == "win32":
            ctypes.windll.kernel32.SetDllDirectoryW(None)
        
        env = dict(os.environ)
        if getattr(sys, 'frozen', False):
            meipass = getattr(sys, '_MEIPASS', None)
            if meipass and 'PATH' in env:
                paths = env['PATH'].split(os.pathsep)
                clean_paths = [p for p in paths if meipass not in p]
                env['PATH'] = os.pathsep.join(clean_paths)
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            errors='ignore',
            timeout=300,
            env=env
        )
        if result.returncode == 0 and os.path.exists(output_path):
            print(f"[DEBUG] Re-encode successful: {output_path}")
            try:
                os.unlink(input_path)
            except:
                pass
            return output_path
        else:
            print(f"[DEBUG] Re-encode failed: {result.stderr[:300] if result.stderr else 'unknown error'}")
        
        return input_path
    
    def _find_ffmpeg(self) -> str | None:
        """Find ffmpeg executable"""
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path

        app_dir = Path(__file__).parent.parent
        app_ffmpeg = app_dir / "ffmpeg.exe"
        if app_ffmpeg.exists():
            return str(app_ffmpeg)

        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe"),
        ]

        for p in common_paths:
            if os.path.exists(p):
                return p

        return None
    
    def cleanup_preview(self, keep_file: str = None):
        """Remove old preview files"""
        for f in self.output_dir.glob("*_480p*.mp4"):
            if keep_file and str(f.resolve()) == keep_file:
                continue
            try:
                f.unlink()
            except:
                pass
    
    def download_1080p(self, url: str) -> str | None:
        """Download 1080p version for final processing"""
        if os.path.exists(url):
            return url
        
        format_str = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]"
        suffix = "_1080p"
        output_template = str(self.output_dir / "%(title)s{}.%(ext)s".format(suffix))
        
        for attempt in range(3):
            try:
                print(f"[DEBUG] Download 1080p attempt {attempt + 1}/3: {url}")
                
                ydl_opts = {
                    'format': format_str,
                    'outtmpl': output_template,
                    'merge_output_format': 'mp4',
                    'noplaylist': True,
                    'quiet': False,
                    'no_warnings': False,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                for f in self.output_dir.glob(f"*{suffix}.mp4"):
                    print(f"[DEBUG] 1080p download complete: {f}")
                    return str(f.resolve())
                
            except Exception as e:
                print(f"[DEBUG] Download error: {e}")
                continue
        
        return None
