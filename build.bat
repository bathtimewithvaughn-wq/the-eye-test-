@echo off
echo ================================
echo The Eye Test - Build Script
echo ================================
echo.

REM Create build directory
if not exist "release" mkdir release
if not exist "release\TheEyeTest" mkdir release\TheEyeTest

REM Build executable with PyInstaller
echo [1/4] Building executable...
pyinstaller --clean build.spec
if errorlevel 1 (
    echo ERROR: PyInstaller failed
    pause
    exit /b 1
)

REM Copy executable
echo [2/4] Copying executable...
copy dist\TheEyeTest.exe release\TheEyeTest\

REM Copy assets
echo [3/4] Copying assets...
xcopy /E /I assets release\TheEyeTest\assets
xcopy /E /I config release\TheEyeTest\config

REM Create output folder
if not exist "release\TheEyeTest\output" mkdir release\TheEyeTest\output

REM Download ffmpeg if not present
echo [4/4] Checking ffmpeg...
if not exist "release\TheEyeTest\ffmpeg.exe" (
    echo Downloading ffmpeg...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'ffmpeg.zip'}"
    powershell -Command "& {Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'ffmpeg_temp' -Force}"
    copy ffmpeg_temp\ffmpeg-*-essentials_build\bin\ffmpeg.exe release\TheEyeTest\
    copy ffmpeg_temp\ffmpeg-*-essentials_build\bin\ffprobe.exe release\TheEyeTest\
    rmdir /S /Q ffmpeg_temp
    del ffmpeg.zip
)

REM Create ZIP
echo.
echo Creating ZIP archive...
cd release
powershell -Command "& {Compress-Archive -Path 'TheEyeTest' -DestinationPath 'TheEyeTest_v1.0.zip' -Force}"
cd ..

echo.
echo ================================
echo BUILD COMPLETE!
echo ================================
echo.
echo Output: release\TheEyeTest_v1.0.zip
echo.
pause
