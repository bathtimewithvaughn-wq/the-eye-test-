# THE EYE TEST - Development Plan (Updated)

**Based on Kimi's code review - 2026-02-20**

---

## 🎯 Project Overview

Desktop app for manually positioning black bars on football videos with cartoon filter processing.

**Location:** `D:\football-video-processor-app\`

---

## ✅ Technical Stack (Confirmed Working)

- Python 3.13.11
- PyQt5 5.15.11 (pip in conda base)
- opencv-python 4.13.0.92
- pillow 12.1.1
- yt-dlp 2026.2.4
- ffmpeg 7.1

---

## 🔧 Key Architecture Decisions

### 1. Preview → Final Workflow
- **Preview:** Download 480p for fast loading
- **Final:** Download 1080p when processing
- **Benefit:** Fast UI, low CPU during editing

### 2. Black Bar Coordinate System
Store as **normalized ratios** (0.0-1.0) not pixels:

```python
bar = {
    'x': click_x / preview_width,      # 0.0 to 1.0
    'y': click_y / preview_height,
    'width': drag_width / preview_width,
    'height': drag_height / preview_height
}

# Apply to 1080p:
x_final = bar['x'] * 1920
y_final = bar['y'] * 1080
width_final = bar['width'] * 1920
height_final = bar['height'] * 1080
```

**Why:** 480p coordinates don't map 1:1 to 1080p

### 3. Black Bar UI Component
Use **QRubberBand** instead of custom widgets:
- Built-in PyQt5
- Handles drag-to-draw automatically
- Less code to maintain

### 4. QMediaPlayer Backend Fix
Force Windows Media Foundation to avoid codec issues:

```python
import os
os.environ['QT_MULTIMEDIA_PREFERRED_PLUGINS'] = 'windowsmediafoundation'
```

---

## ⚠️ Risk Mitigations

### 1. yt-dlp Reliability
- YouTube frequently changes signatures
- **Fix:** Add retry logic (3 attempts)
- **Fix:** Allow local file import as fallback
- **Fix:** Warn users to update yt-dlp if downloads fail

### 2. QMediaPlayer Limitations
- DirectShow can be codec-finicky
- **Test:** Early with 480p/1080p files
- **Fallback:** Consider mpv or VLC bindings if needed

### 3. Processing Pipeline (Phase 4)
- 2 hours was optimistic
- **Revised:** 3-4 hours
- **Watch for:**
  - Color space handling (RGB vs YUV)
  - Audio sync during mirroring
  - Progress bar accuracy with ffmpeg subprocess

### 4. Missing Considerations Added
| Item | Implementation |
|------|---------------|
| Temp file cleanup | Delete 480p preview after final download |
| UI blocking | Show spinner during yt-dlp fetch |
| Storage check | Warn if < 2GB free before final download |
| Cancel handling | SIGTERM ffmpeg, clean up partial files |

---

## 📁 Updated File Structure

```
D:\football-video-processor-app\
├── main.py                     # Launch app + QMediaPlayer fix
├── requirements.txt            # No version pins (for yt-dlp)
├── gui/
│   ├── __init__.py
│   ├── main_window.py          # Main window layout
│   ├── video_widget.py         # Video preview player
│   ├── black_bar_editor.py     # QRubberBand overlay
│   └── controls.py             # Buttons, inputs
├── processor/
│   ├── __init__.py
│   ├── downloader.py           # yt-dlp with retry logic
│   ├── effects.py              # WARM/COOL filter functions
│   └── encoder.py              # ffmpeg with progress tracking
├── utils/
│   ├── __init__.py
│   ├── coordinates.py          # Normalized ratio conversion
│   └── storage.py              # Disk space checks
├── config/
│   └── settings.json           # Last used settings
├── assets/
│   └── logo.jpg                # Pixel art logo
└── temp/
    └── .gitkeep                # Temporary files (auto-cleaned)
```

---

## 🗓️ Revised Development Phases

### Phase 1: Foundation (3 hours)
- Create project structure
- Basic window with QMediaPlayer fix
- URL input + download preview (480p)
- **Add:** Retry logic for yt-dlp
- **Add:** Local file import option

### Phase 2: Black Bar Editor (2 hours)
- Use QRubberBand for drag-to-draw
- Store coordinates as normalized ratios
- Save/load positions
- Multiple bars support (max 10)

### Phase 3: Controls & Settings (2 hours)
- Trim time inputs
- Filter dropdown with preview
- Output folder chooser
- Settings persistence (JSON)
- **Add:** Storage space check

### Phase 4: Processing Pipeline (4 hours) ⬆️ *Increased from 2h*
- Integrate cartoon filter code
- Apply black bars at normalized coordinates
- Add logo overlay
- Mirror video
- ffmpeg encoding with progress
- **Handle:** Audio sync, color spaces
- **Add:** Cancel + cleanup on SIGTERM

### Phase 5: Polish (1 hour)
- Error handling (bad URL, download fails)
- Input validation
- Success/failure messages
- "Open output folder" button
- **Add:** Temp file cleanup

**Total Estimated Time:** 12 hours (up from 10h)

---

## 📋 Requirements.txt (No Version Pins)

```
PyQt5
opencv-python
pillow
yt-dlp
requests
```

**Why no pins:** yt-dlp needs frequent updates for YouTube changes

---

## ✅ Before Starting Checklist

- [x] Python 3.13.11 installed
- [x] PyQt5 installed and tested
- [x] opencv-python installed
- [x] pillow installed
- [x] yt-dlp installed
- [x] ffmpeg 7.1 available
- [x] Logo file ready (`assets/new_logo.jpg`)
- [ ] Project structure created
- [ ] First test video downloaded (TNT Champions League)

---

## 🎬 Next Step

Create `D:\football-video-processor-app\` folder structure and begin Phase 1.

**Ready to proceed?**
