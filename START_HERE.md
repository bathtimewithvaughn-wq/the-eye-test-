# NEW SESSION START - Copy This Message

---

**Paste this at the start of the new session:**

```
We are building "The Eye Test" - a desktop GUI app for processing football videos with black bars and cartoon filters.

PROJECT LOCATION: D:\football-video-processor-app\

WHAT IT DOES:
1. Download YouTube video (480p preview, 1080p final)
2. User clicks/drags to position black bars on video
3. User sets trim time (skip first N seconds)
4. User selects filter (WARM or COOL)
5. Processes and exports 1080p video with settings applied

TECH STACK (all installed and working):
- Python 3.13.11 (Windows, conda base)
- PyQt5 5.15.11
- opencv-python 4.13.0.92
- pillow 12.1.1
- yt-dlp 2026.2.4
- ffmpeg 7.1

TESTED: D:\pyqt5_test.py works - PyQt5 confirmed

LOGO: Copy from D:\football-video-processor\assets\new_logo.jpg

FILTERS LOCKED IN:
- WARM: +10B/-10R color shift, +20% sat, +20% gamma
- COOL: -10B/+10R color shift, -10% sat, +15% contrast

NEXT STEPS:
1. Read the plan: D:\football-video-processor-app\PLAN.md
2. Create project folder structure
3. Start Phase 1: Basic GUI with video preview

IMPORTANT:
- Store black bar coordinates as normalized ratios (0.0-1.0), not pixels
- Use QRubberBand for black bar UI
- Add os.environ['QT_MULTIMEDIA_PREFERRED_PLUGINS'] = 'windowsmediafoundation' for QMediaPlayer
- Add retry logic for yt-dlp downloads

Start by reading the full plan, then create the project structure.
```
