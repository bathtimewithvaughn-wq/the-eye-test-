# The Eye Test - Project Summary

**Status:** COMPLETE ✅
**Version:** v1.3.1
**Date:** 2026-02-26

## Links
- **GitHub:** https://github.com/bathtimewithvaughn-wq/the-eye-test-
- **Latest Release:** https://github.com/bathtimewithvaughn-wq/the-eye-test-/releases/tag/v1.3.1
- **Download:** https://github.com/bathtimewithvaughn-wq/the-eye-test-/releases/download/v1.3.1/TheEyeTest.exe

## Features
- Draw black bars to cover overlays
- Mirror mode for copyright avoidance
- Warm/Cool color grades
- Auto logo overlay
- YouTube download support
- Cartoon effect with OpenCV

## Technical Details

### Build Command
```powershell
cd D:\the-eye-test-fix
py -3.11 -m PyInstaller --onefile --console --clean --name TheEyeTest --add-data 'assets;assets' --add-binary 'ffmpeg.exe;.' --add-binary 'ffprobe.exe;.' --add-data 'config;config' main.py
```

### Key Files
- `main.py` - Entry point
- `gui/main_window.py` - Main GUI
- `gui/black_bar_editor.py` - Bar drawing overlay
- `gui/video_widget.py` - Video preview widget
- `processor/encoder.py` - FFmpeg processing pipeline
- `processor/downloader.py` - YouTube download with yt-dlp

### Filter Chain (encoder.py)
```
1. setpts (speed 1.12x)
2. color grade (warm/cool)
3. hflip (mirror)
4. drawbox (black bars) ← BEFORE crop/scale
5. crop/scale (zoom 1.08x)
6. format (yuv420p)
```

### Known Issues (RESOLVED)
- ✅ Black bar positioning - fixed by storing normalized coords + filter chain reorder
- ✅ Logo not appearing - fixed by using sys._MEIPASS for PyInstaller path
- ✅ Rotation artifacts - removed rotation filter entirely
- ✅ Large file sizes - removed grain filter

### Copyright Avoidance
- Speed: 1.12x
- Mirror: horizontal flip
- Zoom: 1.08x with centered crop
- **Removed:** rotation (0.5° caused artifacts), grain (increased file size)

### Dependencies
- Python 3.11.9
- PyQt5
- OpenCV (cv2)
- yt-dlp
- FFmpeg (bundled)

## Development Notes

### Bar Coordinate System
- Bars stored as normalized coordinates (0.0-1.0) internally
- Converted to pixels in `paintEvent` for display
- Encoder scales to 1920x1080
- Mirror flips x-coordinate: `x = width - x - w`

### Preview vs Final
- Preview: 480p WMV (DirectShow compatible)
- Final: 1080p MP4
- Both use same normalized coordinates

### PyInstaller Path Issue
PyInstaller `--onefile` extracts assets to temp directory:
```python
# Wrong:
return Path(sys.executable).parent.resolve()

# Correct:
return Path(sys._MEIPASS).resolve()
```

## Future Improvements (if needed)
- Add more color grade presets
- Support vertical videos
- Batch processing
- Custom bar colors
- Preview at 1080p (if DirectShow codec available)
