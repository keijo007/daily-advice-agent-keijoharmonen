#!/usr/bin/env bash
# DEPLOYMENT VERIFICATION CHECKLIST
# Run this to verify everything is ready for GitHub Actions

echo "🔍 Daily Insight Agent - Deployment Verification"
echo "=================================================="
echo ""

# 1. Check Python
echo "1. Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "   ✓ Python $PYTHON_VERSION found"
else
    echo "   ✗ Python not found (needed for local testing)"
fi
echo ""

# 2. Check script file
echo "2. Main script..."
if [ -f "scripts/generate_insight_safe.py" ]; then
    LINES=$(wc -l < scripts/generate_insight_safe.py)
    echo "   ✓ scripts/generate_insight_safe.py exists ($LINES lines)"
else
    echo "   ✗ scripts/generate_insight_safe.py NOT FOUND"
fi
echo ""

# 3. Check workflow file
echo "3. GitHub Actions workflow..."
if [ -f ".github/workflows/daily-insight.yml" ]; then
    echo "   ✓ .github/workflows/daily-insight.yml exists"
    if grep -q "python scripts/generate_insight_safe.py" .github/workflows/daily-insight.yml; then
        echo "   ✓ Workflow uses generate_insight_safe.py"
    else
        echo "   ✗ Workflow NOT using generate_insight_safe.py"
    fi
else
    echo "   ✗ .github/workflows/daily-insight.yml NOT FOUND"
fi
echo ""

# 4. Check requirements.txt
echo "4. Python dependencies..."
if [ -f "requirements.txt" ]; then
    echo "   ✓ requirements.txt found"
    
    # Check if sqlite3 is listed (it shouldn't be)
    if grep -q "^sqlite3" requirements.txt; then
        echo "   ⚠ WARNING: sqlite3 listed (it's stdlib, remove it)"
    else
        echo "   ✓ sqlite3 not listed (correct)"
    fi
    
    # Check key packages
    for pkg in fastapi openai feedparser pydantic python-dotenv; do
        if grep -q "$pkg" requirements.txt; then
            echo "   ✓ $pkg found"
        else
            echo "   ✗ $pkg missing"
        fi
    done
else
    echo "   ✗ requirements.txt NOT FOUND"
fi
echo ""

# 5. Check documentation
echo "5. Documentation..."
docs=("README.md" "ARCHITECTURE.md" "GITHUB_ACTIONS_SAFE_SETUP.md" "GITHUB_ACTIONS_SUMMARY.md")
for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "   ✓ $doc found"
    else
        echo "   ⚠ $doc missing"
    fi
done
echo ""

# 6. Check data directories (for local testing)
echo "6. Data directories..."
dirs=("data" "data/diary" "data/goals" "data/daily_insights")
for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "   ✓ $dir exists"
    else
        echo "   ⚠ $dir missing (will be created by script)"
    fi
done
echo ""

# 7. Environment variables
echo "7. Environment variables..."
if [ -n "$OPENAI_API_KEY" ]; then
    echo "   ✓ OPENAI_API_KEY set (local)"
else
    echo "   ⚠ OPENAI_API_KEY not set in local shell"
    echo "     (This is OK - you'll set it in GitHub Secrets)"
fi
echo ""

# 8. Git setup
echo "8. Git setup..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    echo "   ✓ Git repository found (branch: $BRANCH)"
    
    # Check if remote exists
    if git config --get remote.origin.url > /dev/null; then
        REMOTE=$(git config --get remote.origin.url)
        echo "   ✓ Remote origin: $REMOTE"
    else
        echo "   ✗ No remote origin configured"
    fi
else
    echo "   ✗ Not a git repository"
fi
echo ""

# 9. Summary
echo "=================================================="
echo "✅ DEPLOYMENT READY?"
echo ""
echo "Complete these steps:"
echo "1. Push code to GitHub:"
echo "   git add -A"
echo "   git commit -m 'Add safe GitHub Actions setup'"
echo "   git push"
echo ""
echo "2. Add GitHub Secret:"
echo "   GitHub → Settings → Secrets and variables → Actions"
echo "   → New repository secret"
echo "   → Name: OPENAI_API_KEY"
echo "   → Value: sk-proj-... (your OpenAI key)"
echo ""
echo "3. Test workflow:"
echo "   GitHub → Actions → Daily Insight Generator"
echo "   → Run workflow"
echo ""
echo "4. Monitor logs:"
echo "   [workflow run] → generate-insight"
echo "   Look for ✓ symbols throughout"
echo ""
echo "5. Verify results:"
echo "   ✓ index.html should appear in repo"
echo "   ✓ data/daily_insights/YYYY-MM-DD.json created"
echo ""
echo "=================================================="
