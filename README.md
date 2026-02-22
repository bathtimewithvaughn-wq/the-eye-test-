# The Eye Test

**Football Video Processor** - Apply cinematic effects to football highlights

---

## Features

✅ **Download videos** from YouTube (1080p)
✅ **Cartoon edge detection** - Black outline effect with temporal smoothing
✅ **Color filters** - WARM (vibrant orange) and COOL (muted blue)
✅ **Black bar overlay** - Hide scores and graphics
✅ **Copyright avoidance** - Speed change, zoom, rotation, grain
✅ **Mirror mode** - Horizontal flip
✅ **Logo watermark** - Your branding in corner
✅ **H.264 encoding** - Small file sizes

---

## Screenshots

![The Eye Test UI](screenshots/main_window.png)

---

## Download

**Windows:** Download `TheEyeTest_v1.0.zip` from [Releases](../../releases)

No Python needed - just extract and run `TheEyeTest.exe`

---

## How to Use

### 1. Load Video
- Paste a YouTube URL and click **LOAD PREVIEW**
- Or click 📁 to browse a local video file

### 2. Draw Black Bars
- Click and drag on the video to draw black bars over scores/logos
- Right-click to remove the last bar
- Maximum 5 bars

### 3. Choose Filter
- **WARM** - Vibrant orange/yellow tones, boosted saturation
- **COOL** - Muted blue tones, reduced saturation

### 4. Process
- Click **PROCESS VIDEO**
- Output saves to `output/` folder
- Filenames include filter: `video_eyetest_warm.mp4`

---

## Output Effects

| Effect | Description |
|--------|-------------|
| **Cartoon edges** | Black outlines around players/objects |
| **Color filter** | WARM or COOL color grading |
| **Mirror** | Horizontal flip |
| **Speed 12%** | Faster playback (copyright protection) |
| **Zoom 8%** | Crops edges (copyright protection) |
| **Rotation 0.5°** | Subtle rotation (copyright protection) |
| **Grain** | Subtle noise (copyright protection) |
| **Logo** | Watermark in bottom-left |

---

## Requirements (for source code)

- Python 3.10+
- PyQt5
- OpenCV
- ffmpeg

```bash
pip install -r requirements.txt
python main.py
```

---

## Building from Source

```bash
pip install pyinstaller
pyinstaller build.spec
```

Output: `dist/TheEyeTest.exe`

---

## License

MIT License - Free for personal and commercial use

---

## Credits

Created by **Darius Stone**

☕ [Support on Ko-fi](https://ko-fi.com/dariusstone)

---

## Changelog

### v1.0.0 (2026-02-22)
- Initial release
- Cartoon edge detection with temporal smoothing
- WARM and COOL color filters
- Copyright avoidance (speed, zoom, rotation, grain)
- Black bar overlay system
- Ko-fi support link
