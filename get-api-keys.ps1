# Interactive API Key Setup Helper
# This script helps you get both required API keys quickly

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VibeDocs API Key Setup Helper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "I'll help you get the 2 required API keys quickly." -ForegroundColor White
Write-Host ""

# Check if keys already exist
$envPath = "backend\.env"
$envContent = ""
$githubTokenExists = $false
$anthropicKeyExists = $false

if (Test-Path $envPath) {
    $envContent = Get-Content $envPath -Raw

    if ($envContent -match "GITHUB_TOKEN=ghp_") {
        $githubTokenExists = $true
        Write-Host "[OK] GitHub token already configured!" -ForegroundColor Green
    }

    if ($envContent -match "ANTHROPIC_API_KEY=sk-ant-") {
        $anthropicKeyExists = $true
        Write-Host "[OK] Anthropic API key already configured!" -ForegroundColor Green
    }
}

Write-Host ""

# ============================================================
# GitHub Token
# ============================================================

if (-not $githubTokenExists) {
    Write-Host "============================================" -ForegroundColor Yellow
    Write-Host "  STEP 1: GitHub Personal Access Token" -ForegroundColor Yellow
    Write-Host "============================================" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "Opening GitHub token creation page in your browser..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2

    # Open GitHub tokens page
    Start-Process "https://github.com/settings/tokens/new?description=VibeDocs%20Automation&scopes=repo"

    Write-Host ""
    Write-Host "In your browser:" -ForegroundColor White
    Write-Host "  1. The form should be pre-filled:" -ForegroundColor Gray
    Write-Host "     - Description: VibeDocs Automation" -ForegroundColor Gray
    Write-Host "     - Scope: repo (already checked)" -ForegroundColor Gray
    Write-Host "  2. Set expiration (90 days recommended)" -ForegroundColor Gray
    Write-Host "  3. Click 'Generate token' at the bottom" -ForegroundColor Gray
    Write-Host "  4. Copy the token (starts with ghp_)" -ForegroundColor Gray
    Write-Host ""

    # Wait for user to get the token
    Write-Host "Paste your GitHub token here (it won't be visible): " -ForegroundColor Cyan -NoNewline
    $githubToken = Read-Host -AsSecureString
    $githubTokenPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($githubToken))

    # Validate token format
    if ($githubTokenPlain -match "^ghp_[a-zA-Z0-9]{36,}$") {
        Write-Host "[OK] Valid GitHub token format!" -ForegroundColor Green

        # Update .env file
        if (Test-Path $envPath) {
            $envContent = Get-Content $envPath -Raw
            $envContent = $envContent -replace "GITHUB_TOKEN=.*", "GITHUB_TOKEN=$githubTokenPlain"
            Set-Content -Path $envPath -Value $envContent -NoNewline
            Write-Host "[OK] GitHub token saved to backend\.env" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] backend\.env not found!" -ForegroundColor Red
        }
    } elseif ($githubTokenPlain -eq "") {
        Write-Host "[SKIP] No token entered" -ForegroundColor Yellow
    } else {
        Write-Host "[WARN] Token format looks incorrect (should start with ghp_)" -ForegroundColor Yellow
        Write-Host "       Saving anyway, but please verify it's correct" -ForegroundColor Yellow

        if (Test-Path $envPath) {
            $envContent = Get-Content $envPath -Raw
            $envContent = $envContent -replace "GITHUB_TOKEN=.*", "GITHUB_TOKEN=$githubTokenPlain"
            Set-Content -Path $envPath -Value $envContent -NoNewline
        }
    }

    Write-Host ""
} else {
    Write-Host "[SKIP] GitHub token already configured" -ForegroundColor Gray
    Write-Host ""
}

# ============================================================
# Anthropic API Key
# ============================================================

if (-not $anthropicKeyExists) {
    Write-Host "============================================" -ForegroundColor Yellow
    Write-Host "  STEP 2: Anthropic API Key" -ForegroundColor Yellow
    Write-Host "============================================" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "Opening Anthropic Console in your browser..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2

    # Open Anthropic console
    Start-Process "https://console.anthropic.com/settings/keys"

    Write-Host ""
    Write-Host "In your browser:" -ForegroundColor White
    Write-Host "  1. Sign in to Anthropic (or create account if needed)" -ForegroundColor Gray
    Write-Host "  2. Go to Settings > API Keys" -ForegroundColor Gray
    Write-Host "  3. Click 'Create Key'" -ForegroundColor Gray
    Write-Host "  4. Name it: VibeDocs Lazy-Bird" -ForegroundColor Gray
    Write-Host "  5. Copy the key (starts with sk-ant-)" -ForegroundColor Gray
    Write-Host ""

    Write-Host "Paste your Anthropic API key here (it won't be visible): " -ForegroundColor Cyan -NoNewline
    $anthropicKey = Read-Host -AsSecureString
    $anthropicKeyPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($anthropicKey))

    # Validate key format
    if ($anthropicKeyPlain -match "^sk-ant-") {
        Write-Host "[OK] Valid Anthropic API key format!" -ForegroundColor Green

        # Save to environment file for WSL2 setup
        $wslEnvFile = "$HOME\.vibedocs-anthropic-key"
        Set-Content -Path $wslEnvFile -Value $anthropicKeyPlain -NoNewline
        Write-Host "[OK] Anthropic key saved for WSL2 setup" -ForegroundColor Green

        # Also add to .env for future use
        if (Test-Path $envPath) {
            $envContent = Get-Content $envPath -Raw
            if ($envContent -match "ANTHROPIC_API_KEY=") {
                $envContent = $envContent -replace "ANTHROPIC_API_KEY=.*", "ANTHROPIC_API_KEY=$anthropicKeyPlain"
            } else {
                $envContent += "`n`n# Anthropic API (for Claude Code CLI)`nANTHROPIC_API_KEY=$anthropicKeyPlain"
            }
            Set-Content -Path $envPath -Value $envContent -NoNewline
        }
    } elseif ($anthropicKeyPlain -eq "") {
        Write-Host "[SKIP] No key entered" -ForegroundColor Yellow
    } else {
        Write-Host "[WARN] Key format looks incorrect (should start with sk-ant-)" -ForegroundColor Yellow
        Write-Host "       Saving anyway, but please verify it's correct" -ForegroundColor Yellow

        $wslEnvFile = "$HOME\.vibedocs-anthropic-key"
        Set-Content -Path $wslEnvFile -Value $anthropicKeyPlain -NoNewline
    }

    Write-Host ""
} else {
    Write-Host "[SKIP] Anthropic API key already configured" -ForegroundColor Gray
    Write-Host ""
}

# ============================================================
# Verification
# ============================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Re-check .env
$envContent = Get-Content $envPath -Raw

$allGood = $true

if ($envContent -match "GITHUB_TOKEN=ghp_") {
    Write-Host "[OK] GitHub token is set" -ForegroundColor Green
} else {
    Write-Host "[MISSING] GitHub token not set" -ForegroundColor Red
    $allGood = $false
}

$anthropicKeyFile = "$HOME\.vibedocs-anthropic-key"
if (Test-Path $anthropicKeyFile) {
    Write-Host "[OK] Anthropic key saved for WSL2 setup" -ForegroundColor Green
} else {
    Write-Host "[MISSING] Anthropic key not set" -ForegroundColor Yellow
    $allGood = $false
}

Write-Host ""

if ($allGood) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  SUCCESS! All API keys configured!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""

    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Run pre-flight check:" -ForegroundColor White
    Write-Host "   powershell -ExecutionPolicy Bypass -File preflight-check.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Test the pipeline:" -ForegroundColor White
    Write-Host "   cd backend" -ForegroundColor Gray
    Write-Host "   .\venv\Scripts\python.exe test_e2e_pipeline.py" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. For full automation, follow:" -ForegroundColor White
    Write-Host "   ACTION_CHECKLIST.md" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  Some keys are missing" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Run this script again to add missing keys," -ForegroundColor White
    Write-Host "or add them manually to backend\.env" -ForegroundColor White
    Write-Host ""
}

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
