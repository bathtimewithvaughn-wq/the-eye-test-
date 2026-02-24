"""
Video downloader with yt-dlp library (not subprocess)
"""

import os
import shutil
from pathlib import Path
import yt_dlp


class VideoDownloader:
    """Download videos from YouTube using yt-dlp library"""
    
    def __init__(self, output_dir: str = "temp"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def download(self, url: str, quality: str = "480", max_retries: int = 3) -> str | None:
        """
        Download video from URL using yt-dlp library.
        
        Args:
            url: YouTube URL or local file path
            quality: "480" for preview or "1080" for final
            max_retries: Number of retry attempts
            
        Returns:
            Path to downloaded file, or None if failed
        """
        # Check if it's a local file
        if os.path.exists(url):
            return url
        
        # Determine format string
        if quality == "480":
            format_str = "bestvideo[height<=480]+bestaudio/best[height<=480]"
            suffix = "_480p"
        else:
            format_str = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
            suffix = "_1080p"
        
        output_template = str(self.output_dir / "%(title)s{}.%(ext)s".format(suffix))
        
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] Download attempt {attempt + 1}/{max_retries}: {url}")
                
                # Use yt-dlp as a library (works in PyInstaller bundle)
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
                
                # Find the downloaded file
                for f in self.output_dir.glob(f"*{suffix}.mp4"):
                    if quality == "1080":
                        return str(f.resolve())
                    if "_preview.wmv" in str(f):
                        return str(f.resolve())
                    return self._reencode_for_preview(str(f.resolve()))
                
                # Try to find any mp4 if suffix pattern didn't match
                for f in sorted(self.output_dir.glob("*.mp4"), key=os.path.getmtime, reverse=True):
                    if quality == "1080":
                        return str(f.resolve())
                    if "_preview.wmv" in str(f):
                        return str(f.resolve())
                    return self._reencode_for_preview(str(f.resolve()))
                
            except Exception as e:
                print(f"[DEBUG] Download error: {e}")
                continue
        
        return None
    
    def cleanup_preview(self, keep_file: str = None):
        """Remove 480p preview files after final download"""
        for f in self.output_dir.glob("*_480p*.mp4"):
            if keep_file and str(f.resolve()) == keep_file:
                continue
            try:
                f.unlink()
            except:
                pass
    
    def _reencode_for_preview(self, input_path: str) -> str:
        """Re-encode video to WMV for DirectShow compatibility"""
        if "_preview.wmv" in input_path:
            return input_path
        
        output_path = input_path.replace(".mp4", "_preview.wmv")
        
        # Find ffmpeg
        ffmpeg_path = self._find_ffmpeg()
        if not ffmpeg_path:
            print("[DEBUG] ffmpeg not found, returning original file")
            return input_path
            
        import subprocess
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
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='ignore',
                timeout=300
            )
            if result.returncode == 0 and os.path.exists(output_path):
                print(f"[DEBUG] Re-encode successful: {output_path}")
                # Remove original
                try:
                    os.unlink(input_path)
                except:
                    pass
                return output_path
            else:
                print(f"[DEBUG] Re-encode failed: {result.stderr[:300] if result.stderr else 'unknown error'}")
        except Exception as e:
            print(f"[DEBUG] Re-encode error: {e}")
        
        return input_path
    
    def _find_ffmpeg(self) -> str | None:
        """Find ffmpeg executable"""
        # Check PATH first
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path

        # Check app's own directory (for packaged releases)
        app_dir = Path(__file__).parent.parent  # Go up from processor/ to app root
        app_ffmpeg = app_dir / "ffmpeg.exe"
        if app_ffmpeg.exists():
            return str(app_ffmpeg)

        # Check common Windows locations
        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe"),
            os.path.expandvars(r"%USERPROFILE%\miniconda3\Library\bin\ffmpeg.exe"),
            os.path.expandvars(r"%USERPROFILE%\anaconda3\Library\bin\ffmpeg.exe"),
        ]

        for p in common_paths:
            if os.path.exists(p):
                return p

        return None
    
    def download_1080p(self, url: str) -> str | None:
        """Download 1080p version for final processing (no re-encoding)"""
        return self.download(url, quality="1080")
