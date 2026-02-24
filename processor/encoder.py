"""
Video encoder - processing pipeline with OpenCV cartoon effect + FFmpeg filters
"""

import subprocess
import os
import shutil
import sys
import time
import tempfile
import re
from pathlib import Path
from typing import Callable
import cv2
import numpy as np
import psutil

from processor.downloader import VideoDownloader
from utils.storage import check_disk_space, format_size

# Optional WMI for Windows temperature
try:
    import wmi
except ImportError:
    wmi = None


class VideoProcessor:
    """Process video with cartoon effect, black bars, filters, and effects"""
    
    CARTOON_SETTINGS = {
        'blur_size': 5,
        'canny_low': 40,      # Better edge detection
        'canny_high': 100,    # Middle ground for continuity
        'edge_opacity': 0.25,
    }
    
    FILTER_PRESETS = {
        "WARM": {
            "description": "Warm tones, boosted saturation",
            "ffmpeg": "colorbalance=rm=0.12:bm=-0.12,hue=s=1.30,format=yuv420p,lutyuv=y=val*1.30"
        },
        "COOL": {
            "description": "Cool tones, reduced saturation",
            "ffmpeg": "colorbalance=rm=-0.08:bm=0.08,hue=s=0.80,format=yuv420p,lutyuv=y=(val-128)*1.05+128"
        }
    }
    
    COPYRIGHT_AVOIDANCE = {
        'speed': 1.12,        # 12% faster = fewer frames = cooler
        'zoom': 1.08,
        'border': 10,
        'rotation': 0.5,
        'grain_strength': 8,
    }
    
    LOGO_PATH = Path("assets/logo.jpg")
    LOGO_SIZE = 100
    LOGO_MARGIN = 20
    
    def __init__(self, input_path, output_folder, bars, trim_seconds, filter_name, original_url=None, add_logo=True, mirror=False):
        self.input_path = input_path
        self.output_folder = Path(output_folder) if output_folder else Path("output")
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.bars = bars
        self.trim_seconds = trim_seconds
        self.filter_name = filter_name
        self.original_url = original_url
        self.add_logo = add_logo
        self.mirror = mirror
        self.downloader = VideoDownloader("temp")
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def _get_cpu_temp(self):
        """Get CPU temperature with WMI fallback for Windows"""
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
        """Apply cartoon effect using FFmpeg pipe (avoids VideoWriter crashes)"""
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
        
        # Handle trim_seconds - skip first N frames
        frames_to_skip = int(self.trim_seconds * fps) if self.trim_seconds > 0 else 0
        if frames_to_skip > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frames_to_skip)
            total_frames -= frames_to_skip
        
        settings = self.CARTOON_SETTINGS
        blur_size = settings['blur_size']
        if blur_size % 2 == 0:
            blur_size += 1
        
        # FFmpeg pipe for raw video input
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{width}x{height}',
            '-pix_fmt', 'bgr24',
            '-r', str(fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '18',
            '-pix_fmt', 'yuv420p',
            '-an',
            '-movflags', '+faststart',
            str(output_path)
        ]
        
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        
        frame_count = 0
        batch_size = 30
        rest_time = 0.5
        temp_check_counter = 0
        
        try:
            while True:
                if self._cancelled:
                    break
                
                # Thermal pacing: check every 30 frames, rest if no temp sensor
                if frame_count % batch_size == 0 and frame_count > 0:
                    temp = self._get_cpu_temp()
                    temp_check_counter += 1
                    # Rest if hot OR if we've processed 3 batches without temp data
                    if temp > 65 or (temp == 0 and temp_check_counter % 3 == 0):
                        time.sleep(rest_time)
                
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame is None or frame.size == 0:
                    continue
                
                try:
                    # Cartoon processing
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
                    edges = cv2.Canny(blurred, settings['canny_low'], settings['canny_high'])
                    
                    # Dilate then close to connect edge segments
                    kernel = np.ones((2, 2), np.uint8)
                    edges = cv2.dilate(edges, kernel, iterations=1)
                    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
                    
                    # Blend with original
                    edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                    cartoon = cv2.addWeighted(frame, 1.0, edges_colored, settings['edge_opacity'], 0)
                    
                    # Write to FFmpeg pipe
                    process.stdin.write(cartoon.tobytes())
                    frame_count += 1
                    
                    if progress_callback and frame_count % 5 == 0:
                        progress = min(35 + (frame_count / total_frames) * 35, 70)
                        progress_callback(int(progress))
                
                except Exception as e:
                    print(f"Frame processing error at {frame_count}: {e}")
                    try:
                        process.stdin.write(frame.tobytes())
                        frame_count += 1
                    except:
                        pass
                    continue
        
        finally:
            cap.release()
            if process.stdin:
                process.stdin.close()
            process.wait()
            
            if process.returncode != 0:
                stderr = process.stderr.read().decode() if process.stderr else "Unknown"
                raise RuntimeError(f"FFmpeg pipe failed: {stderr}")
        
        return frame_count > 0
    
    def _apply_ffmpeg_filters(self, input_path, output_path, width, height):
        """Apply FFmpeg filters with logo overlay, speed change, and muted audio"""
        settings = self.COPYRIGHT_AVOIDANCE
        speed = settings['speed']
        zoom = settings['zoom']
        rotation = settings['rotation']
        border = settings['border']
        
        # Calculate speed PTS multiplier (1.12x speed = 0.893 PTS multiplier)
        pts_multiplier = 1.0 / speed
        
        # Build video filter chain
        filters = []
        
        # 1. Speed change (setpts) - drops frames = less CPU work
        filters.append(f'setpts={pts_multiplier:.3f}*PTS')
        
        # 2. Color grading
        if self.filter_name in self.FILTER_PRESETS:
            filters.append(self.FILTER_PRESETS[self.filter_name]['ffmpeg'])
        
        # 3. Mirror (conditional)
        if self.mirror:
            filters.append('hflip')
        
        # 4. Black bars
        if self.bars:
            bar_height = int(height * 0.10)
            filters.append(f'pad={width}:{height + 2*bar_height}:0:{bar_height}:black')
            new_height = height + 2 * bar_height
        else:
            new_height = height
        
        # 5. Zoom and rotate
        crop_width = int(width / zoom)
        crop_height = int(new_height / zoom)
        crop_x = (width - crop_width) // 2
        crop_y = (new_height - crop_height) // 2
        filters.append(f'crop={crop_width}:{crop_height}:{crop_x}:{crop_y}')
        filters.append(f'scale={width}:{new_height}')
        filters.append(f'rotate={rotation}*PI/180:c=black')
        
        # 6. Border
        final_width = width + 2 * border
        final_height = new_height + 2 * border
        filters.append(f'pad={final_width}:{final_height}:{border}:{border}:black')
        
        # 7. Grain
        filters.append(f'noise=alls={settings["grain_strength"]}:allf=t+u')
        
        # 8. Format
        filters.append('format=yuv420p')
        
        video_filter_str = ','.join(filters)
        
        # Thermal management
        temp = self._get_cpu_temp()
        if temp > 68:
            preset = 'slow'
            x264_opts = 'frame-threads=1:sliced-threads=1'
        else:
            preset = 'medium'
            x264_opts = ''
        
        # Build command
        cmd = ['ffmpeg', '-y']
        
        # Logo overlay - bottom left
        if self.add_logo and self.LOGO_PATH.exists():
            cmd.extend(['-i', str(input_path), '-i', str(self.LOGO_PATH)])
            
            logo_x = self.LOGO_MARGIN
            logo_y = final_height - self.LOGO_SIZE - self.LOGO_MARGIN
            
            filter_complex = (
                f'[0:v]{video_filter_str}[main];'
                f'[1:v]scale={self.LOGO_SIZE}:{self.LOGO_SIZE}[logo];'
                f'[main][logo]overlay={logo_x}:{logo_y}:format=auto[final]'
            )
            cmd.extend(['-filter_complex', filter_complex, '-map', '[final]'])
        else:
            cmd.extend(['-i', str(input_path), '-vf', video_filter_str])
        
        # Video encoding
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', preset,
            '-crf', '23',
            '-r', '30',
            '-pix_fmt', 'yuv420p'
        ])
        
        if x264_opts:
            cmd.extend(['-x264opts', x264_opts])
        
        # Audio: MUTED
        cmd.extend(['-af', 'volume=0', '-c:a', 'aac', '-b:a', '128k'])
        
        cmd.append(str(output_path))
        
        creationflags = subprocess.BELOW_NORMAL_PRIORITY_CLASS if sys.platform == 'win32' else 0
        result = subprocess.run(cmd, capture_output=True, text=True, creationflags=creationflags)
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
    
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
            
            # Get actual dimensions
            cap = cv2.VideoCapture(str(input_video))
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            if progress_callback:
                progress_callback(35)
            
            cartoon_path = self.output_folder / "cartoon_temp.mp4"
            success = self._apply_cartoon_opencv(input_video, cartoon_path, progress_callback)
            
            if not success or self._cancelled:
                return None
            
            if progress_callback:
                progress_callback(70)
            
            output_path = self._generate_output_path(input_video)
            self._apply_ffmpeg_filters(cartoon_path, output_path, actual_width, actual_height)
            
            if progress_callback:
                progress_callback(95)
            
            if cartoon_path.exists():
                cartoon_path.unlink()
            
            if progress_callback:
                progress_callback(100)
            
            return str(output_path)
        
        except Exception as e:
            print(f"Processing error: {e}")
            raise
