# VS Code Setup Guide for VibeDocs

## Quick Fix: Python Interpreter Not Found

If you see an error like `No module named uvicorn` when debugging, follow these steps:

### Step 1: Select Python Interpreter

1. Open VS Code Command Palette:
   - Windows/Linux: `Ctrl+Shift+P`
   - Mac: `Cmd+Shift+P`

2. Type: `Python: Select Interpreter`

3. Choose: `Python 3.11.0 ('venv': venv) .\backend\venv\Scripts\python.exe`

   If you don't see it:
   - Click "Enter interpreter path..."
   - Browse to: `D:\Projects\VibeDocs\backend\venv\Scripts\python.exe`

### Step 2: Reload VS Code Window

1. Command Palette (`Ctrl+Shift+P`)
2. Type: `Developer: Reload Window`
3. Press Enter

### Step 3: Verify Setup

Open a new terminal in VS Code. You should see:
```
(venv) PS D:\Projects\VibeDocs\backend>
```

The `(venv)` prefix indicates the virtual environment is active.

## What We Fixed

### Created Virtual Environment
```bash
cd backend
python -m venv venv
```

### Installed All Dependencies
All packages from `requirements.txt` are now installed in the venv:
- ✅ FastAPI 0.115.0
- ✅ Uvicorn 0.30.6
- ✅ Azure Storage Blob 12.19.0
- ✅ Azure Identity 1.15.0
- ✅ Gunicorn 22.0.0
- ✅ And all other dependencies...

### Updated Configuration
- ✅ `.vscode/settings.json` configured to use venv
- ✅ `backend/.gitignore` updated to exclude venv
- ✅ Terminal environment variables set

## Debugging Now Works!

### Backend Debugger
1. Press `F5`
2. Select "Backend: FastAPI"
3. Server starts at http://localhost:8000
4. Set breakpoints and debug!

### Full Stack Debugger
1. Press `F5`
2. Select "Full Stack: Backend + Frontend"
3. Both services start together
4. Backend: http://localhost:8000
5. Frontend: http://localhost:3000

## Troubleshooting

### Still seeing Python 3.9?

**Solution 1: Restart VS Code completely**
- Close all VS Code windows
- Reopen the workspace

**Solution 2: Manually select interpreter**
- Click on Python version in bottom-left status bar
- Select the venv interpreter

### Virtual environment not activating?

**Manual activation:**
```powershell
# PowerShell
cd backend
.\venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

```bash
# Git Bash / WSL
cd backend
source venv/Scripts/activate
```

### Dependencies missing?

**Reinstall in venv:**
```bash
cd backend
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Verification Commands

Run these to verify everything is working:

```bash
# Check Python version in venv
cd backend
.\venv\Scripts\python.exe --version
# Should show: Python 3.11.0

# Check uvicorn is installed
.\venv\Scripts\python.exe -m pip show uvicorn
# Should show: Name: uvicorn, Version: 0.30.6

# Test backend manually
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
# Should start server at http://127.0.0.1:8000
```

## Why Virtual Environment?

✅ **Isolated dependencies**: Each project has its own packages
✅ **No conflicts**: Different projects can use different versions
✅ **Reproducible**: Same setup on every machine
✅ **Clean**: Easy to delete and recreate
✅ **Best practice**: Industry standard for Python projects

## Next Steps

Once the Python interpreter is selected correctly:
1. ✅ Debugger will work from VS Code
2. ✅ IntelliSense will show correct imports
3. ✅ Linting will use correct Python version
4. ✅ Tests will run in correct environment

Ready to debug! Press `F5` and select your configuration.
