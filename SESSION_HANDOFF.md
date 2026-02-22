# The Eye Test - Final Settings

**Project:** Football video processor desktop app with PyQt5 GUI
**Location:** `D:\football-video-processor-app\`
**Last Updated:** 2026-02-22 01:15 GMT

---

## ✅ ALL FEATURES WORKING

- YouTube download (yt-dlp)
- Video preview (QMediaPlayer + WMV)
- Black bar drawing overlay
- Cartoon edge detection (OpenCV)
- Mirror (always on)
- Color filters (WARM/COOL)
- Logo overlay (bottom-left)
- H.264 encoding (smaller files)
- **Copyright avoidance (speed + grain)**

---

## 🔒 LOCKED SETTINGS

### Cartoon Effect (in `processor/encoder.py`):

```python
CARTOON_SETTINGS = {
    'blur_size': 7,           # Gaussian blur kernel
    'canny_low': 30,          # Edge detection low threshold
    'canny_high': 70,         # Edge detection high threshold
    'edge_opacity': 0.25,     # 25% opacity for visible but subtle lines
    'temporal_weight': 0.92,  # 92% current / 8% previous - tight, less flicker
}
```

### Color Filters (in `processor/encoder.py`):

```python
FILTER_PRESETS = {
    "WARM": {
        "description": "Warm tones, boosted saturation",
        "ffmpeg": "colorbalance=rm=0.12:bm=-0.12,eq=saturation=1.40:gamma=1.30"
    },
    "COOL": {
        "description": "Cool tones, reduced saturation", 
        "ffmpeg": "colorbalance=rm=-0.08:bm=0.08,eq=saturation=0.80:contrast=1.05"
    }
}
```

| Filter | Red | Blue | Saturation | Gamma/Contrast |
|--------|-----|------|------------|----------------|
| **WARM** | +12% | -12% | +40% | +30% gamma |
| **COOL** | -8% | +8% | -20% | +5% contrast |

### Copyright Avoidance (NEW):

```python
COPYRIGHT_AVOIDANCE = {
    'speed': 1.08,        # 8% faster - bypasses Content ID
    'grain_strength': 2,  # Subtle film grain (1-5 range)
}
```

**What it does:**
- **Speed 1.08x** - Video plays 8% faster (5:31 → ~5:07)
- **Film grain** - Adds subtle noise to break Content ID fingerprinting

### Logo Settings:

```python
LOGO_PATH = Path("assets/logo.jpg")
LOGO_SIZE = 100        # pixels height
LOGO_OPACITY = 0.8     # 80%
LOGO_MARGIN = 20       # pixels from edges
```

---

## 📊 FILE SIZE COMPARISON

| Codec | 5:31 Video (1080p) |
|-------|-------------------|
| Original YouTube (AV1) | 78 MB |
| **Output (H.264)** | 150-400 MB |

---

## 🎬 PROCESSING PIPELINE

1. **Download** 1080p from YouTube
2. **OpenCV cartoon** - Canny edges + temporal smoothing
3. **FFmpeg filters:**
   - Color filter (WARM/COOL)
   - Mirror (horizontal flip)
   - Black bars
   - **Film grain** (copyright avoidance)
   - **Speed change** (copyright avoidance)
   - Logo overlay
4. **H.264 encode** - Small file size

---

## 🚀 TO RUN

```powershell
cd D:\football-video-processor-app
python main.py
```

---

**Status:** ✅ Complete - Copyright avoidance enabled
