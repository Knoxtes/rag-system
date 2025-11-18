# Copy 7MM Logo Files
# Run this script after saving the logo images to the rag-system directory

Write-Host "7MM Logo File Copy Script" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host ""

$ragSystemPath = "c:\Users\Notxe\Desktop\rag-system"
$publicPath = "c:\Users\Notxe\Desktop\rag-system\chat-app\public"

# Check if source files exist
$colorLogoSource = Join-Path $ragSystemPath "image.png"
$whiteLogoSource = Join-Path $ragSystemPath "image (1).png"

Write-Host "Checking for logo files..." -ForegroundColor Yellow

if (Test-Path $colorLogoSource) {
    Write-Host "✓ Found color logo: image.png" -ForegroundColor Green
    Copy-Item $colorLogoSource "$publicPath\7mm-logo-color.png" -Force
    Write-Host "  Copied to: 7mm-logo-color.png" -ForegroundColor Cyan
} else {
    Write-Host "✗ Color logo not found: image.png" -ForegroundColor Red
    Write-Host "  Please save the color 7MM logo as 'image.png' in:" -ForegroundColor Yellow
    Write-Host "  $ragSystemPath" -ForegroundColor Yellow
}

Write-Host ""

if (Test-Path $whiteLogoSource) {
    Write-Host "✓ Found white logo: image (1).png" -ForegroundColor Green
    Copy-Item $whiteLogoSource "$publicPath\7mm-logo-white.png" -Force
    Write-Host "  Copied to: 7mm-logo-white.png" -ForegroundColor Cyan
} else {
    Write-Host "✗ White logo not found: image (1).png" -ForegroundColor Red
    Write-Host "  Please save the white 7MM logo as 'image (1).png' in:" -ForegroundColor Yellow
    Write-Host "  $ragSystemPath" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Save the logo files if you haven't already" -ForegroundColor White
Write-Host "2. Run this script again to copy them" -ForegroundColor White
Write-Host "3. Rebuild the React app: cd chat-app; npm run build" -ForegroundColor White
Write-Host "4. Start the system: python start_chat_system.py" -ForegroundColor White
Write-Host ""
