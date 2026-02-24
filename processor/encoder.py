"""
Video encoder - processing pipeline with OpenCV cartoon effect + FFmpeg filters
"""

import subprocess
import os
import shutil
from pathlib import Path
from typing import Callable
import re
import cv2
import numpy as np

from processor.downloader import VideoDownloader
from utils.storage import check_disk_space, format_size


class VideoProcessor:
    """Process video with cartoon effect, black bars, filters, and effects"""
    
    # Cartoon effect settings (optimized for speed - ~3x processing)
    CARTOON_SETTINGS = {
        'blur_size': 5,           # Reduced from 7 for ~10% speed gain
        'canny_low': 30,
        'canny_high': 70,
        'edge_opacity': 0.25,
        'temporal_weight': 1.0,   # 100% current frame (no temporal smoothing) - ~30% speed gain
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
    
    # Copyright avoidance settings (applied to all outputs)
    COPYRIGHT_AVOIDANCE = {
        'speed': 1.12,        # 12% faster - effective against Content ID
        'zoom': 1.08,         # 8% zoom in - crops edges
        'border': 10,         # 10px black border around video
        'rotation': 0.5,      # 0.5 degree rotation - shifts all pixels
        'grain_strength': 8,  # Subtle grain (added in OpenCV)
    }
    
    # Logo settings
    LOGO_PATH = Path("assets/logo.jpg")
    LOGO_SIZE = 100  # pixels height
    LOGO_OPACITY = 0.8
    LOGO_MARGIN = 20  # pixels from edge
    
    def __init__(
        self,
        input_path: str,
        output_folder: str,
        bars: list,
        trim_seconds: int,
        filter_name: str,
        original_url: str = None,
        add_logo: bool = True,
        mirror: bool = False
    ):
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
        """Cancel processing"""
        self._cancelled = True
    
    def run(self, progress_callback: Callable[[int], None] = None) -> str | None:
        """
        Run the full processing pipeline.
        
        Pipeline:
        1. Download 1080p if needed
        2. OpenCV: Apply cartoon edge detection (preserves color)
        3. FFmpeg: Apply color filter, mirror, black bars
        
        Args:
            progress_callback: Function to call with progress percentage (0-100)
            
        Returns:
            Output file path, or None if failed
        """
        try:
            # Step 1: Check disk space (5%)
            if progress_callback:
                progress_callback(5)
            
            has_space, available = check_disk_space(str(self.output_folder), 2.0)
            if not has_space:
                raise Exception(f"Insufficient disk space. Need 2GB, have {format_size(available * 1024**3)}")
            
            # Step 2: Download 1080p if URL was provided (10-35%)
            if self.original_url and self._is_youtube_url(self.original_url):
                if progress_callback:
                    progress_callback(10)
                
                self.input_path = self.downloader.download_1080p(self.original_url)
                
                if not self.input_path:
                    raise Exception("Failed to download 1080p version")
                
                if progress_callback:
                    progress_callback(35)
            else:
                if progress_callback:
                    progress_callback(25)
            
            if self._cancelled:
                return None
            
            # Get video dimensions
            video_width, video_height = self._get_video_dimensions()
            
            # Generate output filename
            output_path = self._generate_output_path()
            
            # Step 3: OpenCV cartoon effect (35-70%)
            temp_cartoon = output_path.replace('.mp4', '_cartoon_temp.mp4')
            
            if progress_callback:
                progress_callback(40)
                print(f"[DEBUG] Applying OpenCV cartoon effect...")
            
            success = self._apply_cartoon_opencv(
                self.input_path, 
                temp_cartoon,
                lambda pct: progress_callback(40 + int(pct * 0.3)) if progress_callback else None
            )
            
            if not success or self._cancelled:
                if os.path.exists(temp_cartoon):
                    os.unlink(temp_cartoon)
                return None
            
            # Step 4: FFmpeg filters (70-95%)
            if progress_callback:
                progress_callback(70)
                print(f"[DEBUG] Applying FFmpeg filters...")
            
            success = self._apply_ffmpeg_filters(temp_cartoon, output_path, video_width, video_height)
            
            # Cleanup temp cartoon file
            if os.path.exists(temp_cartoon):
                os.unlink(temp_cartoon)
            
            if self._cancelled:
                if output_path and os.path.exists(output_path):
                    os.unlink(output_path)
                return None
            
            if not success:
                raise Exception("FFmpeg processing failed")
            
            # Step 5: Cleanup (95-100%)
            if progress_callback:
                progress_callback(95)
            
            # Clean up preview files (keep output)
            self.downloader.cleanup_preview()
            
            if progress_callback:
                progress_callback(100)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Processing error: {str(e)}")
    
    def _apply_cartoon_opencv(self, input_path: str, output_path: str, progress_callback=None) -> bool:
        """
        Apply cartoon edge detection using OpenCV.
        Processes at 720p for CPU efficiency, FFmpeg upscales to 1080p.
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            print(f"[ERROR] Cannot open video: {input_path}")
            return False
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Process at 720p for lower CPU load, FFmpeg will upscale
        process_height = 720
        process_width = int(width * (process_height / height))
        
        # Apply trim if specified
        skip_frames = int(fps * self.trim_seconds)
        if skip_frames > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, skip_frames)
            frames_to_process = total_frames - skip_frames
        else:
            frames_to_process = total_frames
        
        # Setup video writer at 720p
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (process_width, process_height))
        
        if not out.isOpened():
            print(f"[ERROR] Cannot create output: {output_path}")
            cap.release()
            return False
        
        # Settings from working script
        blur_size = self.CARTOON_SETTINGS['blur_size']
        canny_low = self.CARTOON_SETTINGS['canny_low']
        canny_high = self.CARTOON_SETTINGS['canny_high']
        edge_opacity = self.CARTOON_SETTINGS['edge_opacity']
        temporal_weight = self.CARTOON_SETTINGS['temporal_weight']
        
        prev_edges = None
        frame_count = 0
        
        print(f"[DEBUG] OpenCV cartoon: {process_width}x{process_height} (from {width}x{height}), {frames_to_process} frames")
        
        while frame_count < frames_to_process:
            if self._cancelled:
                cap.release()
                out.release()
                return False
            
            ret, frame = cap.read()
            if not ret:
                break
            
            # Downscale to 720p for processing
            frame_small = cv2.resize(frame, (process_width, process_height), interpolation=cv2.INTER_AREA)
            
            # Convert to grayscale for edge detection
            gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
            
            # Blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
            
            # Canny edge detection
            edges = cv2.Canny(blurred, canny_low, canny_high)
            
            # Dilate to thicken edges
            edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
            
            # Temporal smoothing (85% current, 15% previous)
            if prev_edges is not None:
                edges = cv2.addWeighted(edges, temporal_weight, prev_edges, 1 - temporal_weight, 0)
            
            # Morphological closing to connect gaps
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
            prev_edges = edges.copy()
            
            # Convert edges to 3-channel for blending
            edge_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            
            # KEY: addWeighted preserves original frame color, adds edges at opacity
            cartoon_frame = cv2.addWeighted(frame_small, 1.0, edge_colored, edge_opacity, 0)
            
            # Grain moved to FFmpeg for speed (was slow in Python)
            
            out.write(cartoon_frame)
            frame_count += 1
            
            if progress_callback and frame_count % 30 == 0:
                progress_callback(frame_count / frames_to_process * 100)
            
            if frame_count % 500 == 0:
                print(f"[DEBUG] OpenCV processed {frame_count}/{frames_to_process} frames")
        
        cap.release()
        out.release()
        
        print(f"[DEBUG] OpenCV complete: {frame_count} frames at 720p")
        return True
    
    def _apply_ffmpeg_filters(self, input_path: str, output_path: str, width: int, height: int) -> bool:
        """Apply FFmpeg filters: color correction, mirror, black bars, logo, copyright avoidance."""
        
        ffmpeg_path = self._find_ffmpeg()
        if not ffmpeg_path:
            raise Exception("ffmpeg not found")
        
        # Build filter chain for -vf (simple filters)
        filters = []
        
        # Color filter
        if self.filter_name in self.FILTER_PRESETS:
            filters.append(self.FILTER_PRESETS[self.filter_name]["ffmpeg"])
        
        # Mirror (horizontal flip) - always on
        filters.append("hflip")
        
        # Black bars (after flip, so coordinates are mirrored)
        for bar in self.bars:
            x = int((1 - bar['x'] - bar['width']) * width)
            y = int(bar['y'] * height)
            w = int(bar['width'] * width)
            h = int(bar['height'] * height)
            
            # Clamp values
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            w = max(1, min(w, width - x))
            h = max(1, min(h, height - y))
            
            filters.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color=black:t=fill")
        
        # Copyright avoidance: Zoom (crop edges)
        zoom = self.COPYRIGHT_AVOIDANCE['zoom']
        if zoom > 1.0:
            crop_w = int(width / zoom)
            crop_h = int(height / zoom)
            crop_x = (width - crop_w) // 2
            crop_y = (height - crop_h) // 2
            filters.append(f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale={width}:{height}")
        
        # Copyright avoidance: Rotation (subtle, shifts all pixels)
        rotation = self.COPYRIGHT_AVOIDANCE['rotation']
        if rotation != 0:
            # Rotate then crop to remove black corners, then scale back
            # Use bilinear interpolation for smoothness
            filters.append(f"rotate={rotation}*PI/180:bilinear=1:fillcolor=black")
            # Crop edges where rotation created black borders
            rot_crop = int(max(width, height) * 0.02)  # 2% crop
            filters.append(f"crop={width-2*rot_crop}:{height-2*rot_crop}:{rot_crop}:{rot_crop},scale={width}:{height}")
        
        # Copyright avoidance: Border (black border around video)
        border = self.COPYRIGHT_AVOIDANCE['border']
        if border > 0:
            # Add black border, then crop back to original size (shifts content)
            filters.append(f"pad={width+2*border}:{height+2*border}:{border}:{border}:black,crop={width}:{height}:{border}:{border}")
        
        # Copyright avoidance: Grain (moved from OpenCV for speed)
        grain_strength = self.COPYRIGHT_AVOIDANCE['grain_strength']
        if grain_strength > 0:
            filters.append(f"noise=alls={grain_strength}:allf=t")
        
        # Upscale from 720p back to original resolution
        filters.append(f"scale={width}:{height}:flags=lanczos")
        
        # Speed change is handled via setpts in filter
        speed = self.COPYRIGHT_AVOIDANCE['speed']
        setpts_val = 1.0 / speed  # e.g., 1/1.12 = 0.893
        
        filter_str = ",".join(filters) if filters else "copy"
        filter_str = f"setpts={setpts_val:.3f}*PTS,{filter_str}"
        
        print(f"[DEBUG] FFmpeg filter: {filter_str}")
        print(f"[DEBUG] Copyright avoidance: speed={speed}x, zoom={zoom}x, rotation={rotation}°, border={border}px, grain={grain_strength}")
        
        # Check if logo exists
        logo_path = self.LOGO_PATH
        has_logo = logo_path.exists() and self.add_logo
        
        # Check if libx264 is available for H.264 encoding (smaller files)
        has_h264 = self._check_codec_available(ffmpeg_path, 'libx264')
        video_codec = 'libx264' if has_h264 else 'mpeg4'
        video_args = ['-crf', '23', '-preset', 'fast'] if has_h264 else ['-q:v', '3']
        
        print(f"[DEBUG] Using video codec: {video_codec}")
        
        if has_logo:
            # Use filter_complex for logo overlay
            # Logo goes in bottom-left corner
            logo_w = self.LOGO_SIZE
            logo_x = self.LOGO_MARGIN
            logo_y = height - self.LOGO_SIZE - self.LOGO_MARGIN
            
            filter_complex = f"[0:v]{filter_str}[video];[1:v]scale={logo_w}:-1[logo];[video][logo]overlay={logo_x}:{logo_y}"
            
            cmd = [
                ffmpeg_path, '-y',
                '-i', input_path,
                '-i', str(logo_path),
                '-filter_complex', filter_complex,
                '-c:v', video_codec,
                *video_args,
                '-c:a', 'aac',
                '-b:a', '128k',
                '-af', 'volume=0',
                '-movflags', '+faststart',
                output_path
            ]
        else:
            # No logo, use simple -vf
            cmd = [
                ffmpeg_path, '-y',
                '-i', input_path,
                '-vf', filter_str,
                '-c:v', video_codec,
                *video_args,
                '-c:a', 'aac',
                '-b:a', '128k',
                '-af', 'volume=0',
                '-movflags', '+faststart',
                output_path
            ]
        
        try:
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Hide console window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',
                errors='ignore',
                env=env,
                startupinfo=startupinfo
            )
            
            error_log = []
            for line in process.stderr:
                if self._cancelled:
                    process.terminate()
                    return False
                error_log.append(line.strip())
                if len(error_log) > 20:
                    error_log.pop(0)
            
            process.wait()
            
            if process.returncode == 0 and os.path.exists(output_path):
                return True
            else:
                err_text = " | ".join(error_log[-5:])
                print(f"[ERROR] FFmpeg failed: {err_text}")
                return False
                
        except subprocess.SubprocessError as e:
            print(f"[ERROR] FFmpeg error: {str(e)}")
            return False
    
    def _generate_output_path(self) -> str:
        """Generate output file path with filter name."""
        input_name = Path(self.input_path).stem
        input_name = re.sub(r'[^\w\s-]', '', input_name).strip()[:50]
        # Include filter name in output filename for clarity
        filter_suffix = f"_{self.filter_name.lower()}" if self.filter_name else ""
        output_name = f"{input_name}_eyetest{filter_suffix}.mp4"
        return str(self.output_folder / output_name)
    
    def _get_video_dimensions(self) -> tuple:
        """Get video width and height using OpenCV."""
        cap = cv2.VideoCapture(self.input_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return width, height
    
    def _is_youtube_url(self, url: str) -> bool:
        """Check if URL is a YouTube link"""
        return "youtube.com" in url or "youtu.be" in url
    
    def _find_ffmpeg(self) -> str | None:
        """Find ffmpeg executable"""
        # First check system PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path

        # Check app's own directory (for packaged releases)
        app_dir = Path(__file__).parent.parent  # Go up from processor/ to app root
        app_ffmpeg = app_dir / "ffmpeg.exe"
        if app_ffmpeg.exists():
            return str(app_ffmpeg)

        # Check common system paths
        common_paths = [
            os.path.expandvars(r"%USERPROFILE%\miniconda3\Library\bin\ffmpeg.exe"),
            os.path.expandvars(r"%USERPROFILE%\anaconda3\Library\bin\ffmpeg.exe"),
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        ]

        for p in common_paths:
            if os.path.exists(p):
                return p

        return None
    
    def _check_codec_available(self, ffmpeg_path: str, codec: str) -> bool:
        """Check if a codec is available in ffmpeg"""
        try:
            result = subprocess.run(
                [ffmpeg_path, '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return codec in result.stdout
        except:
            return False
    
    def cleanup(self):
        """Clean up resources."""
        pass
