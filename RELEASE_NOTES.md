# The Eye Test v1.0.1 - Release Notes

**Football Video Processor with Cinematic Effects**

---

## Download

**Windows:** `TheEyeTest_v1.0.1.zip`

Extract and run `TheEyeTest.exe` (or `START.bat`)

---

## v1.0.1 Changes

- **Fixed:** ffmpeg now correctly bundled with release - processing works out of the box
- App now checks its own folder for ffmpeg before system paths

---

## What's Included

```
TheEyeTest/
├── TheEyeTest.exe      # Main application
├── START.bat           # Simple launcher
├── ffmpeg.exe          # Video processing (bundled)
├── ffprobe.exe         # Video analysis
├── assets/
│   └── logo.jpg        # Your logo
├── config/
│   └── settings.json   # App settings
└── output/             # Processed videos go here
```

---

## Features

### Video Processing
- **Download** videos from YouTube (1080p support)
- **Cartoon effect** - Black edge outlines with temporal smoothing
- **Color filters** - WARM (vibrant) and COOL (muted)
- **Black bar overlay** - Hide scores and graphics
- **Mirror mode** - Horizontal flip

### Copyright Protection
- **12% speed increase** - Bypasses Content ID timing detection
- **8% zoom** - Crops edges, changes pixel positions
- **0.5° rotation** - Shifts all pixel coordinates
- **Subtle grain** - Disrupts visual fingerprinting

### Output
- **H.264 encoding** - Small file sizes
- **1080p resolution** - Full HD output
- **Clear naming** - `video_eyetest_warm.mp4` or `video_eyetest_cool.mp4`

---

## How to Use

1. **Load Video**
   - Paste YouTube URL → Click **LOAD PREVIEW**
   - Or click 📁 to browse local file

2. **Draw Black Bars**
   - Click & drag on video to hide scores
   - Right-click to undo
   - Max 5 bars

3. **Choose Filter**
   - **WARM** - Orange/yellow, vibrant
   - **COOL** - Blue/muted, cinematic

4. **Process**
   - Click **PROCESS VIDEO**
   - Output in `output/` folder

---

## Requirements

- **Windows 10/11**
- **No Python needed** - everything included

---

## Known Limitations

- Processing speed depends on video length (2-5 min per 5 min video)
- Some YouTube videos may fail if age-restricted or private
- Preview uses WMV format (Windows compatibility)

---

## Support

☕ **Ko-fi:** https://ko-fi.com/dariusstone

---

## License

MIT License - Free for personal and commercial use
