"""
Video encoder - processing pipeline with OpenCV cartoon effect + FFmpeg filters
"""

import subprocess
import os
import shutil
import sys
import time
import re
import ctypes
from pathlib import Path
from typing import Callable
import cv2
import numpy as np
import psutil

from processor.downloader import VideoDownloader
from utils.storage import check_disk_space, format_size

try:
    import wmi
except ImportError:
    wmi = None


def get_app_dir():
    """Get the app directory - RESOLVED ONCE at module load"""
    if getattr(sys, 'frozen', False):
        # Bundled with PyInstaller - use temp extraction directory
        return Path(sys._MEIPASS).resolve()
    else:
        # Development: project root (encoder.py is in processor/, so go up 2 levels)
        return Path(__file__).parent.parent.resolve()


# RESOLVE APP DIR ONCE - not in functions
APP_DIR = get_app_dir()


def find_ffmpeg() -> str:
    """Find ffmpeg executable"""
    # Check bundled location first
    bundled = APP_DIR / "ffmpeg.exe"
    if bundled.exists():
        return str(bundled)
    
    # Check PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    
    # Fallback
    return "ffmpeg"


def run_ffmpeg_safely(cmd, creationflags=0):
    """
    Run FFmpeg with PyInstaller environment cleanup.
    """
    if sys.platform == "win32":
        ctypes.windll.kernel32.SetDllDirectoryW(None)
    
    env = dict(os.environ)
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass and 'PATH' in env:
            paths = env['PATH'].split(os.pathsep)
            clean_paths = [p for p in paths if meipass not in p]
            env['PATH'] = os.pathsep.join(clean_paths)
    
    print(f"[DEBUG] FFmpeg command: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=creationflags,
        env=env
    )
    
    try:
        stdout, stderr = process.communicate(timeout=600)
        print(f"[DEBUG] FFmpeg done, return code: {process.returncode}")
        if process.returncode != 0:
            print(f"[ERROR] FFmpeg stderr: {stderr[-500:]}")
    except subprocess.TimeoutExpired:
        print(f"[ERROR] FFmpeg TIMEOUT after 600s")
        process.kill()
        raise RuntimeError("FFmpeg timed out after 10 minutes")
    
    if process.returncode != 0:
        error_msg = stderr[-500:] if stderr else "Unknown error"
        raise RuntimeError(f"FFmpeg failed (code {process.returncode}): {error_msg}")
    
    return stdout, stderr


class VideoProcessor:
    """Process video with cartoon effect, black bars, filters, and effects"""

    CARTOON_SETTINGS = {
        'blur_size': 5,
        'canny_low': 40,
        'canny_high': 100,
        'edge_opacity': 0.25,
    }

    FILTER_PRESETS = {
        "WARM": {
            "description": "Warm tones, boosted saturation",
            "ffmpeg": "colorbalance=rm=0.08:bm=-0.08,hue=s=1.10,format=yuv420p,lutyuv=y=val*1.10"
        },
        "COOL": {
            "description": "Cool tones, reduced saturation",
            "ffmpeg": "colorbalance=rm=-0.08:bm=0.08,hue=s=0.80,format=yuv420p,lutyuv=y=(val-128)*1.05+128"
        }
    }

    COPYRIGHT_AVOIDANCE = {
        'speed': 1.12,
        'zoom': 1.08,
    }

    # Logo at 150px
    LOGO_PATH = APP_DIR / "assets" / "logo.jpg"
    LOGO_SIZE = 150
    LOGO_MARGIN = 20

    def __init__(self, input_path, output_folder, bars, trim_seconds, filter_name, original_url=None, add_logo=True, mirror=False):
        self.input_path = input_path
        self.output_folder = (APP_DIR / output_folder).resolve() if output_folder else (APP_DIR / "output").resolve()
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.bars = bars
        self.trim_seconds = trim_seconds
        self.filter_name = filter_name
        self.original_url = original_url
        self.add_logo = add_logo
        self.mirror = mirror
        self.downloader = VideoDownloader(str(APP_DIR / "temp"))
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _get_cpu_temp(self):
        """Get CPU temperature with WMI fallback"""
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if any(x in name.lower() for x in ['k10temp', 'coretemp', 'cpu', 'processor']):
                        return max(e.current for e in entries)
        except:
            pass

        if wmi and sys.platform == 'win32':
            try:
                w = wmi.WMI(namespace="root\\wmi")
                temps = w.MSAcpi_ThermalZoneTemperature()
                if temps:
                    return (temps[0].CurrentTemperature / 10.0) - 273.15
            except:
                pass

        try:
            freq = psutil.cpu_freq()
            if freq and freq.current < freq.max * 0.9:
                return 75
        except:
            pass

        return 0

    def _generate_output_path(self, input_path):
        """Generate descriptive output filename"""
        timestamp = int(time.time())
        filter_tag = self.filter_name if self.filter_name else "NOFILTER"
        mirror_tag = "_MIRROR" if self.mirror else ""
        bars_tag = "_BARS" if self.bars else ""

        if self.original_url:
            match = re.search(r'[?&]v=([^&]+)', self.original_url)
            video_id = match.group(1) if match else f"vid_{timestamp}"
        else:
            video_id = Path(input_path).stem

        filename = f"{video_id}_{filter_tag}{mirror_tag}{bars_tag}_{timestamp}.mp4"
        return self.output_folder / filename

    def _apply_cartoon_opencv(self, input_path, output_path, progress_callback=None):
        """Apply cartoon effect using FFmpeg pipe"""
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {input_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if width <= 0 or height <= 0 or fps <= 0:
            cap.release()
            raise ValueError(f"Invalid video properties: {width}x{height}@{fps}")

        frames_to_skip = int(self.trim_seconds * fps) if self.trim_seconds > 0 else 0
        if frames_to_skip > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frames_to_skip)
            total_frames -= frames_to_skip

        settings = self.CARTOON_SETTINGS
        blur_size = settings['blur_size']
        if blur_size % 2 == 0:
            blur_size += 1

        ffmpeg_cmd = [
            find_ffmpeg(), '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{width}x{height}',
            '-pix_fmt', 'bgr24',
            '-r', str(fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-an',
            '-movflags', '+faststart',
            str(output_path)
        ]

        if sys.platform == "win32":
            ctypes.windll.kernel32.SetDllDirectoryW(None)

        env = dict(os.environ)
        if getattr(sys, 'frozen', False):
            meipass = getattr(sys, '_MEIPASS', None)
            if meipass and 'PATH' in env:
                paths = env['PATH'].split(os.pathsep)
                clean_paths = [p for p in paths if meipass not in p]
                env['PATH'] = os.pathsep.join(clean_paths)

        print(f"[DEBUG] Starting cartoon FFmpeg pipe...")
        print(f"[DEBUG] Output path: {output_path}")
        print(f"[DEBUG] Output exists before: {Path(output_path).exists()}")

        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env=env
        )

        frame_count = 0
        batch_size = 30
        rest_time = 0.5
        temp_check_counter = 0

        try:
            while True:
                if self._cancelled:
                    break

                if frame_count % batch_size == 0 and frame_count > 0:
                    temp = self._get_cpu_temp()
                    temp_check_counter += 1
                    if temp > 65 or (temp == 0 and temp_check_counter % 3 == 0):
                        time.sleep(rest_time)

                ret, frame = cap.read()
                if not ret:
                    break

                if frame is None or frame.size == 0:
                    continue

                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
                    edges = cv2.Canny(blurred, settings['canny_low'], settings['canny_high'])

                    kernel = np.ones((2, 2), np.uint8)
                    edges = cv2.dilate(edges, kernel, iterations=1)
                    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

                    edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                    cartoon = cv2.addWeighted(frame, 1.0, edges_colored, settings['edge_opacity'], 0)

                    process.stdin.write(cartoon.tobytes())
                    frame_count += 1

                    if progress_callback and frame_count % 5 == 0:
                        progress = min(35 + (frame_count / total_frames) * 35, 70)
                        progress_callback(int(progress))

                except Exception as e:
                    print(f"[ERROR] Frame processing error at {frame_count}: {e}")
                    try:
                        process.stdin.write(frame.tobytes())
                        frame_count += 1
                    except:
                        pass
                    continue

        finally:
            print(f"[DEBUG] Processed {frame_count} frames, closing stdin...")
            cap.release()
            if process.stdin:
                process.stdin.close()

            stderr_data = process.stderr.read() if process.stderr else b''

            try:
                return_code = process.wait(timeout=60)
                print(f"[DEBUG] FFmpeg exit code: {return_code}")
                if stderr_data:
                    print(f"[DEBUG] FFmpeg stderr: {stderr_data.decode()[-500:]}")
                if return_code != 0:
                    raise RuntimeError(f"FFmpeg failed: {stderr_data.decode()[-500:]}")
            except subprocess.TimeoutExpired:
                process.kill()
                raise RuntimeError("FFmpeg encoding timed out")

            output_path = Path(output_path)
            if not output_path.exists():
                raise RuntimeError(f"FFmpeg reported success but output file missing: {output_path}")

            print(f"[DEBUG] Cartoon output verified: {output_path} ({output_path.stat().st_size} bytes)")

        return frame_count > 0

    def _apply_ffmpeg_filters(self, input_path, output_path, width, height):
        """Apply FFmpeg filters with logo overlay"""

        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Cartoon input not found: {input_path}")

        print(f"[DEBUG] Filter stage input: {input_path} ({input_path.stat().st_size} bytes)")

        settings = self.COPYRIGHT_AVOIDANCE
        speed = settings['speed']
        zoom = settings['zoom']

        pts_multiplier = 1.0 / speed

        filters = []
        filters.append(f'setpts={pts_multiplier:.3f}*PTS')

        # Color grade
        if self.filter_name in self.FILTER_PRESETS:
            filters.append(self.FILTER_PRESETS[self.filter_name]['ffmpeg'])

        # Mirror FIRST (flips coordinate system for bars)
        if self.mirror:
            filters.append('hflip')

        # Draw bars BEFORE zoom/crop - at original resolution
        # This way bars get cropped/zoomed along with the video
        if self.bars and len(self.bars) > 0:
            print(f"[DEBUG] Using {len(self.bars)} custom bar positions")
            for i, bar in enumerate(self.bars):
                x = int(bar['x'] * width)
                y = int(bar['y'] * height)
                w = int(bar['width'] * width)
                h = int(bar['height'] * height)
                
                # After hflip: flip coordinates so bars stay at same screen position
                if self.mirror:
                    x = width - x - w
                
                print(f"[DEBUG] Bar {i+1}: x={x}, y={y}, w={w}, h={h}")
                filters.append(f'drawbox={x}:{y}:{w}:{h}:black:fill')

        # Zoom/crop for copyright avoidance (bars get cropped/zoomed with video)
        crop_width = int(width / zoom)
        crop_height = int(height / zoom)
        crop_x = (width - crop_width) // 2
        crop_y = (height - crop_height) // 2
        filters.append(f'crop={crop_width}:{crop_height}:{crop_x}:{crop_y}')
        filters.append(f'scale={width}:{height}:force_original_aspect_ratio=decrease,setsar=1')
        # Ensure even dimensions for libx264
        filters.append('scale=trunc(iw/2)*2:trunc(ih/2)*2')

        filters.append('format=yuv420p')

        video_filter_str = ','.join(filters)

        # Thermal management
        temp = self._get_cpu_temp()
        if temp > 68:
            preset = 'slow'
            x264_opts = 'threads=4'
        else:
            preset = 'medium'
            x264_opts = ''

        cmd = [find_ffmpeg(), '-y']

        # Logo overlay
        if self.add_logo and self.LOGO_PATH.exists():
            cmd.extend(['-i', str(input_path), '-i', str(self.LOGO_PATH)])

            logo_x = self.LOGO_MARGIN
            logo_y = self.LOGO_MARGIN

            filter_complex = (
                f'[0:v]{video_filter_str}[main];'
                f'[1:v]scale={self.LOGO_SIZE}:{self.LOGO_SIZE}[logo];'
                f'[main][logo]overlay={logo_x}:{logo_y}:format=auto[final]'
            )
            cmd.extend(['-filter_complex', filter_complex, '-map', '[final]'])
        else:
            cmd.extend(['-i', str(input_path), '-vf', video_filter_str])

        cmd.extend([
            '-c:v', 'libx264',
            '-preset', preset,
            '-crf', '23',
            '-r', '30',
            '-pix_fmt', 'yuv420p'
        ])

        if x264_opts:
            cmd.extend(['-x264opts', x264_opts])

        cmd.extend(['-af', 'volume=0', '-c:a', 'aac', '-b:a', '128k'])
        cmd.append(str(output_path))

        creationflags = subprocess.BELOW_NORMAL_PRIORITY_CLASS if sys.platform == 'win32' else 0

        if sys.platform == "win32":
            ctypes.windll.kernel32.SetDllDirectoryW(None)

        env = dict(os.environ)
        if getattr(sys, 'frozen', False):
            meipass = getattr(sys, '_MEIPASS', None)
            if meipass and 'PATH' in env:
                paths = env['PATH'].split(os.pathsep)
                clean_paths = [p for p in paths if meipass not in p]
                env['PATH'] = os.pathsep.join(clean_paths)

        print(f"[DEBUG] Starting FFmpeg filter stage...")
        print(f"[DEBUG] Output path: {output_path}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env=env,
            creationflags=creationflags
        )

        try:
            stdout, stderr = process.communicate(timeout=600)
        except subprocess.TimeoutExpired:
            process.kill()
            raise RuntimeError("FFmpeg filter stage timed out")

        print(f"[DEBUG] FFmpeg exit code: {process.returncode}")
        if stderr:
            print(f"[DEBUG] FFmpeg stderr: {stderr.decode()[-1000:]}")

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode()[-500:]}")

        output_path = Path(output_path)
        if not output_path.exists():
            raise RuntimeError(f"FFmpeg reported success but output missing: {output_path}")

        print(f"[DEBUG] Filter output verified: {output_path} ({output_path.stat().st_size} bytes)")

    def run(self, progress_callback=None):
        """Full processing pipeline"""
        try:
            if progress_callback:
                progress_callback(5)

            if not check_disk_space(str(self.output_folder), required_gb=2.0):
                raise RuntimeError("Insufficient disk space")

            # Download
            if self.original_url:
                if progress_callback:
                    progress_callback(10)

                try:
                    if hasattr(self.downloader, 'download_1080p'):
                        input_video = self.downloader.download_1080p(self.original_url)
                    else:
                        raise AttributeError
                except (AttributeError, TypeError):
                    input_video = self.downloader.download(self.original_url, progress_callback)
            else:
                input_video = self.input_path

            if self._cancelled:
                return None

            # Get dimensions
            cap = cv2.VideoCapture(str(input_video))
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()

            print(f"[DEBUG] Input video: {input_video}")
            print(f"[DEBUG] Dimensions: {actual_width}x{actual_height}")
            print(f"[DEBUG] Output folder: {self.output_folder}")

            if progress_callback:
                progress_callback(35)

            # Cartoon stage
            cartoon_path = self.output_folder / "cartoon_temp.mp4"
            print(f"[DEBUG] Cartoon temp path: {cartoon_path}")

            success = self._apply_cartoon_opencv(input_video, cartoon_path, progress_callback)

            if not success or self._cancelled:
                return None

            if progress_callback:
                progress_callback(70)

            # Filter stage
            output_path = self._generate_output_path(input_video)
            print(f"[DEBUG] Final output path: {output_path}")

            self._apply_ffmpeg_filters(cartoon_path, output_path, actual_width, actual_height)

            if progress_callback:
                progress_callback(95)

            # Cleanup
            if cartoon_path.exists():
                cartoon_path.unlink()
                print(f"[DEBUG] Cleaned up temp file")

            if progress_callback:
                progress_callback(100)

            return str(output_path)

        except Exception as e:
            print(f"[ERROR] Processing error: {e}")
            raise
