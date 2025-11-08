# Full Automation Setup Guide - Lazy-Bird + VibeDocs

**Goal:** Set up complete autonomous pipeline from Chat UI → GitHub Issue → Automated Implementation → PR → Auto-Merge

**Time Estimate:** 45-60 minutes

## Overview

This guide will set up Lazy-Bird in WSL2 to autonomously implement features created through the VibeDocs Chat UI.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows Environment                       │
│                                                              │
│  ┌───────────────────────────────────────────────────┐     │
│  │              VibeDocs Backend                      │     │
│  │  • FastAPI Server (Windows)                       │     │
│  │  • GitHub Monitor (Auto-merge)                    │     │
│  │  • PostgreSQL Database                            │     │
│  └───────────────────┬───────────────────────────────┘     │
│                      │                                       │
│                      ▼                                       │
│              ┌───────────────┐                              │
│              │  GitHub API   │                              │
│              │  (Issues)     │                              │
│              └───────┬───────┘                              │
│                      │                                       │
└──────────────────────┼───────────────────────────────────────┘
                       │
┌──────────────────────┼───────────────────────────────────────┐
│                      │        WSL2 Ubuntu                    │
│                      ▼                                        │
│              ┌───────────────┐                               │
│              │  Lazy-Bird    │                               │
│              │  • Watches "ready" label                      │
│              │  • Claude Code CLI                           │
│              │  • Implements features                       │
│              │  • Runs tests                                │
│              │  • Creates PRs                               │
│              └───────┬───────┘                               │
│                      │                                        │
│                      ▼                                        │
│              ┌───────────────┐                               │
│              │  VibeDocs     │                               │
│              │  (Cloned in   │                               │
│              │   WSL2)       │                               │
│              └───────────────┘                               │
└───────────────────────────────────────────────────────────────┘
```

## Prerequisites

✅ **You Have:**
- Windows with WSL2 installed (Ubuntu)
- Node.js 18+ (installed in both Windows and WSL2)
- GitHub repository: MihaiTheCoder/DocuVibe
- VibeDocs backend implemented and tested

⚠️ **You Need:**
- GitHub Personal Access Token (repo scope)
- Anthropic API Key (for Claude Code CLI)
- ~8GB RAM available
- ~30 minutes of setup time

## Setup Process

### Phase 1: Prepare Windows Environment (10 minutes)

This is already done! ✅

1. **Backend Configuration** ✅
   - [backend/.env](backend/.env) configured
   - Database migrated
   - GitHub token slot ready (line 45)

2. **Test Suite** ✅
   - All tests passing (5/5)
   - Models, services, workers verified

### Phase 2: WSL2 Setup (15 minutes)

Your WSL2 is already installed! ✅ Ubuntu is the default distribution.

#### 2.1: Access WSL2

Open PowerShell or Command Prompt and run:

```powershell
wsl
```

This will start Ubuntu WSL2. You should see a Linux prompt like:
```
username@computer:~$
```

#### 2.2: Update WSL2 System

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

#### 2.3: Install Required Tools

The setup script will handle this, but you can manually install:

```bash
# Node.js (if not already installed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Python and pip
sudo apt-get install -y python3 python3-pip python3-venv

# Git
sudo apt-get install -y git

# Build essentials
sudo apt-get install -y build-essential
```

### Phase 3: Claude Code CLI Setup (10 minutes)

#### 3.1: Get Anthropic API Key

1. Go to: https://console.anthropic.com/
2. Sign in or create account
3. Navigate to API Keys
4. Create a new API key
5. Copy the key (starts with `sk-ant-...`)

#### 3.2: Install Claude Code CLI

In WSL2:

```bash
npm install -g @anthropic-ai/claude-code-cli
```

#### 3.3: Configure Claude Code CLI

```bash
claude-code configure
```

Enter your API key when prompted.

#### 3.4: Verify Installation

```bash
claude-code --version
```

### Phase 4: Run Automated Setup Script (20 minutes)

#### 4.1: Copy Setup Script to WSL2

In WSL2, download the setup script from Windows:

```bash
# Access Windows files from WSL2
cd /mnt/d/Projects/VibeDocs

# Copy setup script and make executable
cp setup-lazy-bird-wsl2.sh ~/setup-lazy-bird.sh
chmod +x ~/setup-lazy-bird.sh
```

#### 4.2: Run Setup Script

```bash
cd ~
./setup-lazy-bird.sh
```

The script will:
1. ✓ Check all prerequisites
2. ✓ Verify Claude Code CLI installation
3. ✓ Clone VibeDocs to WSL2 (~//projects/vibedocs)
4. ✓ Clone and install Lazy-Bird
5. ✓ Validate the project structure
6. ✓ Create configuration files
7. ✓ Install Python dependencies
8. ✓ Run lazy-bird wizard

**During the script:**
- You'll be asked for your GitHub token (from https://github.com/settings/tokens)
- The wizard will ask ~8 configuration questions
- Choose "Python" as project type
- Confirm default settings for most options

### Phase 5: Start Services (5 minutes)

#### 5.1: Start Lazy-Bird Watcher (WSL2)

In WSL2 terminal:

```bash
# Load environment
source ~/.lazy-bird-env

# Start lazy-bird in watch mode
cd ~/lazy-bird
./lazy-bird watch --project ~/projects/vibedocs --verbose
```

Leave this terminal running. You should see:
```
[INFO] Lazy-bird watcher started
[INFO] Monitoring repository: MihaiTheCoder/DocuVibe
[INFO] Watching for labels: ready, easy, medium, hard
```

#### 5.2: Start VibeDocs Backend (Windows)

In a new Windows terminal:

```powershell
cd d:\Projects\VibeDocs\backend

# Activate virtual environment
.\venv\Scripts\activate

# Start server
python -m uvicorn app.main:app --reload --log-level info
```

You should see:
```
Starting VibeDocs Backend...
GitHub monitor started
INFO:     Started server process [PID]
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Testing the Full Pipeline

### Test Case 1: Easy Feature (Complete Automation)

#### Step 1: Create Test User and Organization

In Windows PowerShell:

```powershell
cd d:\Projects\VibeDocs\backend

.\venv\Scripts\python.exe -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization

db = SessionLocal()

# Create test organization
org = Organization(name='test-org', display_name='Test Organization')
db.add(org)
db.commit()

# Create test user
user = User(email='test@example.com', full_name='Test User')
db.add(user)
db.commit()

print(f'Organization ID: {org.id}')
print(f'User ID: {user.id}')

db.close()
"
```

Save the Organization ID and User ID.

#### Step 2: Create GitHub Issue via Chat API

```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -H "X-Organization-ID: YOUR_ORG_ID" \
  -d '{
    "message": "Add a simple CSV export button to the dashboard that downloads the current table data"
  }'
```

**Expected Response:**
```json
{
  "message": "I've created a GitHub issue for your feature request...",
  "results": [{
    "type": "github_issue",
    "data": {
      "number": 123,
      "url": "https://github.com/MihaiTheCoder/DocuVibe/issues/123",
      "difficulty": "easy",
      "title": "Add CSV export button to dashboard"
    }
  }],
  "suggested_actions": [{
    "action_type": "mark_ready",
    "label": "Mark issue as ready for implementation"
  }]
}
```

#### Step 3: Mark Issue as Ready

```bash
curl -X POST http://localhost:8000/api/v1/chat/mark-ready/{issue_id} \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -H "X-Organization-ID: YOUR_ORG_ID"
```

#### Step 4: Watch the Magic Happen

**In WSL2 terminal (lazy-bird):**
```
[INFO] Detected new issue: #123 with 'ready' label
[INFO] Starting implementation...
[INFO] Running tests...
[INFO] All tests passed
[INFO] Creating pull request...
[INFO] PR created: #45
```

**In Windows terminal (backend):**
```
GitHub monitor: Detected PR #45 for issue #123
GitHub monitor: Enabling auto-merge for easy issue
GitHub monitor: PR #45 checks passing
GitHub monitor: Auto-merging PR #45
GitHub monitor: PR #45 merged successfully
```

**Timeline:**
- T+0s: Issue created with "easy" label
- T+5s: Issue marked as "ready"
- T+60s: Lazy-bird detects ready label
- T+120s: Lazy-bird starts implementation
- T+300s: Implementation complete, tests running
- T+360s: PR created
- T+420s: GitHub Monitor detects PR
- T+480s: Tests pass, auto-merge enabled
- T+540s: PR merged, issue closed

**Total: ~9 minutes** from chat message to merged code! 🚀

### Test Case 2: Medium Feature (Manual Review)

Same process, but use a more complex request:

```json
{
  "message": "Create a new API endpoint for bulk document upload with validation, error handling, and progress tracking"
}
```

Expected behavior:
- Issue created with "medium" label
- Lazy-bird implements feature
- PR created
- **Auto-merge NOT enabled** (requires manual review)
- Developer reviews and merges manually

### Test Case 3: Hard Feature (Planning Required)

```json
{
  "message": "Implement real-time WebSocket notifications with distributed message queue and automatic failover"
}
```

Expected behavior:
- Issue created with "hard" label
- NOT automatically marked as ready
- Requires planning and discussion
- Can be marked ready manually after review

## Monitoring and Debugging

### Check Lazy-Bird Status

In WSL2:
```bash
# View logs
tail -f ~/.lazy-bird/logs/watch.log

# Check running processes
ps aux | grep lazy-bird
```

### Check GitHub Monitor Status

In Windows:
```powershell
# Check backend logs
cd d:\Projects\VibeDocs\backend
type logs\app.log | findstr /i "github"

# Check API health
curl http://localhost:8000/api/v1/health
```

### Check Database Status

```powershell
cd d:\Projects\VibeDocs\backend

.\venv\Scripts\python.exe -c "
from app.core.database import SessionLocal
from app.models.github_integration import GitHubIssue

db = SessionLocal()
issues = db.query(GitHubIssue).all()

for issue in issues:
    print(f'Issue #{issue.issue_number}: {issue.status.value}')
    if issue.pr_number:
        print(f'  PR: #{issue.pr_number} - {issue.pr_url}')

db.close()
"
```

## Troubleshooting

### Issue: Lazy-Bird Not Detecting "Ready" Label

**Check:**
```bash
# In WSL2
cd ~/lazy-bird
./lazy-bird status
```

**Fix:**
- Ensure lazy-bird watcher is running
- Check label is exactly "ready" (case-sensitive)
- Verify GitHub token has repo access

### Issue: Claude Code CLI Not Working

**Check:**
```bash
claude-code --version
```

**Fix:**
- Re-run: `claude-code configure`
- Verify API key is valid
- Check internet connection

### Issue: GitHub Monitor Not Detecting PR

**Check:**
- Is GITHUB_TOKEN set in Windows .env?
- Is backend server running?
- Check backend logs for errors

**Fix:**
```powershell
# Restart backend
cd d:\Projects\VibeDocs\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Issue: Tests Failing in PR

**Check:**
```bash
# In WSL2
cd ~/projects/vibedocs/backend
source venv/bin/activate
python3 -m pytest
```

**Fix:**
- Review test failures
- Fix implementation
- Lazy-bird will retry if configured

## Configuration Files

### Lazy-Bird Config: `~/projects/vibedocs/.lazy-bird.yml`

```yaml
repository: MihaiTheCoder/DocuVibe

watch:
  labels: [ready, easy, medium, hard]

auto_implement:
  - label: ready
    require_labels: [feature-request]

testing:
  framework: pytest
  test_command: "cd backend && python3 -m pytest"
  coverage_threshold: 70

implementation:
  style_guide: "Follow patterns in CLAUDE.md"
  max_files_per_pr: 5
  create_pr: true

ci:
  provider: github_actions
  check_required: true

auto_merge:
  enabled: false  # Handled by VibeDocs GitHub Monitor
```

### Environment: `~/.lazy-bird-env`

```bash
export GITHUB_TOKEN="your_github_token"
export LAZY_BIRD_PROJECT="$HOME/projects/vibedocs"
export ANTHROPIC_API_KEY="your_anthropic_key"
```

Load with: `source ~/.lazy-bird-env`

## Success Criteria

### Minimum Viable Success ✅

- [x] WSL2 installed and working
- [x] Claude Code CLI configured
- [x] Lazy-bird installed and watching
- [x] Backend running with GitHub Monitor
- [ ] Can create issue via Chat API
- [ ] Lazy-bird detects "ready" label
- [ ] PR created automatically

### Full Success 🎯

- All above, plus:
- [ ] Auto-merge works for easy issues
- [ ] Medium issues require review
- [ ] Hard issues require planning
- [ ] Database synced correctly
- [ ] No errors in logs

### Excellence 🚀

- All above, plus:
- [ ] Pipeline < 10 minutes end-to-end
- [ ] All difficulty levels tested
- [ ] Metrics collected
- [ ] Documentation complete

## Performance Expectations

### Easy Feature
- **Implementation:** 2-5 minutes
- **Testing:** 1-2 minutes
- **PR Creation:** 30 seconds
- **Auto-merge:** 2-3 minutes
- **Total:** 5-10 minutes

### Medium Feature
- **Implementation:** 5-15 minutes
- **Testing:** 2-5 minutes
- **PR Creation:** 30 seconds
- **Manual Review:** Variable
- **Total:** 10-20 minutes + review time

### Hard Feature
- **Planning:** Variable
- **Implementation:** 15-60 minutes
- **Testing:** 5-10 minutes
- **Review:** Variable
- **Total:** 20+ minutes + review time

## Next Steps

1. **Complete Setup**
   - Run setup script in WSL2
   - Configure GitHub token
   - Start services

2. **Test Basic Flow**
   - Create easy feature request
   - Watch full pipeline execute
   - Verify auto-merge works

3. **Test All Difficulties**
   - Easy → Auto-merge
   - Medium → Manual review
   - Hard → Planning required

4. **Monitor and Tune**
   - Collect metrics
   - Adjust thresholds
   - Optimize performance

5. **Production Readiness**
   - Add monitoring
   - Set up alerts
   - Document workflows

## Resources

- **Lazy-Bird:** https://github.com/yusufkaraaslan/lazy-bird
- **VibeDocs:** https://github.com/MihaiTheCoder/DocuVibe
- **Claude Code:** https://www.anthropic.com/api
- **GitHub Tokens:** https://github.com/settings/tokens

## Summary

This setup gives you:

✅ **Complete Automation**
- User creates feature request via chat
- System creates GitHub issue with difficulty
- Lazy-bird implements feature autonomously
- Tests run automatically
- PR created automatically
- Easy issues merge automatically
- Database tracks everything

✅ **Intelligent Classification**
- Easy features: Full automation
- Medium features: Manual review
- Hard features: Planning first

✅ **Safety and Control**
- Tests must pass before merge
- Only "easy" features auto-merge
- Can require approvals in production
- Full audit trail in database

🎯 **Result:** From idea to production in ~10 minutes with zero manual intervention for simple features!

---

**Ready to start?** Run the setup script in WSL2:

```bash
cd /mnt/d/Projects/VibeDocs
cp setup-lazy-bird-wsl2.sh ~/setup-lazy-bird.sh
chmod +x ~/setup-lazy-bird.sh
cd ~
./setup-lazy-bird.sh
```

Let's build! 🚀
