# VibeDocs Pre-Flight Check
# Verifies Windows environment is ready for full automation
# Run this before starting the WSL2 setup

Write-Host "========================================"
Write-Host "VibeDocs Pre-Flight Check"
Write-Host "========================================"
Write-Host ""

$allGood = $true

# Function to print results
function Test-Requirement {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Message
    )

    if ($Passed) {
        Write-Host "[OK] $Name" -ForegroundColor Green
        if ($Message) { Write-Host "     $Message" -ForegroundColor Gray }
    } else {
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        if ($Message) { Write-Host "     $Message" -ForegroundColor Yellow }
        $script:allGood = $false
    }
}

function Test-Warning {
    param(
        [string]$Name,
        [string]$Message
    )
    Write-Host "[WARN] $Name" -ForegroundColor Yellow
    if ($Message) { Write-Host "     $Message" -ForegroundColor Gray }
}

Write-Host "Checking Windows Environment..." -ForegroundColor Cyan
Write-Host ""

# Check WSL2
Write-Host "1. WSL2 Status"
try {
    $wslStatus = wsl --status 2>&1 | Out-String
    if ($wslStatus -match "Ubuntu") {
        Test-Requirement "WSL2 with Ubuntu installed" $true "Default: Ubuntu, Version: 2"
    } else {
        Test-Requirement "WSL2 with Ubuntu installed" $false "WSL2 found but Ubuntu not set as default"
    }
} catch {
    Test-Requirement "WSL2 installed" $false "Run: wsl --install"
}
Write-Host ""

# Check Node.js
Write-Host "2. Node.js (Windows)"
try {
    $nodeVersion = node --version
    if ($nodeVersion -match "v(\d+)") {
        $major = [int]$matches[1]
        if ($major -ge 16) {
            Test-Requirement "Node.js installed" $true "Version: $nodeVersion"
        } else {
            Test-Requirement "Node.js >= 16" $false "Current: $nodeVersion, need 16+"
        }
    }
} catch {
    Test-Requirement "Node.js installed" $false "Download from: https://nodejs.org/"
}
Write-Host ""

# Check Python virtual environment
Write-Host "3. Python Virtual Environment"
$venvPath = "backend\venv\Scripts\python.exe"
if (Test-Path $venvPath) {
    try {
        $pythonVersion = & $venvPath --version 2>&1
        Test-Requirement "Python venv exists" $true "$pythonVersion"
    } catch {
        Test-Requirement "Python venv functional" $false "Venv exists but python not working"
    }
} else {
    Test-Requirement "Python venv exists" $false "Run: cd backend && python -m venv venv"
}
Write-Host ""

# Check backend dependencies
Write-Host "4. Backend Dependencies"
if (Test-Path $venvPath) {
    try {
        $packages = & $venvPath -m pip list 2>&1 | Out-String

        $requiredPackages = @("fastapi", "sqlalchemy", "alembic", "httpx", "pydantic")
        $allInstalled = $true

        foreach ($pkg in $requiredPackages) {
            if ($packages -match $pkg) {
                Write-Host "     [OK] $pkg installed" -ForegroundColor Gray
            } else {
                Write-Host "     [MISSING] $pkg" -ForegroundColor Yellow
                $allInstalled = $false
            }
        }

        Test-Requirement "Backend dependencies installed" $allInstalled $(if (-not $allInstalled) { "Run: cd backend && venv\Scripts\pip install -r requirements.txt" })
    } catch {
        Test-Requirement "Backend dependencies" $false "Could not check pip packages"
    }
} else {
    Test-Warning "Backend dependencies" "Skipped - venv not found"
}
Write-Host ""

# Check database migration status
Write-Host "5. Database Migration"
if (Test-Path $venvPath) {
    try {
        Push-Location backend
        $alembicOutput = & ..\backend\venv\Scripts\python.exe -m alembic current 2>&1 | Out-String
        Pop-Location

        if ($alembicOutput -match "003") {
            Test-Requirement "Database migrated to v003" $true "Chat & GitHub models ready"
        } elseif ($alembicOutput -match "002") {
            Test-Warning "Database at v002" "Need to run: cd backend && venv\Scripts\python.exe -m alembic upgrade head"
        } else {
            Test-Warning "Database migration status unclear" $alembicOutput.Trim()
        }
    } catch {
        Test-Warning "Database migration check" "Could not verify (may need DATABASE_URL in .env)"
    }
} else {
    Test-Warning "Database migration" "Skipped - venv not found"
}
Write-Host ""

# Check .env configuration
Write-Host "6. Environment Configuration"
$envPath = "backend\.env"
if (Test-Path $envPath) {
    $envContent = Get-Content $envPath -Raw

    # Check GITHUB_REPO
    if ($envContent -match "GITHUB_REPO=MihaiTheCoder/DocuVibe") {
        Test-Requirement "GITHUB_REPO configured" $true "MihaiTheCoder/DocuVibe"
    } else {
        Test-Warning "GITHUB_REPO" "Should be: MihaiTheCoder/DocuVibe"
    }

    # Check GITHUB_TOKEN
    if ($envContent -match "GITHUB_TOKEN=ghp_") {
        Test-Requirement "GITHUB_TOKEN set" $true "Token found (starts with ghp_)"
    } elseif ($envContent -match "GITHUB_TOKEN=YOUR_GITHUB_TOKEN") {
        Test-Warning "GITHUB_TOKEN not set" "Get token from: https://github.com/settings/tokens"
        Write-Host "     Required scope: repo (full control)" -ForegroundColor Gray
    } else {
        Test-Warning "GITHUB_TOKEN unclear" "Check format in .env"
    }

    # Check auto-merge settings
    if ($envContent -match "GITHUB_AUTO_MERGE_EASY=true") {
        Test-Requirement "Auto-merge enabled" $true "Easy issues will auto-merge"
    } else {
        Test-Warning "Auto-merge" "Set GITHUB_AUTO_MERGE_EASY=true for automation"
    }

    # Check DATABASE_URL
    if ($envContent -match "DATABASE_URL=postgresql://") {
        Test-Requirement "DATABASE_URL configured" $true "PostgreSQL connection string found"
    } else {
        Test-Warning "DATABASE_URL" "PostgreSQL connection string needed"
    }
} else {
    Test-Requirement ".env file exists" $false "Copy from: backend\.env.example"
}
Write-Host ""

# Check test suite
Write-Host "7. Test Suite"
$testFile = "backend\test_chat_github_integration.py"
if (Test-Path $testFile) {
    Test-Requirement "Integration tests exist" $true "test_chat_github_integration.py"

    if (Test-Path $venvPath) {
        Write-Host "     Running automated tests..." -ForegroundColor Gray
        try {
            Push-Location backend
            $testOutput = & ..\backend\venv\Scripts\python.exe test_chat_github_integration.py 2>&1 | Out-String
            Pop-Location

            if ($testOutput -match "5/5 tests passed") {
                Write-Host "     [SUCCESS] All tests passed (5/5)" -ForegroundColor Green
            } elseif ($testOutput -match "tests passed") {
                Write-Host "     [PARTIAL] Some tests passed" -ForegroundColor Yellow
                Write-Host "     $($testOutput -split "`n" | Select-Object -Last 3)" -ForegroundColor Gray
            } else {
                Write-Host "     [UNKNOWN] Test results unclear" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "     [SKIP] Could not run tests" -ForegroundColor Gray
        }
    }
} else {
    Test-Warning "Integration tests" "Test file not found"
}
Write-Host ""

# Check lazy-bird setup script
Write-Host "8. Lazy-Bird Setup Script"
$setupScript = "setup-lazy-bird-wsl2.sh"
if (Test-Path $setupScript) {
    Test-Requirement "Setup script exists" $true "setup-lazy-bird-wsl2.sh"

    # Check if it has Unix line endings (should have LF, not CRLF)
    $scriptContent = Get-Content $setupScript -Raw
    if ($scriptContent -match "`r`n") {
        Test-Warning "Setup script line endings" "Has Windows CRLF, may need conversion for WSL2"
        Write-Host "     Run in WSL2: dos2unix setup-lazy-bird-wsl2.sh" -ForegroundColor Gray
    } else {
        Test-Requirement "Setup script format" $true "Unix line endings (LF)"
    }
} else {
    Test-Requirement "Setup script exists" $false "setup-lazy-bird-wsl2.sh not found"
}
Write-Host ""

# Check documentation
Write-Host "9. Documentation"
$docs = @(
    "QUICKSTART.md",
    "FULL_AUTOMATION_SETUP.md",
    "SETUP_STATUS.md",
    "CHAT_GITHUB_INTEGRATION_SUMMARY.md"
)

$docsFound = 0
foreach ($doc in $docs) {
    if (Test-Path $doc) { $docsFound++ }
}

Test-Requirement "Documentation complete" ($docsFound -eq $docs.Count) "$docsFound/$($docs.Count) files found"
Write-Host ""

# Summary
Write-Host "========================================"
Write-Host "Summary"
Write-Host "========================================"
Write-Host ""

if ($allGood) {
    Write-Host "[SUCCESS] All checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Add your GitHub token to backend\.env (line 45)" -ForegroundColor White
    Write-Host "2. Run setup in WSL2:" -ForegroundColor White
    Write-Host "   wsl" -ForegroundColor Gray
    Write-Host "   cd /mnt/d/Projects/VibeDocs" -ForegroundColor Gray
    Write-Host "   ./setup-lazy-bird-wsl2.sh" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "[INCOMPLETE] Some requirements not met" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Fix the issues above, then run this script again." -ForegroundColor White
    Write-Host ""
}

Write-Host "For detailed instructions, see: QUICKSTART.md" -ForegroundColor Cyan
Write-Host ""

# Return exit code
if ($allGood) { exit 0 } else { exit 1 }
