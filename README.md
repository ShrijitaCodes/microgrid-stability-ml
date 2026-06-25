# Stability Analysis of Interconnected Microgrids

**Machine Learning for Small-Signal Stability Prediction in Grid-Connected Microgrids**

---

## Overview

This project develops a data-driven machine learning pipeline to predict small-signal stability in interconnected microgrids. The system uses physics-informed synthetic dataset generation combined with classical and deep learning models to enable real-time stability assessment with minimal computational overhead.

### Key Features

- **Physics-Informed Dataset Generation**: First-order frequency dynamics model for 3-interconnected microgrids
- **Comprehensive ML/DL Comparison**: 12+ algorithms (Logistic Regression, SVM, Random Forest, XGBoost, Neural Networks, etc.)
- **Federated Learning Support**: Privacy-preserving FedAvg implementation for distributed microgrid networks
- **Production-Ready Validation**: Pandapower reference model with 3,000+ test scenarios
- **Edge Deployment**: Optimized models for embedded systems (Raspberry Pi, industrial gateways)

### Performance Highlights

- **Best Model**: Random Forest with **96.7% accuracy**, **0.991 ROC-AUC**, **2.5s training time**
- **Federated Learning**: 94.3% global accuracy with full data privacy across 3 microgrids
- **Generalization**: 93.9% accuracy on out-of-distribution Pandapower validation set

---

## Project Structure

```
.
├── README.md                          # This file
├── ARCHITECTURE.md                    # Technical architecture & methodology
├── CONTRIBUTING.md                    # Contribution guidelines
├── requirements.txt                   # Python dependencies
├── setup.py                          # Package configuration
├── .gitignore                        # Git configuration
│
├── src/
│   ├── __init__.py
│   ├── dataset_generation/
│   │   ├── __init__.py
│   │   └── synthetic_microgrid.py    # Synthetic dataset generator (12,000 windows)
│   │
│   ├── feature_engineering/
│   │   ├── __init__.py
│   │   └── feature_extractor.py      # 2,100+ statistical feature computation
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── classical_models.py       # Logistic Regression, SVM, Random Forest, etc.
│   │   ├── deep_learning.py          # Neural Networks (small, medium configs)
│   │   ├── ensemble_models.py        # Stacking, Hybrid ensembles
│   │   └── federated_learning.py     # FedAvg algorithm implementation
│   │
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── pandapower_ref.py         # Pandapower reference model
│   │   └── evaluation_metrics.py      # Comprehensive evaluation suite
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py                 # Global configuration
│       └── logger.py                 # Logging utilities
│
├── notebooks/
│   ├── 01_dataset_exploration.ipynb     # Data analysis & visualization
│   ├── 02_feature_analysis.ipynb        # Feature correlation & selection
│   ├── 03_model_comparison.ipynb        # Benchmark results
│   └── 04_federated_learning.ipynb      # Federated training dynamics
│
├── data/
│   ├── raw/                          # Raw output from synthetic generator
│   ├── processed/                    # Windowed & feature-engineered data
│   └── validation/                   # Pandapower reference datasets
│
├── results/
│   ├── models/                       # Trained model checkpoints
│   ├── plots/                        # Generated figures (voltage, frequency, etc.)
│   └── metrics/                      # Evaluation reports (JSON/CSV)
│
├── docs/
│   ├── METHODOLOGY.md                # Mathematical formulations
│   ├── API.md                        # API reference
│   └── DEPLOYMENT.md                 # Edge deployment guide
│
└── tests/
    ├── __init__.py
    ├── test_dataset.py               # Dataset generation tests
    ├── test_features.py              # Feature engineering tests
    └── test_models.py                # Model training tests
```

---

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/user/microgrid-stability-ml.git
cd microgrid-stability-ml

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### 2. Generate Synthetic Dataset

```python
from src.dataset_generation import SyntheticMicrogridGenerator

generator = SyntheticMicrogridGenerator(
    sim_hours=24,
    output_sampling_interval=0.5,  # seconds
    random_seed=42
)

df = generator.run()  # Returns 12,000+ timesteps
df.to_csv('data/raw/microgrid_synthetic.csv', index=False)
```

### 3. Train Models

```python
from src.models import ModelBenchmark
from src.feature_engineering import FeatureExtractor

# Load and preprocess data
df = pd.read_csv('data/raw/microgrid_synthetic.csv')
extractor = FeatureExtractor()
X, y = extractor.fit_transform(df)

# Train all models
benchmark = ModelBenchmark(X, y, random_state=42)
results = benchmark.train_all_models()

# View results
print(results.to_string())
```

### 4. Federated Learning

```python
from src.models import FederatedLearning

fl_trainer = FederatedLearning(num_clients=3, num_rounds=15)
fl_trainer.train(client_data_dict)
global_accuracy = fl_trainer.evaluate()
```

### 5. Validation on Pandapower

```python
from src.validation import PandapowerValidator

validator = PandapowerValidator(model=trained_model)
val_accuracy = validator.test_3000_scenarios()
print(f"Generalization Accuracy: {val_accuracy:.4f}")
```

---

## Dataset

### Synthetic Data Characteristics

| Property | Value |
|----------|-------|
| Output Timesteps | 12,000 (24 hours @ 0.5s sampling) |
| Microgrids | 3 (diesel, solar, hybrid) |
| Feature Dimensionality | 2,100+ |
| Class Distribution | 62% stable / 38% unstable |
| Disturbance Types | Load steps, solar dips, wind gusts, tie-line weaknesses |

### Data Format

```csv
time,bus,voltage_pu,angle_deg,frequency,rocof,gen_p,load_p,tie_line_power,delay
0.0,MG1,1.02,0.0,50.0,0.0,15.0,12.1,0.5,0.10
0.5,MG1,1.019,0.05,49.98,-0.04,15.1,12.2,0.4,0.11
...
```

---

## Model Performance

### Classical & Deep Learning Benchmark (Test Set, 2,000 samples)

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | MCC | Train Time |
|-------|----------|-----------|--------|----------|---------|-----|------------|
| **Random Forest** | **0.967** | **0.990** | **0.926** | **0.957** | **0.991** | **0.931** | 2.5s |
| Logistic Regression | 0.965 | 0.979 | 0.931 | 0.955 | 0.991 | 0.926 | 0.2s |
| XGBoost | 0.962 | 0.987 | 0.917 | 0.951 | 0.991 | 0.922 | 1.2s |
| SVM (RBF) | 0.963 | 0.977 | 0.930 | 0.953 | 0.989 | 0.923 | 8.3s |
| Gradient Boosting | 0.963 | 0.986 | 0.919 | 0.951 | 0.991 | 0.922 | 26.0s |
| ANN (Medium) | 0.962 | 0.975 | 0.928 | 0.951 | 0.989 | 0.921 | 4.1s |
| Decision Tree | 0.955 | 0.960 | 0.926 | 0.942 | 0.965 | 0.905 | 0.8s |
| KNN (k=10) | 0.957 | 0.975 | 0.917 | 0.945 | 0.975 | 0.911 | 0.1s |
| Naive Bayes | 0.962 | 0.965 | 0.939 | 0.952 | 0.987 | 0.921 | 0.1s |
| AdaBoost | 0.961 | 0.987 | 0.915 | 0.950 | 0.991 | 0.920 | 3.2s |

### Federated Learning Results (3 Microgrids, 15 Communication Rounds)

- **Global Test Accuracy**: 94.3%
- **Local Loss Reduction**: 0.106 → 0.041 (61% improvement)
- **Privacy**: Full data isolation—raw telemetry never leaves client

### Pandapower Validation (3,000 Out-of-Distribution Scenarios)

- **XGBoost Generalization Accuracy**: 93.9%
- **Robustness**: Consistent performance across grid topologies and loading conditions

---

## Technical Methodology

### System Model

Each microgrid is modeled using first-order frequency dynamics:

```
df_i/dt = (P_gen,i - P_load,i - P_tie,i) / (2*H_i) - D_i*(f_i - f_nom)
dδ_i/dt = 2π*(f_i - f_nom)
P_tie,i = Σ_j (V_i * V_j / X_ij) * sin(δ_i - δ_j)
```

### Feature Engineering

- **Per-window temporal features**: mean, std, min, max, range, slope
- **Inter-area metrics**: angle differences, frequency deviations
- **Aggregate metrics**: total power imbalance, average communication delay
- **Total**: 2,100+ features per window (3 buses × 21 base features × 30+ derived features)

### Training Pipeline

1. **Dataset Generation**: 12,000 windows from physics-informed simulation
2. **Windowing**: 12-step input windows, 12-step future horizon (6s observations)
3. **Labeling**: Composite stability score (voltage + frequency + angle + power balance) thresholded at 60th percentile
4. **Preprocessing**: StandardScaler normalization (classical ML), no scaling (tree-based)
5. **Train/Test Split**: 70% / 30% (stratified)
6. **Validation**: Pandapower reference model with 3,000 grid scenarios

For more details, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Usage Examples

### Example 1: End-to-End Pipeline

```python
import pandas as pd
from src.dataset_generation import SyntheticMicrogridGenerator
from src.feature_engineering import FeatureExtractor
from src.models import ModelBenchmark
from sklearn.model_selection import train_test_split

# Generate dataset
print("Generating synthetic dataset...")
generator = SyntheticMicrogridGenerator(sim_hours=24)
df_raw = generator.run()

# Extract features
print("Engineering features...")
extractor = FeatureExtractor(window_size=12, step_size=6)
X, y = extractor.fit_transform(df_raw)

# Train models
print("Training models...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
benchmark = ModelBenchmark(X_train, y_train, X_test, y_test)
results_df = benchmark.train_all_models()

# Save results
results_df.to_csv('results/metrics/benchmark_results.csv', index=False)
print("Complete! See results/metrics/benchmark_results.csv")
```

### Example 2: Inference with Trained Model

```python
import joblib
import numpy as np

# Load trained model
model = joblib.load('results/models/random_forest_best.pkl')

# New observation (2,100 features from feature extractor)
new_features = np.random.randn(1, 2100)

# Predict stability
prediction = model.predict(new_features)  # 0 = unstable, 1 = stable
probability = model.predict_proba(new_features)

print(f"Prediction: {'STABLE' if prediction[0] else 'UNSTABLE'}")
print(f"Confidence: {probability[0, prediction[0]]:.2%}")
```

### Example 3: Federated Training Simulation

```python
from src.models import FederatedLearning

# Prepare per-microgrid data splits
mg1_data = (X_train_mg1, y_train_mg1)
mg2_data = (X_train_mg2, y_train_mg2)
mg3_data = (X_train_mg3, y_train_mg3)

# Initialize federated trainer
fl = FederatedLearning(
    num_clients=3,
    num_rounds=15,
    epochs_per_round=5
)

# Train globally across microgrids
history = fl.train([mg1_data, mg2_data, mg3_data])

# Evaluate
global_accuracy = fl.evaluate(X_test, y_test)
print(f"Federated Global Accuracy: {global_accuracy:.4f}")
```

---

## Deployment

### Edge Device Deployment (Raspberry Pi / Industrial Gateway)

```python
import joblib
import numpy as np

# Load quantized model (smaller footprint)
model = joblib.load('results/models/random_forest_quantized.pkl')

# Real-time inference loop
while True:
    # Acquire telemetry from MQTT/sensor
    voltage, frequency, angle, power = acquire_telemetry()
    
    # Extract features
    features = extract_features_realtime(voltage, frequency, angle, power)
    
    # Predict
    is_stable = model.predict([features])[0]
    
    # Trigger action if unstable
    if not is_stable:
        trigger_protection_scheme()
```

For deployment details, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## Key Publications & References

- **Microgrid Stability**: Li & Shahidehpour (2019). "Small-Signal Modeling and Stability Analysis of Hybrid AC/DC Microgrids."
- **ML for Power Systems**: Sheta et al. (2025). "Machine-Learning-Based Adaptive Settings of Directional Overcurrent Relays."
- **Federated Learning**: McMahan et al. (2017). "Communication-Efficient Learning of Deep Networks from Decentralized Data."

Full reference list in [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Contributing

This is a research project. For bug reports, feature requests, or pull requests, see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT License – See LICENSE file for details.

---

## Contact & Attribution

**Project**: Stability Analysis of Interconnected Microgrids  
**Institution**: Department of Power Engineering, Jadavpur University  
**Period**: 2026  
**Supervisor**: Prof. Niladri Chakraborty

For questions or collaboration inquiries, please open an issue on GitHub.
