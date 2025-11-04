# CI Testing Guide

This guide shows you multiple ways to test your GitHub Actions CI workflow before pushing to production.

## 🚨 **Current Test Status**

Based on local testing, we found these issues that need to be fixed:

### Issues Found:
1. **Test failures**: 10 tests in `test_dependencies.py` are failing due to missing `azure_chat_openai_client` attribute
2. **Formatting issues**: `src/eval/eval.py` needs formatting 
3. **Minor lint warning**: Invalid `# noqa` directive in `test_qa_engine.py`

## 🔧 **Fix These Issues First**

### 1. Fix the formatting issue:
```bash
cd /workspaces/constitutional-qa-agent
uv run ruff format src/ tests/
```

### 2. Fix the lint warning:
Edit `tests/core/test_qa_engine.py` line 317 and change:
```python
# From: yield  # noqa: unreachable - needed for type checker
# To:   yield  # noqa: F841
```

### 3. Fix test dependencies:
The test mocking might need adjustment based on your actual dependencies module.

## 🧪 **Testing Methods**

### Method 1: Local Command Testing (Fastest)

Test each CI step locally before pushing:

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest tests/ -v --tb=short

# Check linting
uv run ruff check src/ tests/

# Check formatting
uv run ruff format --check src/ tests/

# Run type checking
uv run pyright
```

### Method 2: Using Act (Local GitHub Actions Simulation)

Act lets you run GitHub Actions locally using Docker:

```bash
# Install act (already done above)
./bin/act --list

# Test specific job
./bin/act -j test           # Run just the test job
./bin/act -j lint           # Run just the lint job
./bin/act -j type-check     # Run just the type-check job

# Test all jobs (simulates full CI)
./bin/act

# Test with specific event
./bin/act pull_request      # Simulate a pull request event
./bin/act push              # Simulate a push event

# Dry run (see what would happen)
./bin/act --dry-run

# Use specific Docker image
./bin/act -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

### Method 3: Draft Pull Request Testing

Create a draft PR to test without affecting the main branch:

```bash
# Create a test branch
git checkout -b test-ci-workflow

# Make a small change (e.g., add a comment)
echo "# CI Test" >> README.md

# Commit and push
git add .
git commit -m "test: CI workflow testing"
git push origin test-ci-workflow

# Create draft PR via GitHub CLI
gh pr create --title "Test CI Workflow" --body "Testing CI pipeline" --draft
```

### Method 4: Repository Dispatch Testing

Test using repository dispatch events:

```bash
# Trigger workflow manually (if you add workflow_dispatch)
gh workflow run ci.yml
```

### Method 5: Live Testing on Feature Branch

```bash
# Create feature branch
git checkout -b feature/test-ci

# Make changes
echo "Testing CI" > test_file.txt
git add test_file.txt
git commit -m "feat: add test file"

# Push and create PR
git push origin feature/test-ci
gh pr create --title "CI Test" --body "Testing CI workflow"

# Watch the CI run
gh pr checks
```

## 📊 **Monitoring CI Results**

### Via GitHub CLI:
```bash
# Check workflow runs
gh run list --workflow=ci.yml

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log

# Check PR status
gh pr status
gh pr checks
```

### Via Web Interface:
- Go to your repository on GitHub
- Click "Actions" tab
- View workflow runs and logs

## 🐛 **Common Issues and Solutions**

### Issue: Tests fail locally but not in CI
**Solution**: Check Python version differences, environment variables

### Issue: Act fails with permission errors
**Solution**: 
```bash
# Run with sudo if needed
sudo ./bin/act

# Or fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker
```

### Issue: Dependencies not found
**Solution**: Ensure `uv.lock` file is committed and up to date

### Issue: Type checking fails
**Solution**: Check `pyproject.toml` configuration and Python path

## 🎯 **Recommended Testing Workflow**

1. **Local Testing** (always first):
   ```bash
   uv run pytest tests/
   uv run ruff check src/ tests/
   uv run ruff format --check src/ tests/
   uv run pyright
   ```

2. **Act Testing** (optional, for full simulation):
   ```bash
   ./bin/act --dry-run
   ./bin/act -j test
   ```

3. **Draft PR Testing** (recommended):
   - Create draft PR
   - Watch CI results
   - Fix issues
   - Convert to ready for review

4. **Final Verification**:
   - Ensure all checks pass
   - Merge when green

## 🔄 **Continuous Improvement**

### Monitor CI Performance:
- Track job duration
- Optimize slow steps
- Use caching effectively

### Update Dependencies:
- Keep GitHub Actions versions current
- Update Python versions in matrix
- Review and update dev dependencies

## 📝 **Quick Fix Commands**

Here are the immediate fixes needed:

```bash
# Fix formatting
cd /workspaces/constitutional-qa-agent
uv run ruff format src/ tests/

# Fix the noqa directive
sed -i 's/# noqa: unreachable - needed for type checker/# noqa: F841/' tests/core/test_qa_engine.py

# Test again
uv run pytest tests/ -v --tb=short
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```