# Contributing to Microgrid Stability ML

Thank you for your interest in contributing! This document provides guidelines for reporting bugs, suggesting features, and submitting pull requests.

---

## Code of Conduct

This project operates under a Code of Conduct promoting professional, respectful collaboration. Please maintain constructive communication in all interactions.

---

## Reporting Bugs

### Before Submitting a Bug Report

- **Check existing issues**: Search [GitHub Issues](https://github.com/user/microgrid-stability-ml/issues) to avoid duplicates
- **Verify reproducibility**: Confirm the issue is consistent and document steps clearly
- **Gather information**: Include Python version, OS, installed packages, and minimal reproducible example

### Bug Report Format

```markdown
**Title**: [Concise description]

**Environment**:
- Python: X.X.X
- OS: [Windows/Linux/macOS]
- Installed packages: [output of `pip freeze` in affected environment]

**Steps to Reproduce**:
1. [Step 1]
2. [Step 2]
...

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Error Message/Traceback**:
```python
[Full traceback if applicable]
```

**Additional Context**:
[Any other relevant information]
```

---

## Feature Requests

### Before Submitting a Feature Request

- **Check existing discussions**: See if the feature has been proposed
- **Align with project scope**: Feature should relate to microgrid stability prediction or ML pipeline improvements

### Feature Request Format

```markdown
**Title**: [Feature description]

**Motivation**:
[Why this feature is needed. Use case example?]

**Proposed Implementation**:
[High-level approach or algorithm outline]

**Impact**:
[How would this improve the project? Performance gains? New capabilities?]

**Complexity**:
[Estimated effort: Low / Medium / High]

**References**:
[Any papers, discussions, or related work]
```

---

## Pull Request Process

### 1. Fork and Branch

```bash
git clone https://github.com/your-username/microgrid-stability-ml.git
cd microgrid-stability-ml
git checkout -b feature/your-feature-name
```

**Naming convention**:
- `feature/description` – new features
- `bugfix/description` – bug fixes
- `refactor/description` – refactoring
- `docs/description` – documentation updates

### 2. Make Changes

- **Follow PEP 8**: Use `black` and `flake8` for style compliance
  ```bash
  black src/
  flake8 src/ --max-line-length=120
  ```

- **Add tests**: New features must include unit tests
  ```bash
  pytest tests/ -v --cov=src
  ```

- **Update documentation**: If functionality changes, update README.md, ARCHITECTURE.md, or docstrings

- **Write clear commit messages**:
  ```
  [Type] Short description (50 chars max)
  
  Longer explanation (wrap at 72 chars). Explain *why*, not just *what*.
  
  - Bullet point 1
  - Bullet point 2
  
  Fixes #issue_number
  ```

  Examples:
  ```
  [feature] Add differential privacy to federated learning
  [bugfix] Fix feature scaling in classical models
  [docs] Update ARCHITECTURE.md with FedAvg algorithm
  ```

### 3. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Go to GitHub and create a Pull Request with:
- **Title**: Brief, descriptive
- **Description**: Reference the issue, explain changes, note any breaking changes
- **Checklist**:
  ```markdown
  - [ ] Tests pass locally (`pytest tests/`)
  - [ ] Code follows PEP 8 (`black` and `flake8`)
  - [ ] Documentation updated
  - [ ] No new warnings introduced
  - [ ] Commit messages are clear
  ```

### 4. Review Process

- Maintainers will review within 5-7 business days
- Respond to feedback constructively
- Keep the PR focused (avoid mixing unrelated changes)
- Once approved, maintainers will merge

---

## Development Workflow

### Setup Development Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev,notebooks]"
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_models.py -v

# With coverage report
pytest tests/ --cov=src --cov-report=html
```

### Code Quality Checks

```bash
# Format code
black src/

# Lint
flake8 src/ --max-line-length=120

# Type checking
mypy src/ --ignore-missing-imports
```

### Documentation

- Use Google-style docstrings:
  ```python
  def train_model(X, y, n_estimators=100):
      """Train a Random Forest classifier.
      
      Args:
          X: Feature matrix (n_samples, n_features)
          y: Target labels (n_samples,)
          n_estimators: Number of trees in the forest
          
      Returns:
          Trained RandomForestClassifier instance
          
      Raises:
          ValueError: If X and y have mismatched sample counts
          
      Example:
          >>> X, y = load_data()
          >>> model = train_model(X, y, n_estimators=50)
      """
  ```

---

## Area-Specific Guidelines

### Dataset Generation (`src/dataset_generation/`)

- Maintain physics accuracy (validate against known ODE solutions)
- Document all parameters with physical units (MHz, MW, pu, etc.)
- Add numerical stability checks (e.g., clip voltage to [0.8, 1.2] pu)

### Feature Engineering (`src/feature_engineering/`)

- Include correlation analysis for new features
- Document feature scaling choices
- Ensure windowing preserves temporal causality (no future leakage)

### Models (`src/models/`)

- Specify all hyperparameters in config or docstrings
- Include train/test split strategy
- Log convergence metrics (loss, accuracy curves)

### Validation (`src/validation/`)

- Test on multiple grid topologies
- Report generalization metrics (e.g., accuracy on Pandapower)
- Include error analysis (confusion matrices, ROC curves)

---

## Documentation Standards

All Python files should include:
- **Module docstring**: 2-3 line summary
- **Function docstrings**: Google style (Args, Returns, Raises, Example)
- **Complex logic comments**: Explain *why*, not just *what*
- **Type hints**: Use for all function signatures

Example:
```python
"""Feature engineering pipeline for microgrid stability data.

This module provides tools for extracting statistical features from
windowed time-series data (voltage, frequency, angle, power).
"""

from typing import Tuple
import numpy as np
import pandas as pd

def extract_statistical_features(
    X: np.ndarray,
    window_size: int = 12
) -> Tuple[np.ndarray, np.ndarray]:
    """Extract mean, std, min, max, range, and slope features.
    
    Args:
        X: Input array of shape (n_samples, window_size, n_features)
        window_size: Length of time window (timesteps)
        
    Returns:
        Tuple of (features, windows) where:
        - features: shape (n_windows, n_features * 6)
        - windows: corresponding window indices
        
    Raises:
        ValueError: If window_size > X.shape[1]
    """
```

---

## Performance Benchmarks

When submitting performance improvements:

1. **Baseline**: Report metrics on original code
2. **Improvement**: Report metrics with your changes
3. **Reproducibility**: Include seed, hardware, dataset size
4. **Statistical significance**: Report confidence intervals or run multiple seeds

Example:
```
Hardware: Intel Core i7 (8 cores), 16 GB RAM
Dataset: 10,000 synthetic windows, seed=42

Baseline (Random Forest, n_estimators=50):
  - Accuracy: 96.7% ± 0.3%
  - Training time: 2.5s

Optimized (Random Forest, n_estimators=40, max_depth=10):
  - Accuracy: 96.5% ± 0.2% (−0.2% trade-off)
  - Training time: 1.8s (28% speedup)
```

---

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md (list of all contributors)
- GitHub Acknowledgments
- Release notes for significant contributions

---

## Questions or Discussions?

- **Open an Issue** with the `question` label
- **Start a Discussion** for general ideas or feedback
- **Email** for sensitive topics

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License (same as the project).

---

Thank you for contributing to advancing microgrid stability analysis!
