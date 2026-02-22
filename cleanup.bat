@echo off
echo ================================
echo Cleanup Script
echo ================================
echo.

REM Delete backup folder
echo [1/6] Deleting backup folder...
rmdir /S /Q "..\football-video-processor-app-backup" 2>nul
echo Done.

REM Delete temp files
echo [2/6] Deleting temp files...
rmdir /S /Q "temp" 2>nul
mkdir temp
echo Done.

REM Delete build artifacts
echo [3/6] Deleting build artifacts...
rmdir /S /Q "build" 2>nul
rmdir /S /Q "dist" 2>nul
del /Q "*.pyc" 2>nul
for /d /r %%i in (__pycache__) do @rmdir /S /Q "%%i" 2>nul
echo Done.

REM Delete Python cache
echo [4/6] Clearing pip cache...
pip cache purge 2>nul
echo Done.

REM Delete test files
echo [5/6] Deleting test files...
del /Q "test_*.py" 2>nul
del /Q "generate_*.py" 2>nul
del /Q "*.backup" 2>nul
del /Q "*.bak" 2>nul
echo Done.

REM Keep release folder
echo [6/6] Keeping release folder for GitHub upload.
echo.

echo ================================
echo CLEANUP COMPLETE!
echo ================================
echo.
echo Ready to upload:
echo   release\TheEyeTest_v1.0.zip
echo.
pause
