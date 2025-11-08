# Full Pipeline Test - Step by Step

**Goal:** Test complete autonomous pipeline from API request to deployed code

**Status:** Backend is starting... ✅

---

## Current Status

✅ **Backend Starting** - Server booting up
✅ **GitHub Token** - Configured
✅ **Anthropic Key** - Configured
✅ **Database** - Ready
✅ **Test Data** - Organization & User created

---

## Step 1: Lazy-Bird Setup (WSL2) - 30 minutes

### Open WSL2

```powershell
# Open WSL2 Ubuntu
wsl -d Ubuntu
```

You should see a Linux prompt like: `username@computer:~$`

### Run Automated Setup

```bash
# In WSL2:
cd /mnt/d/Projects/VibeDocs
bash setup-lazy-bird-wsl2.sh
```

**The script will:**
1. ✅ Read your GitHub token from .env automatically
2. ✅ Read your Anthropic key from .env automatically
3. Install Node.js (if needed)
4. Install Python (if needed)
5. Clone lazy-bird repository
6. Install Claude Code CLI
7. Configure everything
8. Validate setup

### During Setup

When the script asks:

**"Enter your GitHub token:"**
→ It should auto-read from .env, just press Enter if it shows "GitHub token found"

**"Enter your Anthropic API key:"**
→ It should auto-read from .env, just press Enter if it shows "API key found"

**"Choose project type:"**
→ Type: `Python`

**"Test framework:"**
→ Type: `pytest`

**Other questions:**
→ Press Enter to accept defaults

### After Setup

You should see:
```
[SUCCESS] Lazy-bird configured!
[SUCCESS] Claude Code CLI installed!
[OK] Project validated!
```

---

## Step 2: Start Lazy-Bird Watcher (WSL2)

Still in WSL2:

```bash
# Load environment
source ~/.lazy-bird-env

# Start lazy-bird in watch mode
cd ~/lazy-bird
./lazy-bird watch --project ~/projects/vibedocs --verbose
```

**Expected output:**
```
[INFO] Lazy-bird watcher started
[INFO] Monitoring repository: MihaiTheCoder/DocuVibe
[INFO] Watching for labels: ready, easy, medium, hard
[INFO] Polling every 60 seconds...
```

**Leave this terminal running!**

---

## Step 3: Verify Backend is Running (Windows)

Backend should already be running. Check:

```powershell
# In new Windows terminal:
curl http://localhost:8000/api/v1/health
```

**Expected:**
```json
{"status": "ok"}
```

If not running, start it:
```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Wait for: `"GitHub monitor started"` ✅

---

## Step 4: Create Feature Request (Windows)

Now the fun part! Create a feature via API:

```powershell
# Get org ID
$ORG_ID = "cbd50808-75e3-45a8-80fa-86f418f41c13"

# Create feature request
curl -X POST http://localhost:8000/api/v1/chat/message `
  -H "Content-Type: application/json" `
  -H "X-Organization-ID: $ORG_ID" `
  -d '{\"message\": \"Add a health check endpoint at /api/v1/status that returns server uptime and database connection status\"}'
```

**Expected Response:**
```json
{
  "message": "I've created a GitHub issue...",
  "results": [{
    "type": "github_issue",
    "data": {
      "number": 1,
      "url": "https://github.com/MihaiTheCoder/DocuVibe/issues/1",
      "difficulty": "easy"
    }
  }],
  "suggested_actions": [{
    "action_type": "mark_ready",
    "label": "Mark issue as ready for implementation"
  }],
  "conversation_id": "..."
}
```

**Save the issue number!** (e.g., #1)

---

## Step 5: Check GitHub Issue

Open: https://github.com/MihaiTheCoder/DocuVibe/issues

You should see your issue with:
- ✅ Title: "Add a health check endpoint..."
- ✅ Label: `easy`
- ✅ Label: `feature-request`
- ✅ Detailed description with acceptance criteria

**🎉 If you see this, API → GitHub is working!**

---

## Step 6: Mark Issue as Ready

Get the `issue_id` from the response above, then:

```powershell
# Replace with actual issue_id
$ISSUE_ID = "uuid-from-response"

curl -X POST http://localhost:8000/api/v1/chat/mark-ready/$ISSUE_ID `
  -H "X-Organization-ID: $ORG_ID"
```

**OR** manually add the "ready" label on GitHub:
1. Go to the issue
2. Click "Labels"
3. Add "ready" label

---

## Step 7: Watch Lazy-Bird Work! ⚡

**In WSL2 terminal (lazy-bird):**

Within ~60 seconds, you should see:
```
[INFO] Detected issue #1 with 'ready' label
[INFO] Starting implementation for: Add a health check endpoint...
[INFO] Analyzing codebase...
[INFO] Creating implementation plan...
[INFO] Implementing feature...
[INFO] Writing code...
[INFO] Running tests...
```

**This will take 3-5 minutes...**

Then:
```
[INFO] All tests passed!
[INFO] Creating pull request...
[INFO] PR #1 created: https://github.com/MihaiTheCoder/DocuVibe/pull/1
[SUCCESS] Implementation complete!
```

**🎉 If you see this, autonomous implementation is working!**

---

## Step 8: Watch Auto-Merge! 🚀

**In Windows terminal (backend logs):**

You should see:
```
GitHub monitor: Detected PR #1 for issue #1
GitHub monitor: PR is for easy issue, enabling auto-merge
GitHub monitor: Waiting for checks to pass...
GitHub monitor: Checks are passing
GitHub monitor: Auto-merging PR #1...
GitHub monitor: PR #1 merged successfully!
```

**Check GitHub:**
- PR should show as "Merged" ✅
- Issue should show as "Closed" ✅

**🎉 If you see this, auto-merge is working!**

---

## Step 9: Verify Code is Merged

Check the new endpoint works:

```powershell
# This should work after merge!
curl http://localhost:8000/api/v1/status
```

**Expected:**
```json
{
  "status": "ok",
  "uptime": "...",
  "database": "connected"
}
```

**🎉 If you see this, the feature is deployed locally!**

---

## Complete Timeline

| Time | Event | Where to Watch |
|------|-------|----------------|
| T+0s | API request sent | Windows terminal |
| T+2s | GitHub issue created | GitHub website |
| T+5s | Issue marked as "ready" | GitHub issue page |
| T+60s | Lazy-bird detects label | WSL2 terminal |
| T+120s | Implementation starts | WSL2 terminal |
| T+300s | Tests run | WSL2 terminal |
| T+360s | PR created | GitHub PR page |
| T+420s | GitHub Monitor detects PR | Backend logs |
| T+480s | Tests pass on GitHub | GitHub Actions |
| T+540s | Auto-merge triggered | Backend logs |
| T+600s | PR merged, issue closed | GitHub |
| T+610s | New endpoint works | curl test |

**Total: ~10 minutes from request to working code!** 🎉

---

## Troubleshooting

### Issue: "Lazy-bird not detecting issue"

**Check:**
```bash
# In WSL2
ps aux | grep lazy-bird
```

**Fix:**
```bash
cd ~/lazy-bird
./lazy-bird watch --project ~/projects/vibedocs --verbose
```

### Issue: "Tests failing on PR"

**Check GitHub Actions:**
- Go to PR → "Checks" tab
- See what failed

**Common fixes:**
- Lazy-bird might need code style fixes
- Tests might need database connection
- Check backend/pytest.ini configuration

### Issue: "Auto-merge not triggering"

**Check:**
1. Is issue marked as "easy"?
2. Are all checks passing?
3. Is backend GitHub Monitor running?

**Verify in database:**
```powershell
cd backend
.\venv\Scripts\python.exe monitor_pipeline.py
```

Look for `auto_merge_enabled: true`

---

## Success Criteria

✅ **Phase 1:** Backend started
✅ **Phase 2:** Lazy-bird watcher running
✅ **Phase 3:** API creates GitHub issue
✅ **Phase 4:** Issue appears on GitHub with labels
✅ **Phase 5:** Lazy-bird detects "ready" label
✅ **Phase 6:** Feature implemented autonomously
✅ **Phase 7:** PR created automatically
✅ **Phase 8:** GitHub Monitor detects PR
✅ **Phase 9:** Auto-merge triggered
✅ **Phase 10:** PR merged, issue closed
✅ **Phase 11:** New endpoint works!

**If all ✅: Full automation is working!** 🚀

---

## Next Steps

Once this works:

1. **Test Medium Feature** - Requires manual review before merge
2. **Test Hard Feature** - Requires planning before implementation
3. **Set up CI/CD** - Deploy to Azure automatically
4. **Add monitoring** - Track metrics and performance

---

## Notes

- First run might take longer (lazy-bird learning codebase)
- Check lazy-bird logs for detailed progress
- GitHub Actions must pass for auto-merge
- Easy issues auto-merge, medium/hard need review

---

**Ready to start?**

**Step 1:** Open WSL2 and run the setup script!

```powershell
wsl -d Ubuntu
# Then in WSL2:
cd /mnt/d/Projects/VibeDocs
bash setup-lazy-bird-wsl2.sh
```

Let's build the future! 🚀
