# Directory Structure & Setup Guide

## Project Layout

```
microgrid-stability-ml/
│
├── README.md                              # Project overview & quick start
├── ARCHITECTURE.md                        # Technical methodology
├── CONTRIBUTING.md                        # Contribution guidelines
├── LICENSE                                # MIT License
├── requirements.txt                       # Python dependencies
├── setup.py                               # Package installation
├── .gitignore                             # Git configuration
│
├── src/                                   # Main package
│   ├── __init__.py
│   │
│   ├── dataset_generation/
│   │   ├── __init__.py
│   │   └── synthetic_microgrid.py         # SyntheticMicrogridGenerator
│   │                                       # (from: Main_CODE.py)
│   │
│   ├── feature_engineering/
│   │   ├── __init__.py
│   │   └── feature_extractor.py           # FeatureExtractor
│   │                                       # (extract from main_code_ml_final_edit.py)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── classical_models.py            # All 12+ classical ML models
│   │   │                                   # (from: main_code_ml_final_edit.py)
│   │   │
│   │   ├── deep_learning.py               # ANN, LSTM, CNN models
│   │   │                                   # (from: hybrid_federated_microgrid__1_.py)
│   │   │
│   │   ├── ensemble_models.py             # Stacking, voting ensembles
│   │   │                                   # (from: hybrid_federated_microgrid__1_.py)
│   │   │
│   │   └── federated_learning.py          # FedAvg implementation
│   │                                       # (from: federated_avg_standalone.py)
│   │
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── pandapower_ref.py              # PandapowerValidator
│   │   │                                   # (reference model generation)
│   │   │
│   │   └── evaluation_metrics.py          # Metric computation & plotting
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py                      # Global configuration
│       └── logger.py                      # Logging utilities
│
├── notebooks/                             # Jupyter notebooks (analysis)
│   ├── 01_dataset_exploration.ipynb
│   ├── 02_feature_analysis.ipynb
│   ├── 03_model_comparison.ipynb
│   └── 04_federated_learning.ipynb
│
├── data/                                  # Data directory
│   ├── raw/                               # Raw output from generator
│   │   └── .gitkeep                       # (placeholder, actual CSV added locally)
│   │
│   ├── processed/                         # Windowed & feature-engineered
│   │   └── .gitkeep
│   │
│   └── validation/                        # Pandapower reference datasets
│       └── .gitkeep
│
├── results/                               # Output directory
│   ├── models/                            # Trained model checkpoints
│   │   └── .gitkeep                       # (joblib .pkl, .h5 files)
│   │
│   ├── plots/                             # Generated visualizations
│   │   └── .gitkeep                       # (PNG, JPG outputs)
│   │
│   └── metrics/                           # Evaluation reports
│       └── .gitkeep                       # (JSON, CSV files)
│
├── docs/                                  # Additional documentation
│   ├── METHODOLOGY.md                     # Mathematical formulations
│   ├── API.md                             # API reference
│   ├── DEPLOYMENT.md                      # Edge deployment guide
│   └── TROUBLESHOOTING.md                 # Common issues & solutions
│
├── tests/                                 # Unit tests
│   ├── __init__.py
│   ├── test_dataset.py                    # Dataset generation tests
│   ├── test_features.py                   # Feature engineering tests
│   ├── test_models.py                     # Model training tests
│   └── test_validation.py                 # Validation tests
│
└── .github/                               # GitHub configuration (optional)
    ├── workflows/
    │   ├── tests.yml                      # CI/CD pipeline
    │   └── lint.yml                       # Code quality checks
    │
    └── ISSUE_TEMPLATE/
        ├── bug_report.md
        └── feature_request.md
```

---

## Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/user/microgrid-stability-ml.git
cd microgrid-stability-ml
```

### 2. Create Virtual Environment

**Linux/macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell)**:
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
# Standard installation (for users)
pip install -r requirements.txt

# Development installation (for contributors)
pip install -e ".[dev,notebooks]"
```

### 4. Verify Installation

```python
python -c "import src; print('✓ Package imported successfully')"
pytest tests/ -v  # Run tests
```

---

## Data Management

### Raw Data (`data/raw/`)

**Purpose**: Store output from `SyntheticMicrogridGenerator`

**Format**: CSV with columns:
```
time, bus, voltage_pu, angle_deg, frequency, rocof, gen_p, load_p, tie_line_power, delay
0.0,  MG1, 1.02,      0.0,       50.0,      0.0,   15.0,  12.1,   0.5,            0.10
```

**Generation**:
```python
from src.dataset_generation import SyntheticMicrogridGenerator

generator = SyntheticMicrogridGenerator(sim_hours=24)
df = generator.run()
df.to_csv('data/raw/microgrid_synthetic_24h.csv', index=False)
```

**Size**: ~12,000 rows (24 hours @ 0.5s sampling)

### Processed Data (`data/processed/`)

**Purpose**: Store windowed, feature-engineered data ready for ML

**Contents**:
- `X_train.pkl` / `X_test.pkl` – Feature arrays
- `y_train.pkl` / `y_test.pkl` – Labels
- `scaler.pkl` – StandardScaler for normalization

**Generation**:
```python
from src.feature_engineering import FeatureExtractor
import joblib

extractor = FeatureExtractor(window_size=12, step_size=6)
X, y = extractor.fit_transform(df)

joblib.dump(X, 'data/processed/X.pkl')
joblib.dump(y, 'data/processed/y.pkl')
```

### Validation Data (`data/validation/`)

**Purpose**: Pandapower reference model scenarios

**Contents**:
- `pandapower_3000_scenarios.csv` – 3,000 load/DG/voltage combinations
- Columns: load_mw, dg_mw, grid_voltage_pu, stable

**Generation**:
```python
from src.validation import PandapowerValidator

validator = PandapowerValidator()
df_val = validator.generate_3000_scenarios()
df_val.to_csv('data/validation/pandapower_3000.csv', index=False)
```

---

## Model Artifacts (`results/models/`)

### Trained Models

**Format**: `joblib` pickle (scikit-learn) or `.h5` (Keras/TensorFlow)

**Naming Convention**:
```
{model_name}_{timestamp}.pkl
```

**Examples**:
- `random_forest_20260625_001.pkl` – Best Random Forest
- `xgboost_20260625_002.pkl` – Best XGBoost
- `lstm_medium_20260625_003.h5` – LSTM model

**Load & Predict**:
```python
import joblib

model = joblib.load('results/models/random_forest_best.pkl')
predictions = model.predict(X_test)
```

### Model Metadata (`results/models/metadata/`)

**JSON file** with each model's specs:
```json
{
  "model_name": "Random Forest",
  "timestamp": "2026-06-25",
  "hyperparameters": {
    "n_estimators": 50,
    "max_depth": 12,
    "random_state": 42
  },
  "performance": {
    "accuracy": 0.967,
    "precision": 0.990,
    "f1": 0.957,
    "roc_auc": 0.991
  },
  "training_time_seconds": 2.5,
  "model_path": "random_forest_20260625.pkl"
}
```

---

## Plots & Figures (`results/plots/`)

### Generated During Dataset Generation

1. **01_voltage.png** – Voltage magnitude over 24 hours (3 buses)
2. **02_frequency.png** – Frequency deviation over time
3. **03_angle_diff.png** – Inter-area angle differences
4. **04_rocof.png** – Rate of Change of Frequency
5. **05_tie_power.png** – Tie-line power exchanges
6. **06_imbalance.png** – Power imbalance (gen - load)
7. **07_phase_portrait.png** – Frequency vs angle phase portraits
8. **08_disturbances.png** – Timeline of injected disturbances
9. **09_correlation.png** – Feature correlation heatmap

### Generated During Model Benchmarking

10. **roc_curves.png** – ROC curves for all 12+ models
11. **confusion_matrices.png** – Confusion matrix heatmaps
12. **performance_heatmap.png** – Accuracy/Precision/F1-Score/AUC grid
13. **training_time_comparison.png** – Training time bar chart
14. **feature_importance.png** – Top features (Random Forest)

### Generated During Federated Learning

15. **federated_convergence.png** – Global accuracy & loss over rounds
16. **federated_client_loss.png** – Per-client loss trajectories

---

## Metrics & Reports (`results/metrics/`)

### Benchmark Results

**benchmark_results.csv**:
```csv
Model,Accuracy,Precision,Recall,F1-Score,ROC-AUC,MCC,Train_Time_s
Logistic Regression,0.965,0.979,0.931,0.955,0.991,0.926,0.2
Random Forest,0.967,0.990,0.926,0.957,0.991,0.931,2.5
XGBoost,0.962,0.987,0.917,0.951,0.991,0.922,1.2
...
```

### Federated Learning Report

**federated_report.json**:
```json
{
  "num_clients": 3,
  "num_rounds": 15,
  "global_accuracy": 0.943,
  "convergence": {
    "round_0": {"accuracy": 0.920, "loss": 0.106},
    "round_15": {"accuracy": 0.943, "loss": 0.041}
  },
  "client_sizes": [3500, 3400, 3100]
}
```

### Pandapower Validation

**pandapower_validation.json**:
```json
{
  "model": "xgboost",
  "test_scenarios": 3000,
  "accuracy": 0.939,
  "precision": 0.956,
  "recall": 0.908,
  "generalization_gap": 0.023
}
```

---

## Workflow Example

### Full Pipeline Execution

```bash
# 1. Generate synthetic dataset
python -c "
from src.dataset_generation import SyntheticMicrogridGenerator
import os

gen = SyntheticMicrogridGenerator(sim_hours=24)
df = gen.run()
os.makedirs('data/raw', exist_ok=True)
df.to_csv('data/raw/microgrid_24h.csv', index=False)
print('✓ Dataset generated')
"

# 2. Extract features
python -c "
import pandas as pd
from src.feature_engineering import FeatureExtractor
import joblib
import os

df = pd.read_csv('data/raw/microgrid_24h.csv')
ext = FeatureExtractor()
X, y = ext.fit_transform(df)
os.makedirs('data/processed', exist_ok=True)
joblib.dump((X, y), 'data/processed/features.pkl')
print('✓ Features extracted')
"

# 3. Train models
python -c "
import joblib
from sklearn.model_selection import train_test_split
from src.models import ModelBenchmark

X, y = joblib.load('data/processed/features.pkl')
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

bench = ModelBenchmark(X_train, y_train, X_test, y_test)
results = bench.train_all_models()
results.to_csv('results/metrics/benchmark.csv')
print('✓ Models trained')
"

# 4. Validate on Pandapower
python -c "
from src.validation import PandapowerValidator

validator = PandapowerValidator()
val_accuracy = validator.test_3000_scenarios()
print(f'✓ Validation accuracy: {val_accuracy:.4f}')
"
```

---

## Troubleshooting

### Memory Issues with Large Datasets

```python
# Process in chunks
import pandas as pd

for chunk in pd.read_csv('data/raw/large.csv', chunksize=10000):
    # Process chunk
    pass
```

### Missing Dependencies

```bash
pip install --upgrade scikit-learn tensorflow xgboost
```

### Model Not Found

```bash
ls results/models/
# If empty, run training first
python scripts/train_all_models.py
```

---

## Next Steps

1. **Review** [ARCHITECTURE.md](../ARCHITECTURE.md) for technical details
2. **Explore** `notebooks/` for analysis examples
3. **Run** tests: `pytest tests/ -v`
4. **Generate** your own dataset: See `Quick Start` in README.md
5. **Deploy** on edge: See `docs/DEPLOYMENT.md`

For questions, open an issue on GitHub.
