# Install GitHub CLI to help with authentication
# This makes it easier to get a GitHub token

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installing GitHub CLI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if winget is available
$wingetAvailable = Get-Command winget -ErrorAction SilentlyContinue

if ($wingetAvailable) {
    Write-Host "Installing GitHub CLI via winget..." -ForegroundColor Cyan
    winget install --id GitHub.cli --silent

    Write-Host ""
    Write-Host "[OK] GitHub CLI installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Now you can authenticate:" -ForegroundColor Cyan
    Write-Host "  gh auth login" -ForegroundColor White
    Write-Host ""
    Write-Host "Then create a token:" -ForegroundColor Cyan
    Write-Host "  gh auth token" -ForegroundColor White
    Write-Host ""

} else {
    Write-Host "[INFO] winget not available, downloading installer..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install GitHub CLI manually:" -ForegroundColor White
    Write-Host "  https://cli.github.com/" -ForegroundColor Cyan
    Write-Host ""
    Start-Process "https://cli.github.com/"
}

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
