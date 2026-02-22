# Build and Release Checklist

## Build Steps (Windows)

### 1. Install PyInstaller
```powershell
pip install pyinstaller
```

### 2. Run Build Script
```powershell
cd D:\football-video-processor-app
build.bat
```

This will:
- Build `TheEyeTest.exe` with PyInstaller
- Copy assets and config
- Download ffmpeg
- Create `TheEyeTest_v1.0.zip` in `release/` folder

---

## GitHub Release Steps

### 1. Create Repository
- Go to https://github.com/new
- Name: `the-eye-test`
- Description: "Football Video Processor with Cinematic Effects"
- Public
- Don't initialize with README (we have one)

### 2. Push Code
```powershell
cd D:\football-video-processor-app
git init
git add .
git commit -m "Initial release v1.0.0"
git remote add origin https://github.com/YOUR_USERNAME/the-eye-test.git
git branch -M main
git push -u origin main
```

### 3. Create Release
- Go to repository → Releases → Draft new release
- Choose tag: `v1.0.0`
- Title: `The Eye Test v1.0.0`
- Copy content from `RELEASE_NOTES.md`
- Upload `release/TheEyeTest_v1.0.zip`
- Publish

---

## Files Ready

✅ README.md
✅ LICENSE (MIT)
✅ .gitignore
✅ build.spec (PyInstaller)
✅ build.bat (Windows build script)
✅ START.bat (Launcher)
✅ RELEASE_NOTES.md

---

## Need to Do

❌ Run `build.bat` on Windows
❌ Take screenshots (optional)
❌ Create GitHub repo
❌ Push code
❌ Upload release ZIP
