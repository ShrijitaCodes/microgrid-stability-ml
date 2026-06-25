# Quick Start Guide

Get up and running in **5 minutes** ⚡

---

## 1. Installation

```bash
# Clone repo
git clone https://github.com/user/microgrid-stability-ml.git
cd microgrid-stability-ml

# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install
pip install -r requirements.txt
```

**Verify**: 
```bash
python -c "import src; print('✓ Ready!')"
```

---

## 2. Generate Synthetic Dataset (2 min)

```python
from src.dataset_generation import SyntheticMicrogridGenerator
import os

os.makedirs('data/raw', exist_ok=True)

# Generate 24-hour dataset with 3 microgrids
generator = SyntheticMicrogridGenerator(
    sim_hours=24,           # simulation duration
    output_sampling_interval=0.5,  # 0.5 seconds
    random_seed=42
)

df = generator.run()
print(f"Generated: {df.shape[0]} timesteps across {df['bus'].nunique()} microgrids")

# Save to CSV
df.to_csv('data/raw/microgrid_dataset.csv', index=False)
print("✓ Saved to: data/raw/microgrid_dataset.csv")
```

**Output**: 12,000+ timesteps, 9 features per bus
- `voltage_pu`, `frequency`, `angle_deg`, `rocof`
- `gen_p`, `load_p`, `tie_line_power`, `delay`

---

## 3. Extract Features (1 min)

```python
import pandas as pd
from src.feature_engineering import FeatureExtractor
import joblib
import os

# Load raw data
df = pd.read_csv('data/raw/microgrid_dataset.csv')

# Extract windowed features
extractor = FeatureExtractor(
    window_size=12,      # 6 seconds @ 0.5s sampling
    step_size=6          # 50% overlap
)

X, y = extractor.fit_transform(df)
print(f"Features: {X.shape} | Labels: {y.shape}")
print(f"Classes: {y.sum()} stable, {len(y) - y.sum()} unstable")

# Save
os.makedirs('data/processed', exist_ok=True)
joblib.dump((X, y), 'data/processed/features.pkl')
print("✓ Features saved")
```

**Output**: X shape = (num_windows, 2100+), y = binary labels

---

## 4. Train Models (30 sec)

```python
import joblib
from sklearn.model_selection import train_test_split
from src.models import ModelBenchmark

# Load processed data
X, y = joblib.load('data/processed/features.pkl')

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# Train all models
benchmark = ModelBenchmark(
    X_train, y_train, 
    X_test, y_test,
    random_state=42
)

results_df = benchmark.train_all_models()

# Display results
print(results_df[['Model', 'Accuracy', 'F1-Score', 'ROC-AUC']].to_string())

# Save results
import os
os.makedirs('results/metrics', exist_ok=True)
results_df.to_csv('results/metrics/benchmark_results.csv', index=False)
print("✓ Results saved to: results/metrics/benchmark_results.csv")
```

**Expected Output**:
```
Model                Accuracy  F1-Score  ROC-AUC
Random Forest           0.967     0.957    0.991
Logistic Regression     0.965     0.955    0.991
XGBoost                 0.962     0.951    0.991
...
```

---

## 5. Make Predictions (Real-Time)

```python
import joblib
import numpy as np

# Load trained model
model = joblib.load('results/models/random_forest_best.pkl')

# New observation (2,100 features)
new_features = np.random.randn(1, 2100)

# Predict
prediction = model.predict(new_features)  # 0 or 1
probability = model.predict_proba(new_features)

is_stable = prediction[0]
confidence = probability[0, is_stable]

print(f"Prediction: {'STABLE' if is_stable else 'UNSTABLE'}")
print(f"Confidence: {confidence:.2%}")
```

---

## 6. Validate on Pandapower (2 min)

```python
from src.validation import PandapowerValidator
import joblib

# Load trained model
model = joblib.load('results/models/random_forest_best.pkl')

# Create validator
validator = PandapowerValidator(model)

# Test on 3,000 grid scenarios
generalization_accuracy = validator.test_3000_scenarios()
print(f"Pandapower Generalization Accuracy: {generalization_accuracy:.4f}")
```

---

## Key Results

**Best Model**: Random Forest
- **Accuracy**: 96.7%
- **Precision**: 99.0%
- **Recall**: 92.6%
- **ROC-AUC**: 0.991
- **Training**: 2.5 seconds
- **Inference**: 0.5 ms per sample ← ready for edge deployment

---

## Federated Learning (Optional - 3 min)

Simulate privacy-preserving training across 3 microgrids:

```python
from src.models import FederatedLearning

# Split data per microgrid
mg1_data = (X_train_mg1, y_train_mg1)
mg2_data = (X_train_mg2, y_train_mg2)
mg3_data = (X_train_mg3, y_train_mg3)

# Train federally
fl = FederatedLearning(num_clients=3, num_rounds=15)
history = fl.train([mg1_data, mg2_data, mg3_data])

# Evaluate global model
global_accuracy = fl.evaluate(X_test, y_test)
print(f"Global Accuracy (Privacy-Preserving): {global_accuracy:.4f}")
```

**Result**: 94.3% accuracy with **zero data sharing**

---

## Next Steps

1. **Explore Notebooks**: See `notebooks/` directory
   ```bash
   jupyter notebook notebooks/01_dataset_exploration.ipynb
   ```

2. **Review Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)

3. **Deploy on Edge**: See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

4. **Run Tests**:
   ```bash
   pytest tests/ -v
   ```

5. **Contribute**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Common Commands

```bash
# Run all tests
pytest tests/ -v --cov=src

# Format code
black src/

# Check code quality
flake8 src/ --max-line-length=120

# Generate dataset
python -c "from src.dataset_generation import SyntheticMicrogridGenerator; SyntheticMicrogridGenerator().run().to_csv('data/raw/data.csv')"

# List trained models
ls results/models/

# View results
cat results/metrics/benchmark_results.csv
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'src'` | Install: `pip install -e .` |
| `MemoryError` | Use subset: `df.iloc[:1000]` or process in chunks |
| `No pandas module` | Install: `pip install -r requirements.txt` |
| Slow training | Reduce samples: `X_train[:5000]` |

---

## Questions?

📖 **Read**: [ARCHITECTURE.md](ARCHITECTURE.md) for technical details  
💬 **Issue**: Open GitHub issue for bugs/features  
📧 **Email**: Contact project maintainers

---

**Estimated Time**: ~10 minutes end-to-end  
**Hardware**: CPU only (GPU optional for deep learning)

Happy predicting! 🎯
