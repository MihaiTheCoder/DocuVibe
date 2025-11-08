#!/bin/bash
#
# Lazy-Bird Setup Script for WSL2
# VibeDocs - Full Automation Pipeline
#
# This script sets up lazy-bird to autonomously implement GitHub issues
# created by the VibeDocs Chat UI.
#

set -e  # Exit on error

echo "========================================"
echo "Lazy-Bird Setup for VibeDocs"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
echo ""

# Check if running in WSL
if ! grep -qi microsoft /proc/version; then
    print_error "This script must be run in WSL2"
    exit 1
fi
print_success "Running in WSL2"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_warning "Node.js not found. Installing..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
NODE_VERSION=$(node --version)
print_success "Node.js installed: $NODE_VERSION"

# Check npm
if ! command -v npm &> /dev/null; then
    print_error "npm not found"
    exit 1
fi
NPM_VERSION=$(npm --version)
print_success "npm installed: $NPM_VERSION"

# Check git
if ! command -v git &> /dev/null; then
    print_warning "Git not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y git
fi
GIT_VERSION=$(git --version)
print_success "Git installed: $GIT_VERSION"

# Check Python
if ! command -v python3 &> /dev/null; then
    print_warning "Python3 not found. Installing..."
    sudo apt-get install -y python3 python3-pip python3-venv
fi
PYTHON_VERSION=$(python3 --version)
print_success "Python3 installed: $PYTHON_VERSION"

echo ""
echo "========================================"
echo "Step 2: Claude Code CLI Setup"
echo "========================================"
echo ""

# Check if Claude Code CLI is installed
if ! command -v claude-code &> /dev/null; then
    print_warning "Claude Code CLI not found"
    echo ""
    echo "To install Claude Code CLI:"
    echo "1. Go to: https://www.anthropic.com/api"
    echo "2. Get your API key"
    echo "3. Install CLI: npm install -g @anthropic-ai/claude-code-cli"
    echo "4. Configure: claude-code configure"
    echo ""
    read -p "Press Enter when Claude Code CLI is installed and configured..."

    # Check again
    if ! command -v claude-code &> /dev/null; then
        print_error "Claude Code CLI still not found. Please install it first."
        exit 1
    fi
fi
print_success "Claude Code CLI is installed"

echo ""
echo "========================================"
echo "Step 3: Clone VibeDocs Repository"
echo "========================================"
echo ""

# Set up project directory
PROJECT_DIR="$HOME/projects/vibedocs"

if [ -d "$PROJECT_DIR" ]; then
    print_warning "VibeDocs directory already exists at $PROJECT_DIR"
    read -p "Do you want to remove it and clone fresh? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$PROJECT_DIR"
        print_success "Removed existing directory"
    fi
fi

if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$HOME/projects"
    cd "$HOME/projects"

    echo "Cloning VibeDocs repository..."
    git clone https://github.com/MihaiTheCoder/DocuVibe.git vibedocs
    print_success "Repository cloned to $PROJECT_DIR"
else
    print_success "Using existing repository at $PROJECT_DIR"
fi

cd "$PROJECT_DIR"

echo ""
echo "========================================"
echo "Step 4: Install Lazy-Bird"
echo "========================================"
echo ""

# Clone lazy-bird if not exists
LAZY_BIRD_DIR="$HOME/lazy-bird"

if [ -d "$LAZY_BIRD_DIR" ]; then
    print_warning "Lazy-bird directory already exists"
    cd "$LAZY_BIRD_DIR"
    git pull origin main
    print_success "Lazy-bird updated"
else
    cd "$HOME"
    echo "Cloning lazy-bird..."
    git clone https://github.com/yusufkaraaslan/lazy-bird.git
    print_success "Lazy-bird cloned to $LAZY_BIRD_DIR"
    cd "$LAZY_BIRD_DIR"
fi

echo ""
echo "========================================"
echo "Step 5: Validate Project"
echo "========================================"
echo ""

# Run phase0 validation
echo "Running project validation..."
if [ -f "./tests/phase0/validate-all.sh" ]; then
    chmod +x ./tests/phase0/validate-all.sh
    ./tests/phase0/validate-all.sh "$PROJECT_DIR" --type python
    print_success "Project validation complete"
else
    print_warning "Validation script not found, skipping..."
fi

echo ""
echo "========================================"
echo "Step 6: Configure Lazy-Bird"
echo "========================================"
echo ""

# Get GitHub token
echo "GitHub Personal Access Token Setup:"
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Click 'Generate new token (classic)'"
echo "3. Select scope: 'repo' (full control of private repositories)"
echo "4. Copy the token"
echo ""
read -p "Enter your GitHub token: " -s GITHUB_TOKEN
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    print_error "GitHub token is required"
    exit 1
fi
print_success "GitHub token received"

# Create lazy-bird config
echo ""
echo "Creating lazy-bird configuration..."

cat > "$PROJECT_DIR/.lazy-bird.yml" << EOF
# Lazy-Bird Configuration for VibeDocs
repository: MihaiTheCoder/DocuVibe

# Watch for issues with these labels
watch:
  labels:
    - ready
    - easy
    - medium
    - hard

# Auto-implement when issue has these label combinations
auto_implement:
  - label: ready
    require_labels:
      - feature-request

# Testing configuration
testing:
  framework: pytest
  test_command: "cd backend && python3 -m pytest"
  coverage_threshold: 70

# Implementation settings
implementation:
  style_guide: "Follow patterns in CLAUDE.md"
  max_files_per_pr: 5
  create_pr: true
  pr_template: |
    ## Automated Implementation by Lazy-Bird

    Implements: #{issue_number}

    ### Changes
    {changes_summary}

    ### Tests
    {test_summary}

    ### Checklist
    - [ ] All tests passing
    - [ ] Code follows style guide
    - [ ] Documentation updated if needed

    🤖 Generated by Lazy-Bird via VibeDocs Chat UI

# CI/CD configuration
ci:
  provider: github_actions
  check_required: true

# Auto-merge settings (managed by GitHub Monitor)
auto_merge:
  enabled: false  # VibeDocs GitHub Monitor handles this
  require_checks_passing: true
  merge_method: squash

# Environment variables
env:
  GITHUB_TOKEN: $GITHUB_TOKEN
  ANTHROPIC_API_KEY: \${ANTHROPIC_API_KEY}
EOF

print_success "Configuration file created: $PROJECT_DIR/.lazy-bird.yml"

# Set up environment
cat > "$HOME/.lazy-bird-env" << EOF
export GITHUB_TOKEN="$GITHUB_TOKEN"
export LAZY_BIRD_PROJECT="$PROJECT_DIR"
EOF

print_success "Environment variables configured"

echo ""
echo "========================================"
echo "Step 7: Install Python Dependencies"
echo "========================================"
echo ""

cd "$PROJECT_DIR/backend"

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

echo "Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt
print_success "Python dependencies installed"

echo ""
echo "========================================"
echo "Step 8: Run Lazy-Bird Wizard"
echo "========================================"
echo ""

cd "$LAZY_BIRD_DIR"

echo "Running lazy-bird wizard..."
echo "This will guide you through the final setup steps."
echo ""

if [ -f "./wizard.sh" ]; then
    chmod +x ./wizard.sh
    ./wizard.sh
else
    print_warning "Wizard not found. Manual configuration required."
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
print_success "Lazy-bird is configured and ready!"
echo ""
echo "Next steps:"
echo "1. Start lazy-bird watcher:"
echo "   cd $LAZY_BIRD_DIR"
echo "   ./lazy-bird watch --project $PROJECT_DIR --verbose"
echo ""
echo "2. In another terminal, start VibeDocs backend:"
echo "   cd $PROJECT_DIR/backend"
echo "   source venv/bin/activate"
echo "   python3 -m uvicorn app.main:app --reload"
echo ""
echo "3. Test the pipeline:"
echo "   - Create a feature request via Chat UI"
echo "   - Mark issue as 'ready'"
echo "   - Watch lazy-bird implement it"
echo "   - PR will be auto-merged if tests pass"
echo ""
echo "Configuration files:"
echo "  - Project config: $PROJECT_DIR/.lazy-bird.yml"
echo "  - Environment: $HOME/.lazy-bird-env"
echo ""
print_success "Full automation pipeline is ready! 🚀"
echo ""
