# GitHub Repository Setup Guide

Follow these steps to create your GitHub repository and upload this project.

---

## Step 1: Create GitHub Repository

### On GitHub Website

1. Go to [github.com/new](https://github.com/new)
2. **Repository name**: `microgrid-stability-ml`
3. **Description**: 
   ```
   Machine Learning for Small-Signal Stability Prediction in Interconnected Microgrids
   ```
4. **Visibility**: Public (for recruitment visibility)
5. **Initialize with**:
   - ✓ Add a README file (we'll replace it)
   - ✓ Add .gitignore for Python (we'll replace it)
   - ✓ Choose license: MIT
6. Click **Create repository**

---

## Step 2: Clone & Setup Locally

```bash
# Clone your new repo
git clone https://github.com/YOUR_USERNAME/microgrid-stability-ml.git
cd microgrid-stability-ml

# Configure git (optional but recommended)
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

---

## Step 3: Copy Project Files

Copy all files from the outputs folder to your local repository:

```bash
# From the outputs directory, copy to your repo
cp README.md microgrid-stability-ml/
cp ARCHITECTURE.md microgrid-stability-ml/
cp CONTRIBUTING.md microgrid-stability-ml/
cp QUICKSTART.md microgrid-stability-ml/
cp DIRECTORY_STRUCTURE.md microgrid-stability-ml/
cp requirements.txt microgrid-stability-ml/
cp setup.py microgrid-stability-ml/
cp LICENSE microgrid-stability-ml/
cp .gitignore microgrid-stability-ml/

# Copy Python source files
cp Main_CODE.py microgrid-stability-ml/
cp main_code_ml_final_edit.py microgrid-stability-ml/
cp federated_avg_standalone.py microgrid-stability-ml/
cp hybrid_federated_microgrid__1_.py microgrid-stability-ml/

# Create directory structure
cd microgrid-stability-ml
mkdir -p src/{dataset_generation,feature_engineering,models,validation,utils}
mkdir -p data/{raw,processed,validation}
mkdir -p results/{models,plots,metrics}
mkdir -p notebooks
mkdir -p tests
mkdir -p docs

# Create __init__.py files for Python packages
touch src/__init__.py
touch src/dataset_generation/__init__.py
touch src/feature_engineering/__init__.py
touch src/models/__init__.py
touch src/validation/__init__.py
touch src/utils/__init__.py
touch tests/__init__.py

# Create placeholder files to preserve directory structure
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch data/validation/.gitkeep
touch results/models/.gitkeep
touch results/plots/.gitkeep
touch results/metrics/.gitkeep
```

---

## Step 4: Organize Python Files

Move the Python source files to appropriate locations:

```bash
# Dataset generation
mv Main_CODE.py src/dataset_generation/synthetic_microgrid.py

# ML models (main code)
mv main_code_ml_final_edit.py src/models/classical_models.py

# Deep learning & ensemble
mv hybrid_federated_microgrid__1_.py src/models/ensemble_and_deep_learning.py

# Federated learning
mv federated_avg_standalone.py src/models/federated_learning.py

# Create placeholder utility modules
touch src/utils/config.py
touch src/utils/logger.py
touch src/validation/evaluation_metrics.py
touch src/validation/pandapower_ref.py
```

---

## Step 5: Create .github Workflows (Optional but Recommended)

For CI/CD automation:

```bash
mkdir -p .github/workflows
mkdir -p .github/ISSUE_TEMPLATE
```

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest tests/ -v --cov=src
    
    - name: Lint
      run: |
        pip install black flake8
        black --check src/
        flake8 src/ --max-line-length=120
```

Create `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug Report
about: Report a bug
title: '[BUG] '
labels: 'bug'
---

## Description
[Brief description of the bug]

## Steps to Reproduce
1. ...
2. ...

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- Python version:
- OS:
- Package versions: [output of `pip freeze`]

## Error Message
```
[Traceback if applicable]
```
```

---

## Step 6: Commit & Push

```bash
# Navigate to your repo
cd microgrid-stability-ml

# Stage all files
git add .

# Commit
git commit -m "Initial project setup: ML pipeline for microgrid stability"

# Push to GitHub
git push origin main
```

---

## Step 7: Add CSV File Later

Once you have your generated dataset:

```bash
# Add the CSV file
cp FINAL_microgrid_dataset_0.5s_GENERATED.csv data/raw/

# (Alternative) Track CSV with Git LFS for large files
git lfs install
git lfs track "*.csv"
git add .gitattributes
git add data/raw/FINAL_microgrid_dataset_0.5s_GENERATED.csv
git commit -m "Add synthetic dataset"
git push origin main
```

**Note**: If CSV is >100MB, consider using [Git LFS](https://git-lfs.github.com/) or upload separately.

---

## Step 8: Configure GitHub Repository Settings

### On GitHub Website

1. **Go to**: Settings → General
   - ✓ Require status checks to pass before merging (optional)
   - ✓ Dismiss stale pull request approvals (optional)

2. **Go to**: Settings → Branches
   - Add rule for `main` branch:
     - ✓ Require pull request reviews
     - ✓ Require status checks to pass

3. **Go to**: Settings → Manage Access
   - Add collaborators if needed

4. **Go to**: Pages
   - Source: Deploy from a branch
   - Branch: `gh-pages` (for auto-generated docs)

---

## Step 9: Add Topics & Repository Details

1. **Go to**: About (gear icon on main page)
2. **Add Topics**: 
   - `machine-learning`
   - `microgrids`
   - `power-systems`
   - `stability-analysis`
   - `federated-learning`
3. **Add Description**:
   ```
   ML/DL pipeline for predicting small-signal stability in interconnected microgrids
   with support for privacy-preserving federated learning.
   ```

---

## Step 10: Create Initial Release (Optional)

```bash
git tag -a v1.0.0 -m "Initial release: Full ML pipeline"
git push origin v1.0.0
```

Then on GitHub:
- Go to Releases
- Click "Create a release"
- Tag: v1.0.0
- Title: "v1.0.0 - Initial Release"
- Description: "First stable release with complete ML pipeline"

---

## File Checklist

Before pushing, verify all files are present:

```
✓ README.md
✓ ARCHITECTURE.md
✓ CONTRIBUTING.md
✓ QUICKSTART.md
✓ DIRECTORY_STRUCTURE.md
✓ LICENSE
✓ requirements.txt
✓ setup.py
✓ .gitignore

✓ src/
  ✓ __init__.py
  ✓ dataset_generation/synthetic_microgrid.py
  ✓ models/classical_models.py
  ✓ models/ensemble_and_deep_learning.py
  ✓ models/federated_learning.py
  ✓ utils/config.py
  ✓ utils/logger.py

✓ data/raw/.gitkeep
✓ data/processed/.gitkeep
✓ data/validation/.gitkeep

✓ results/models/.gitkeep
✓ results/plots/.gitkeep
✓ results/metrics/.gitkeep

✓ .github/workflows/tests.yml (optional)
✓ .github/ISSUE_TEMPLATE/bug_report.md (optional)
```

---

## Verifying Repository

After pushing, verify on GitHub:

1. ✓ All files visible in browser
2. ✓ README renders correctly
3. ✓ 9 Python files in `src/`
4. ✓ Proper .gitignore (no `__pycache__`, `.pyc`, etc.)
5. ✓ License file present (MIT)
6. ✓ Topics visible

---

## Optional: Add Badges to README

Once you have CI/CD and test coverage, add badges at the top of README.md:

```markdown
[![Tests](https://github.com/YOUR_USERNAME/microgrid-stability-ml/workflows/Tests/badge.svg)](https://github.com/YOUR_USERNAME/microgrid-stability-ml/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
```

---

## Repository Structure After Setup

```
GitHub Repository
├── README.md
├── ARCHITECTURE.md
├── CONTRIBUTING.md
├── QUICKSTART.md
├── DIRECTORY_STRUCTURE.md
├── LICENSE
├── requirements.txt
├── setup.py
├── .gitignore
├── .github/
│   ├── workflows/tests.yml
│   └── ISSUE_TEMPLATE/
├── src/
│   ├── __init__.py
│   ├── dataset_generation/
│   ├── models/
│   ├── validation/
│   └── utils/
├── data/
│   ├── raw/
│   ├── processed/
│   └── validation/
├── results/
│   ├── models/
│   ├── plots/
│   └── metrics/
├── notebooks/
└── tests/
```

---

## Next Steps After Repository Creation

1. **Share the repository**: Update your portfolio/CV with GitHub link
2. **Add documentation**: Create GitHub Wiki if needed
3. **Enable discussions**: For community engagement
4. **Create project board**: For tracking development
5. **Monitor stars**: Build visibility through collaborations

---

## Quick Push Command Summary

```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/microgrid-stability-ml.git
cd microgrid-stability-ml

# Copy all files
# (as described in Step 3)

# Commit and push
git add .
git commit -m "Initial project setup: Complete ML pipeline"
git push origin main

# Verify on GitHub
# Browse: https://github.com/YOUR_USERNAME/microgrid-stability-ml
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Permission denied` when pushing | Check SSH keys: `ssh -T git@github.com` |
| Merge conflicts | Fetch latest: `git fetch origin` then `git pull` |
| Large file error | Use Git LFS for files >100MB |
| Default branch mismatch | Ensure local branch matches GitHub default |

---

## GitHub Repository URL

Once created, your repository will be available at:
```
https://github.com/YOUR_USERNAME/microgrid-stability-ml
```

**Share this URL with**:
- Employers/recruiters
- Collaborators
- Academic advisors
- Project portfolio

---

**Congratulations! Your GitHub repository is now ready for the world to see.** 🎉

For questions about repository setup, see [GitHub Help](https://docs.github.com).
