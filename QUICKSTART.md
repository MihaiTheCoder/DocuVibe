# Quick Start - Full Automation in 5 Steps

**Goal:** Get lazy-bird running and test the full pipeline in under 30 minutes.

## Prerequisites

Before starting, get these ready:

1. **GitHub Personal Access Token**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scope: `repo` (full control)
   - Copy the token (starts with `ghp_...`)

2. **Anthropic API Key**
   - Go to: https://console.anthropic.com/
   - Sign in or create account
   - Navigate to API Keys → Create key
   - Copy the key (starts with `sk-ant-...`)

3. **Windows Terminal** (recommended)
   - Install from Microsoft Store if you don't have it

---

## Step 1: Open WSL2 (2 minutes)

WSL2 is already installed on your system! ✅

Open PowerShell or Windows Terminal and run:

```powershell
wsl
```

You should see a Linux prompt like:
```
username@computer:~$
```

---

## Step 2: Run Setup Script (15 minutes)

In WSL2, run these commands:

```bash
# Copy setup script from Windows to WSL2
cd /mnt/d/Projects/VibeDocs
cp setup-lazy-bird-wsl2.sh ~/setup-lazy-bird.sh
chmod +x ~/setup-lazy-bird.sh

# Run setup
cd ~
./setup-lazy-bird.sh
```

**During setup:**
- When asked for GitHub token: Paste the token from Prerequisites
- When asked questions by wizard: Press Enter for defaults
- Choose "Python" as project type when asked

The script will:
- ✓ Install all dependencies
- ✓ Clone VibeDocs in WSL2
- ✓ Install Lazy-Bird
- ✓ Configure everything

---

## Step 3: Install Claude Code CLI (5 minutes)

In WSL2:

```bash
# Install CLI
npm install -g @anthropic-ai/claude-code-cli

# Configure with your API key
claude-code configure
```

When prompted, paste your Anthropic API key.

Verify:
```bash
claude-code --version
```

---

## Step 4: Start Services (5 minutes)

### Terminal 1 (WSL2) - Lazy-Bird Watcher

```bash
# Load environment
source ~/.lazy-bird-env

# Start lazy-bird
cd ~/lazy-bird
./lazy-bird watch --project ~/projects/vibedocs --verbose
```

Leave this running. You should see:
```
[INFO] Lazy-bird watcher started
[INFO] Monitoring repository: MihaiTheCoder/DocuVibe
```

### Terminal 2 (Windows) - VibeDocs Backend

Open a new Windows terminal:

```powershell
cd d:\Projects\VibeDocs\backend

# Add your GitHub token to .env first!
# Edit backend\.env and replace line 45:
# GITHUB_TOKEN=your_actual_github_token

# Start backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

You should see:
```
Starting VibeDocs Backend...
GitHub monitor started
Uvicorn running on http://127.0.0.1:8000
```

---

## Step 5: Test the Pipeline (5 minutes)

### Create Test Data

In a new Windows PowerShell:

```powershell
cd d:\Projects\VibeDocs\backend

.\venv\Scripts\python.exe -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization

db = SessionLocal()

org = Organization(name='test-org', display_name='Test Organization')
db.add(org)
db.commit()

user = User(email='test@example.com', full_name='Test User')
db.add(user)
db.commit()

print(f'Organization ID: {org.id}')
print(f'User ID: {user.id}')

db.close()
"
```

**Save the IDs that are printed!**

### Create a Feature Request

Use the API to create an easy feature request:

```bash
# Replace ORG_ID with the value from above
# Replace AUTH_TOKEN with your test token

curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -H "X-Organization-ID: YOUR_ORG_ID" \
  -d '{
    "message": "Add a simple export button that downloads data as CSV"
  }'
```

### Mark as Ready

From the response, get the `issue_id` and mark it ready:

```bash
curl -X POST http://localhost:8000/api/v1/chat/mark-ready/{issue_id} \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -H "X-Organization-ID: YOUR_ORG_ID"
```

### Watch the Magic! 🎉

**In WSL2 terminal (lazy-bird):**
- Watch it detect the "ready" label
- See it implement the feature
- Watch tests run
- See PR creation

**In Windows terminal (backend):**
- GitHub Monitor detects PR
- Auto-merge enabled for easy issue
- PR merged when tests pass

**Expected time:** 5-10 minutes from "mark ready" to merged code!

---

## Troubleshooting

### "GitHub token not configured"

Edit `d:\Projects\VibeDocs\backend\.env` line 45:
```
GITHUB_TOKEN=ghp_your_actual_token_here
```

Then restart the backend.

### "Claude Code CLI not found"

In WSL2:
```bash
npm install -g @anthropic-ai/claude-code-cli
claude-code configure
```

### "Lazy-bird not detecting issues"

Check if watcher is running:
```bash
ps aux | grep lazy-bird
```

Restart if needed:
```bash
cd ~/lazy-bird
./lazy-bird watch --project ~/projects/vibedocs --verbose
```

---

## What's Happening Behind the Scenes

1. **Chat UI** → Creates feature request
2. **Feature Analyzer** → Classifies difficulty (easy/medium/hard)
3. **GitHub Service** → Creates issue with labels
4. **Lazy-Bird** → Detects "ready" label
5. **Claude Code CLI** → Implements the feature autonomously
6. **Tests** → Run automatically
7. **PR Created** → Lazy-bird creates pull request
8. **GitHub Monitor** → Detects PR (Windows backend)
9. **Auto-Merge** → Merges if easy + tests pass
10. **Database** → Updates issue status

**Total pipeline time:** ~10 minutes for easy features!

---

## Next Steps

Once the basic test works:

1. **Test Medium Features** - Manual review required
2. **Test Hard Features** - Planning required first
3. **Add Monitoring** - Track metrics and performance
4. **Tune Configuration** - Adjust thresholds as needed

---

## Success! 🚀

You now have:
- ✅ Full automation from chat to production
- ✅ Intelligent difficulty classification
- ✅ Auto-merge for easy issues
- ✅ Manual review for complex changes
- ✅ Complete audit trail

**From idea to production in ~10 minutes!**

---

## Resources

- **Full Guide:** [FULL_AUTOMATION_SETUP.md](FULL_AUTOMATION_SETUP.md)
- **Setup Status:** [SETUP_STATUS.md](SETUP_STATUS.md)
- **Integration Summary:** [CHAT_GITHUB_INTEGRATION_SUMMARY.md](CHAT_GITHUB_INTEGRATION_SUMMARY.md)

---

**Questions?** Check [FULL_AUTOMATION_SETUP.md](FULL_AUTOMATION_SETUP.md) for detailed troubleshooting.

**Ready to start?** Go to Step 1! ⬆️
