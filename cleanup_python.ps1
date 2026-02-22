# Cleanup Python Packages Script
# Run this to free up space from unused Python packages

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Python Package Cleanup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# List large packages
Write-Host "[1/3] Checking for large packages..." -ForegroundColor Yellow

# Get site-packages size
$sitePackages = "$env:USERPROFILE\.local\lib\python3.10\site-packages"
if (Test-Path $sitePackages) {
    $size = (Get-ChildItem -Path $sitePackages -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host "Current size: $([math]::Round($size, 2)) GB" -ForegroundColor White
}

# Clear pip cache
Write-Host ""
Write-Host "[2/3] Clearing pip cache..." -ForegroundColor Yellow
pip cache purge 2>$null
Write-Host "Done." -ForegroundColor Green

# Remove unused packages
Write-Host ""
Write-Host "[3/3] Checking for packages to remove..." -ForegroundColor Yellow
Write-Host ""
Write-Host "WARNING: This will remove these packages:" -ForegroundColor Red
Write-Host "  - torch (PyTorch - ~2GB)" -ForegroundColor White
Write-Host "  - tensorflow (~1.5GB)" -ForegroundColor White
Write-Host "  - numpy, scipy, pandas (keep for this project)" -ForegroundColor White
Write-Host ""
$confirm = Read-Host "Remove PyTorch/TensorFlow? (y/N)"

if ($confirm -eq 'y') {
    Write-Host "Removing PyTorch..." -ForegroundColor Yellow
    pip uninstall -y torch torchvision torchaudio 2>$null
    
    Write-Host "Removing TensorFlow..." -ForegroundColor Yellow
    pip uninstall -y tensorflow tensorflow-gpu 2>$null
    
    Write-Host "Done!" -ForegroundColor Green
} else {
    Write-Host "Skipped." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "CLEANUP COMPLETE" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Show new size
if (Test-Path $sitePackages) {
    $newSize = (Get-ChildItem -Path $sitePackages -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host "New size: $([math]::Round($newSize, 2)) GB" -ForegroundColor Green
    Write-Host "Freed: $([math]::Round($size - $newSize, 2)) GB" -ForegroundColor Green
}

Write-Host ""
pause
