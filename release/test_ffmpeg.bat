@echo off
REM Test script for The Eye Test FFmpeg stage
REM Run this from the release folder to test FFmpeg manually

echo Testing FFmpeg stage...
echo.

set INPUT=TheEyeTest\output\cartoon_temp.mp4
set LOGO=TheEyeTest\assets\logo.jpg
set OUTPUT=test_output.mp4

if not exist "%INPUT%" (
    echo ERROR: cartoon_temp.mp4 not found
    echo Run the app first to create cartoon_temp.mp4
    pause
    exit /b 1
)

if not exist "%LOGO%" (
    echo ERROR: logo.jpg not found
    pause
    exit /b 1
)

echo Input: %INPUT%
echo Logo: %LOGO%
echo Output: %OUTPUT%
echo.
echo Running FFmpeg command...
echo.

TheEyeTest\ffmpeg.exe -y -i "%INPUT%" -i "%LOGO%" -filter_complex "[0:v]setpts=0.893*PTS,colorbalance=rm=0.12:bm=-0.12,hue=s=1.30,format=yuv420p,lutyuv=y=val*1.30[main];[1:v]scale=100:100[logo];[main][logo]overlay=20:980:format=auto[final]" -map "[final]" -c:v libx264 -preset slow -crf 23 -r 30 -pix_fmt yuv420p -x264opts frame-threads=1:sliced-threads=1 -af volume=0 -c:a aac -b:a 128k "%OUTPUT%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS! Output created: %OUTPUT%
    echo File size:
    dir "%OUTPUT%" | find "%OUTPUT%"
) else (
    echo.
    echo FAILED with error code %ERRORLEVEL%
    echo Check the error message above
)

pause
