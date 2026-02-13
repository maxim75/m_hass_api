# Automated PyPI Deployment Guide

This guide explains how to set up and use the automated CI/CD pipeline for deploying `m-hass-api` to PyPI.

## Overview

The GitHub Actions workflow (`.github/workflows/ci.yml`) provides:

1. **Automated Testing** - Runs tests on multiple OS/Python versions
2. **Code Quality Checks** - Linting with flake8, type checking with mypy
3. **Automated Building** - Builds Python packages (wheel and source)
4. **Automated Publishing** - Deploys to TestPyPI and PyPI

---

## Prerequisites

### 1. PyPI Account

1. Create an account at https://pypi.org/account/register/
2. Enable **2-Factor Authentication** (required)
3. Generate API tokens:
   - **Production PyPI**: https://pypi.org/manage/account/token/
   - **TestPyPI**: https://test.pypi.org/manage/account/token/

### 2. GitHub Repository Settings

1. Go to your GitHub repository: https://github.com/maxim75/m-hass-api/settings
2. Navigate to **Secrets and variables** → **Actions**
3. Add the following secrets (see sections below)

---

## Setting Up Trusted Publishing (Recommended)

Trusted publishing is the modern, secure way to deploy to PyPI using GitHub Actions.

### For Production PyPI

1. Go to https://pypi.org/manage/account/publishing/
2. Click **"Add a new pending publisher"**
3. Fill in the form:
   - **PyPI Project Name**: `m-hass-api`
   - **Owner**: `maxim75` (your GitHub username)
   - **Repository name**: `m-hass-api`
   - **Workflow name**: `publish.yml` (or your workflow file name)
   - **Environment name**: `pypi`
4. Click **"Add"**

### For TestPyPI

1. Go to https://test.pypi.org/manage/account/publishing/
2. Repeat the same process as above
3. Use environment name: `testpypi`

### Create GitHub Environments

1. In your GitHub repo, go to **Settings** → **Environments**
2. Create environment named `pypi`
3. Optionally add protection rules:
   - Required reviewers
   - Wait timer
4. Create environment named `testpypi`

---

## Alternative: Using API Tokens (Legacy)

If you prefer to use API tokens instead of trusted publishing:

### Add PyPI Token as Secret

1. In GitHub, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Name: `PYPI_API_TOKEN`
4. Value: Your PyPI API token (starts with `pypi-`)
5. Click **"Add secret"**

### Update Workflow

Replace the `publish-pypi` job in `.github/workflows/ci.yml` with:

```yaml
publish-pypi:
  name: Publish to PyPI
  runs-on: ubuntu-latest
  needs: build
  if: github.event_name == 'release' && github.event.action == 'published'

  steps:
    - uses: actions/checkout@v4

    - name: Download build artifacts
      uses: actions/download-artifact@v4
      with:
        name: dist
        path: dist/

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install twine
      run: |
        python -m pip install --upgrade pip
        pip install twine

    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*

    - name: Create GitHub Release
      uses: softprops/action-gh-release@v1
      with:
        generate_release_notes: true
        files: |
          dist/*.whl
          dist/*.tar.gz
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Workflow Triggers

The CI/CD pipeline runs automatically on:

### 1. Push to Main or Develop
```bash
git push origin main      # Triggers test + build
git push origin develop    # Triggers test + build + publish to TestPyPI
```

### 2. Pull Requests
```bash
# Creates PR to main or develop
gh pr create --base main --title "New feature"
```
- Runs full test suite
- Does **not** publish anything

### 3. GitHub Release
```bash
# Create a new release (triggers publish to PyPI)
gh release create v1.0.0 --generate-notes
```
- Runs tests
- Builds package
- Publishes to production PyPI
- Creates GitHub release with download links

---

## Deployment Process

### Development Workflow

1. **Make changes** to your code
2. **Commit changes**:
   ```bash
   git add .
   git commit -m "Add new feature"
   ```
3. **Push to develop**:
   ```bash
   git push origin develop
   ```
4. **Watch the Actions tab**:
   - Tests run automatically
   - Package builds automatically
   - Package publishes to TestPyPI automatically

5. **Test from TestPyPI**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple m-hass-api
   ```

### Production Workflow

1. **Merge develop to main**:
   ```bash
   git checkout main
   git merge develop
   git push origin main
   ```

2. **Create a GitHub release**:
   - Option A: Using GitHub CLI:
     ```bash
     gh release create v0.5.0 --generate-notes
     ```
   - Option B: Using GitHub web interface:
     - Go to **Releases** → **Create a new release**
     - Tag: `v0.5.0`
     - Target: `main`
     - Check **"Set as the latest release"**
     - Click **"Publish release"**

3. **Watch the deployment**:
   - Tests run on multiple OS/Python versions
   - Package builds successfully
   - Package publishes to PyPI
   - GitHub release is created

4. **Verify on PyPI**:
   ```bash
   pip install m-hass-api
   python -c "from m_hass_api import HassApiClient, HassStateMonitor; print('Success!')"
   ```

---

## Monitoring Deployments

### View Workflow Runs

1. Go to your GitHub repository
2. Click **Actions** tab
3. See all workflow runs with status (✅ passed, ❌ failed)

### View Deployment Logs

1. Click on a specific workflow run
2. Expand job logs to see:
   - Test results
   - Build output
   - Deployment status
   - Any errors

### Common Issues

#### Tests Fail
- **Check**: Pull request comments or Actions tab
- **Fix**: Update code locally, commit, and push

#### Build Fails
- **Check**: Build job logs in Actions
- **Common causes**:
  - Missing dependencies in `setup.py`
  - Syntax errors in code
  - Missing files in package

#### Deployment Fails
- **Check**: Publish job logs
- **Common causes**:
  - Missing PyPI API token or trusted publishing setup
  - Version already exists on PyPI
  - Package name conflict
  - Invalid metadata in `setup.py`

---

## Version Management

### Semantic Versioning

Update `setup.py` version following [semver](https://semver.org/):

```python
# setup.py
version="0.4.0"  # MAJOR.MINOR.PATCH
```

- **MAJOR** (e.g., 0.4.0 → 1.0.0): Breaking changes
- **MINOR** (e.g., 0.4.0 → 0.5.0): New features, backwards compatible
- **PATCH** (e.g., 0.4.0 → 0.4.1): Bug fixes, backwards compatible

### Create a Release

1. **Update version** in `setup.py`
2. **Update CHANGELOG** (if you have one)
3. **Commit and push**:
   ```bash
   git add setup.py
   git commit -m "Bump version to 0.5.0"
   git push origin main
   ```
4. **Create GitHub release**:
   ```bash
   gh release create v0.5.0 --generate-notes
   ```

---

## Workflow Details

### Test Job

Runs on matrix:
- **OS**: Ubuntu, macOS, Windows
- **Python**: 3.8, 3.9, 3.10, 3.11, 3.12

Executes:
1. Install dependencies
2. Run flake8 linting
3. Run mypy type checking
4. Run pytest with coverage
5. Upload coverage to Codecov

### Build Job

Executes:
1. Install build tools
2. Build package (wheel + source)
3. Validate package with twine
4. Upload artifacts for deployment jobs

### Publish to TestPyPI Job

**Trigger**: Push to `develop` branch

Executes:
1. Download build artifacts
2. Publish to TestPyPI

### Publish to PyPI Job

**Trigger**: GitHub release published

Executes:
1. Download build artifacts
2. Publish to PyPI
3. Create GitHub release with download links

---

## Best Practices

### 1. Always Test First

Always push to `develop` first to test on TestPyPI:

```bash
git push origin develop  # TestPyPI deployment
# Test the package
gh pr create --base main  # Create PR for review
```

### 2. Use Semantic Versioning

Never reuse a version number. Always increment:

```python
# ❌ BAD - Don't reuse versions
version="0.4.0"  # Already deployed

# ✅ GOOD - Always increment
version="0.4.1"  # Patch version
```

### 3. Write Clear Commit Messages

Use conventional commits:

```bash
git commit -m "feat: add SSL/TLS support for WebSocket"
git commit -m "fix: resolve thread safety issue in subscription_ids"
git commit -m "docs: update README with usage examples"
```

### 4. Monitor Deployments

Always check the Actions tab after pushing:

```bash
# Push and open Actions in browser
git push origin main
gh run list  # View recent workflow runs
gh run view  # View specific run details
```

### 5. Keep Dependencies Updated

Regularly update `setup.py` dependencies:

```bash
pip list --outdated
# Update versions in setup.py
git add setup.py
git commit -m "chore: update dependencies"
```

---

## Troubleshooting

### Issue: "Permission denied" when publishing

**Solution**:
1. Verify trusted publishing is set up correctly
2. Check GitHub environment permissions
3. Ensure 2FA is enabled on PyPI

### Issue: "403 Forbidden" from PyPI

**Solution**:
1. Check API token is valid
2. Verify token has publish permissions
3. Ensure package name isn't taken

### Issue: "Version already exists"

**Solution**:
1. Increment version in `setup.py`
2. Delete existing tag if needed:
   ```bash
   git tag -d v0.4.0
   git push origin :refs/tags/v0.4.0
   ```
3. Create new release with new version

### Issue: Tests pass locally but fail in CI

**Solution**:
1. Check Python version differences
2. Ensure all dependencies are in `requirements.txt`
3. Check for platform-specific issues (Windows/macOS)

---

## Additional Resources

- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Semantic Versioning](https://semver.org/)
- [Python Packaging Guide](https://packaging.python.org/)

---

## Support

For issues with deployment:
1. Check Actions tab for error logs
2. Review this guide's troubleshooting section
3. Open an issue on GitHub: https://github.com/maxim75/m-hass-api/issues