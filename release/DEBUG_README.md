# The Eye Test v1.2.0 - Debug Version

## What's New in This Version

This is a **debug build** with enhanced logging to diagnose the 69% hang issue.

### Debug Features
- Full FFmpeg command logging
- Filter complex string logging
- Logo path validation
- Detailed error messages with stderr/stdout capture

### Testing Instructions

1. **Run the app normally**
   - Extract `TheEyeTest_v1.2.0_debug.zip`
   - Run `TheEyeTest.exe`
   - Process a video

2. **Watch for debug output**
   - The console will print `[DEBUG]` messages
   - If it hangs at 69%, look for the FFmpeg command
   - Copy the full command and any error messages

3. **Alternative: Test FFmpeg directly**
   - Run the app first to create `cartoon_temp.mp4`
   - Then run `test_ffmpeg.bat` to test the FFmpeg stage independently
   - This will show the exact error without running the full app

### Expected Debug Output

```
[DEBUG] Logo found at: assets/logo.jpg
[DEBUG] Filter complex: [0:v]setpts=0.893*PTS,...[main];[1:v]scale=100:100[logo];[main][logo]overlay=20:980:format=auto[final]
[DEBUG] FFmpeg command: ffmpeg -y -i cartoon_temp.mp4 -i assets/logo.jpg -filter_complex ...
```

If it fails:
```
[ERROR] FFmpeg failed with code 1
[ERROR] FFmpeg stderr: [actual error message]
[ERROR] FFmpeg stdout: [output]
```

### What to Report
If the app fails:
1. Screenshot the console output
2. Copy the FFmpeg command
3. Copy any error messages
4. Check if `cartoon_temp.mp4` exists in output folder

### Changes from v1.2.0
- Added debug logging (no functional changes)
- Added `test_ffmpeg.bat` for isolated testing

### Next Steps
Once we identify the error, we'll fix it and release v1.2.1.
