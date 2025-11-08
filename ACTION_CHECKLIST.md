# VibeDocs Full Automation - Action Checklist

**Goal:** Get from current state to fully automated pipeline in ~45 minutes

**Status:** Backend 100% ready. Need: 2 API keys + WSL2 setup

---

## Prerequisites (5 minutes)

### ✅ What You Already Have

- [x] WSL2 installed (Ubuntu)
- [x] Backend implementation complete
- [x] Database migrated to v003
- [x] All tests passing (5/5)
- [x] Node.js installed (v18.20.6)
- [x] Python environment ready
- [x] Documentation complete

### 🔑 What You Need

Get these two keys before starting:

**1. GitHub Personal Access Token** (2 minutes)
   - URL: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Name: "VibeDocs Automation"
   - Expiration: 90 days (or custom)
   - ✅ Check: `repo` (full control of private repositories)
   - Click "Generate token"
   - **Copy the token** (starts with `ghp_...`)

**2. Anthropic API Key** (2 minutes)
   - URL: https://console.anthropic.com/
   - Sign in / Create account
   - Go to: Settings → API Keys
   - Click "Create Key"
   - Name: "VibeDocs Lazy-Bird"
   - **Copy the key** (starts with `sk-ant-...`)

---

## Automated Setup (40 minutes)

### Step 1: Pre-Flight Check (2 minutes)

Run the automated pre-flight check:

```powershell
# In Windows PowerShell
cd d:\Projects\VibeDocs
powershell -ExecutionPolicy Bypass -File preflight-check.ps1
```

**Expected:** All checks pass except "GitHub Token Valid"

If any other checks fail, fix them before proceeding.

---

### Step 2: Add GitHub Token (1 minute)

Edit `backend\.env` and replace line 45:

**Before:**
```
GITHUB_TOKEN=YOUR_GITHUB_TOKEN_HERE_PLEASE_REPLACE_THIS
```

**After:**
```
GITHUB_TOKEN=ghp_your_actual_token_here
```

**Verify:**
```powershell
powershell -ExecutionPolicy Bypass -File preflight-check.ps1
```

Should now show: `[OK] GitHub Token Valid`

---

### Step 3: Create Test Data (1 minute)

```powershell
cd backend
.\venv\Scripts\python.exe setup_test_data.py
```

**Output:** Organization ID and User ID will be printed and saved to `test_credentials.txt`

**Save these IDs** - you'll need them for testing!

---

### Step 4: Run E2E Pipeline Test (1 minute)

```powershell
cd backend
.\venv\Scripts\python.exe test_e2e_pipeline.py
```

**Expected output:**
```
[PASS] Feature Analyzer
[PASS] GitHub Service
[PASS] Pipeline Readiness
[SUCCESS] All automated tests passed!
```

If all pass, your Windows environment is ready! ✅

---

### Step 5: WSL2 Lazy-Bird Setup (30 minutes)

Open a **new terminal** and enter WSL2:

```powershell
wsl
```

You should see a Linux prompt like: `username@computer:~$`

#### 5.1: Copy Setup Script (1 minute)

```bash
# In WSL2
cd /mnt/d/Projects/VibeDocs
cp setup-lazy-bird-wsl2.sh ~/setup-lazy-bird.sh
chmod +x ~/setup-lazy-bird.sh
```

#### 5.2: Run Automated Setup (25 minutes)

```bash
cd ~
./setup-lazy-bird.sh
```

**The script will:**
1. Check all prerequisites (Node.js, Python, Git)
2. Prompt for your GitHub token (paste the token you got earlier)
3. Clone VibeDocs repository to `~/projects/vibedocs`
4. Clone and install Lazy-Bird
5. Run validation tests
6. Create configuration files
7. Install Python dependencies
8. Run the Lazy-Bird wizard

**During the wizard:**
- Choose project type: **Python**
- Accept default values for most questions
- Framework: **FastAPI / pytest**

#### 5.3: Install Claude Code CLI (3 minutes)

If not already installed:

```bash
# In WSL2
npm install -g @anthropic-ai/claude-code-cli
```

Configure with your Anthropic API key:

```bash
claude-code configure
```

Paste your Anthropic API key when prompted.

**Verify:**
```bash
claude-code --version
```

---

## Start Services (5 minutes)

### Terminal 1: Lazy-Bird Watcher (WSL2)

```bash
# In WSL2
source ~/.lazy-bird-env
cd ~/lazy-bird
./lazy-bird watch --project ~/projects/vibedocs --verbose
```

**Expected output:**
```
[INFO] Lazy-bird watcher started
[INFO] Monitoring repository: MihaiTheCoder/DocuVibe
[INFO] Watching for labels: ready, easy, medium, hard
```

**Leave this terminal running!**

---

### Terminal 2: VibeDocs Backend (Windows)

Open a **new** Windows terminal:

```powershell
cd d:\Projects\VibeDocs\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --log-level info
```

**Expected output:**
```
Starting VibeDocs Backend...
Database connected
GitHub monitor started
Workers started
Uvicorn running on http://127.0.0.1:8000
```

**Leave this terminal running!**

---

### Terminal 3: Monitor Dashboard (Windows, Optional)

Open a **third** Windows terminal to watch pipeline status:

```powershell
cd d:\Projects\VibeDocs\backend
.\venv\Scripts\python.exe monitor_pipeline.py --watch
```

This shows real-time status of all issues in the pipeline.

---

## Test the Pipeline! (10 minutes)

### Test 1: Create Feature Request

Open a **fourth** terminal (or use PowerShell):

```powershell
cd d:\Projects\VibeDocs\backend

# Get your organization ID from test_credentials.txt
$ORG_ID = (Get-Content test_credentials.txt | Select-String "Organization ID").ToString().Split(": ")[1]

# Create a feature request
curl -X POST http://localhost:8000/api/v1/chat/message `
  -H "Content-Type: application/json" `
  -H "X-Organization-ID: $ORG_ID" `
  -d '{\"message\": \"Add a simple CSV export button to download table data\"}'
```

**Expected:** Response with issue number and URL

---

### Test 2: Mark as Ready

From the response, get the `issue_id` and mark it ready:

```powershell
# Replace ISSUE_ID with actual ID from response
curl -X POST http://localhost:8000/api/v1/chat/mark-ready/ISSUE_ID `
  -H "X-Organization-ID: $ORG_ID"
```

---

### Test 3: Watch the Magic! ⚡

**In Terminal 1 (WSL2 - Lazy-Bird):**
```
[INFO] Detected issue #123 with 'ready' label
[INFO] Starting implementation...
[INFO] Analyzing codebase...
[INFO] Implementing feature...
[INFO] Running tests...
[INFO] All tests passed
[INFO] Creating pull request...
[INFO] PR #45 created
```

**In Terminal 2 (Windows - Backend):**
```
GitHub monitor: Detected PR #45 for issue #123
GitHub monitor: Enabling auto-merge (easy issue)
GitHub monitor: Waiting for checks...
GitHub monitor: Checks passed
GitHub monitor: Auto-merging PR #45
GitHub monitor: PR #45 merged successfully
```

**In Terminal 3 (Windows - Monitor):**
Watch the issue progress through stages:
- `[NEW] [EASY] Issue #123` → `[READY]` → `[WORK]` → `[PR]` → `[TEST]` → `[DONE]`

**On GitHub:**
- Check: https://github.com/MihaiTheCoder/DocuVibe/issues
- Check: https://github.com/MihaiTheCoder/DocuVibe/pulls

---

## Expected Timeline

For an **easy** feature:

| Time | Event |
|------|-------|
| T+0s | User creates feature request |
| T+2s | Chat API creates GitHub issue |
| T+5s | User marks as "ready" |
| T+60s | Lazy-Bird detects ready label |
| T+120s | Lazy-Bird starts implementation |
| T+300s | Implementation complete, tests run |
| T+360s | PR created |
| T+420s | GitHub Monitor detects PR |
| T+480s | Tests pass, auto-merge triggered |
| T+540s | PR merged! |

**Total: ~9 minutes** from idea to production! 🎉

---

## Troubleshooting

### Issue: "GitHub token not configured"

**Fix:** Edit `backend\.env` line 45 with your actual GitHub token

### Issue: "Claude Code CLI not found" (in WSL2)

**Fix:**
```bash
npm install -g @anthropic-ai/claude-code-cli
claude-code configure
```

### Issue: "Lazy-bird not detecting issues"

**Check:**
```bash
# In WSL2
ps aux | grep lazy-bird
```

**Fix:** Restart lazy-bird:
```bash
cd ~/lazy-bird
./lazy-bird watch --project ~/projects/vibedocs --verbose
```

### Issue: "Backend not starting"

**Check:** Is database accessible?
```powershell
cd backend
.\venv\Scripts\python.exe -c "from app.core.database import SessionLocal; SessionLocal()"
```

**Fix:** Check DATABASE_URL in `.env`

### Issue: "PR not auto-merging"

**Check:**
1. Is issue marked as "easy"?
2. Is auto_merge_enabled=true in database?
3. Did all tests pass on GitHub?

**Fix:**
```powershell
cd backend
.\venv\Scripts\python.exe monitor_pipeline.py
```

Check the issue status and auto_merge_enabled field.

---

## Verification Checklist

After setup, verify everything works:

- [ ] Pre-flight check passes all tests
- [ ] GitHub token is valid (not placeholder)
- [ ] Test data created (org + user)
- [ ] E2E pipeline test passes
- [ ] WSL2 setup complete
- [ ] Lazy-bird installed and configured
- [ ] Claude Code CLI configured
- [ ] Backend starts without errors
- [ ] Lazy-bird watcher running
- [ ] GitHub Monitor started
- [ ] Can create issue via API
- [ ] Issue appears on GitHub
- [ ] Lazy-bird detects "ready" label
- [ ] PR is created automatically
- [ ] Auto-merge works for easy issues
- [ ] Monitor dashboard shows status

---

## Success Metrics

Your automation is working if:

✅ **Easy features:** Fully automated (0 manual steps)
- Chat → Issue → Implementation → PR → Merge

✅ **Medium features:** Automated implementation + manual review
- Chat → Issue → Implementation → PR → [Manual Review] → Merge

✅ **Hard features:** Requires planning
- Chat → Issue → [Manual Planning] → Mark Ready → Auto-implement → PR → Review → Merge

✅ **Pipeline speed:** < 10 minutes for easy features

✅ **No errors:** All services running without crashes

---

## Quick Reference Commands

### Start Everything

**Windows (Backend):**
```powershell
cd d:\Projects\VibeDocs\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

**WSL2 (Lazy-Bird):**
```bash
source ~/.lazy-bird-env
cd ~/lazy-bird
./lazy-bird watch --project ~/projects/vibedocs --verbose
```

### Monitor Status

```powershell
cd d:\Projects\VibeDocs\backend
.\venv\Scripts\python.exe monitor_pipeline.py --watch
```

### Create Test Issue

```powershell
$ORG_ID = (Get-Content backend\test_credentials.txt | Select-String "Organization ID").ToString().Split(": ")[1]

curl -X POST http://localhost:8000/api/v1/chat/message `
  -H "Content-Type: application/json" `
  -H "X-Organization-ID: $ORG_ID" `
  -d '{\"message\": \"Your feature request here\"}'
```

### Check Logs

**Backend:**
```powershell
cd backend
type logs\app.log | findstr /i "github"
```

**Lazy-Bird:**
```bash
# In WSL2
tail -f ~/.lazy-bird/logs/watch.log
```

---

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - Fast 5-step guide
- [FULL_AUTOMATION_SETUP.md](FULL_AUTOMATION_SETUP.md) - Complete 60-minute guide
- [SETUP_STATUS.md](SETUP_STATUS.md) - Implementation status
- [CHAT_GITHUB_INTEGRATION_SUMMARY.md](CHAT_GITHUB_INTEGRATION_SUMMARY.md) - Backend details

---

## Support

If you encounter issues:

1. Run `preflight-check.ps1` to verify Windows setup
2. Run `test_e2e_pipeline.py` to test backend
3. Check lazy-bird logs: `tail -f ~/.lazy-bird/logs/watch.log`
4. Check backend logs: `type backend\logs\app.log`
5. Use monitor dashboard: `python monitor_pipeline.py --watch`

---

## Summary

**Time investment:** ~45 minutes
**Result:** Fully automated feature implementation pipeline
**Value:** From idea to production in ~10 minutes (for easy features)

**You're building the future of software development!** 🚀

Good luck! 🎉
