@echo off
echo ================================
echo GitHub Upload Script
echo ================================
echo.

REM Initialize git if needed
if not exist ".git" (
    echo [1/4] Initializing git repository...
    git init
    git branch -M main
) else (
    echo [1/4] Git already initialized.
)

REM Add all files
echo [2/4] Adding files...
git add .
git add -f release/TheEyeTest_v1.0.zip

REM Commit
echo [3/4] Committing...
git commit -m "Initial release v1.0.0"

echo.
echo ================================
echo NEXT STEPS (Manual):
echo ================================
echo.
echo 1. Go to https://github.com/new
echo 2. Create repository: the-eye-test
echo 3. Don't initialize with README
echo 4. Copy the repository URL
echo.
echo 5. Run these commands:
echo    git remote add origin https://github.com/YOUR_USERNAME/the-eye-test.git
echo    git push -u origin main
echo.
echo 6. Go to Releases ^> Draft new release
echo 7. Tag: v1.0.0
echo 8. Upload: release\TheEyeTest_v1.0.zip
echo.
pause
