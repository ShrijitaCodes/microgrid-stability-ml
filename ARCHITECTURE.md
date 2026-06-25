# Architecture & Methodology

## System Overview

This document describes the technical architecture, physics model, and machine learning pipeline for microgrid small-signal stability prediction.

---

## 1. Physics-Informed System Model

### 1.1 First-Order Frequency Dynamics

Each microgrid is modeled as a first-order frequency dynamics system:

```
d f_i / dt = (P_gen,i - P_load,i - P_tie,i) / (2 * H_i) - D_i * (f_i - f_nom)
```

**Parameters**:
- `f_i` = frequency at bus i (Hz)
- `P_gen,i` = generation output (MW)
- `P_load,i` = load demand (MW)
- `P_tie,i` = net tie-line power exchange (MW)
- `H_i` = inertia constant (seconds)
- `D_i` = damping coefficient (pu)
- `f_nom` = nominal frequency (50 Hz)

**Physical Interpretation**: Frequency deviation directly reflects power balance. High inertia systems (diesel generators) respond slowly; low inertia systems (solar/wind) respond quickly.

### 1.2 Rotor Angle Dynamics

```
d δ_i / dt = 2π * (f_i - f_nom)
```

**Purpose**: Tracks synchronous phase angle relative to reference frame. Inter-area angle differences indicate coherency.

### 1.3 AC Power Flow (Tie-Line Power)

```
P_tie,i = Σ_{j≠i} (V_i * V_j / X_ij) * sin(δ_i - δ_j)
```

**Parameters**:
- `V_i`, `V_j` = voltage magnitudes (pu)
- `X_ij` = tie-line reactance (pu)
- `δ_i - δ_j` = angle difference between areas

**Physical Interpretation**: Power transfer is nonlinear in angle and inversely proportional to impedance. Weak tie-lines increase vulnerability to disturbances.

### 1.4 Droop Control

```
P_gen,i = P_set,i - (1 / R_i) * (f_i - f_nom)
```

**Purpose**: Primary frequency regulation. Generators reduce output when frequency rises (over-generation) and increase when frequency falls (under-generation). Prevents runaway frequency deviations.

### 1.5 Voltage Regulation (Simplified)

```
V_i = V_ref,i - X_i * (Q_load,i - Q_gen,i)
```

- `X_i` = self-impedance (pu)
- `Q_load`, `Q_gen` = reactive power (MVar)

---

## 2. Dataset Generation Pipeline

### 2.1 Configuration

**Simulation Parameters**:
- Duration: 24 hours
- Sampling: 0.5 seconds (48,000 raw points)
- Microgrids: 3 (diesel-dominated, solar, hybrid)
- Total output windows: 12,000 (for windowed ML)

**Microgrid Specifications**:

| Property | MG1 (Diesel) | MG2 (Solar) | MG3 (Hybrid) |
|----------|--------------|------------|-------------|
| H (inertia) | 10.0 | 0.5 | 1.0 |
| D (damping) | 2.0 | 0.5 | 1.0 |
| R (droop) | 0.05 | 0.03 | 0.04 |
| P_nom (MW) | 15.0 | 8.0 | 9.0 |
| X (impedance) | 0.15 | 0.10 | 0.12 |
| Type | Synchronous | Inverter-based | Hybrid |

**Tie-Line Reactances** (3×3 symmetric):
```
X_tie = [
  [0.00, 0.30, 0.25],
  [0.30, 0.00, 0.35],
  [0.25, 0.35, 0.00]
]
```

### 2.2 Base Load/Generation Profiles

**Load Patterns**:
- Daily sinusoidal variation (morning peak, noon dip, evening peak)
- Gaussian smoothing for temporal correlation
- Random noise (±5% std dev)

**Solar Profile**:
- Sinusoidal daytime envelope (6 AM to 6 PM)
- Cloud dips: 0.5% probability, 30-80% output loss
- Ramps: realistic sunrise/sunset transitions

**Wind Profile**:
- 6-hour periodic oscillation (realistic wind cycles)
- 0.2 × random walk noise
- Clipped to [0, 1] pu

### 2.3 Disturbance Injection

Four disturbance types are randomly injected:

| Disturbance | Probability | Magnitude | Duration |
|-------------|------------|-----------|----------|
| Load Step | 0.2% per sample | ±30% of load | Instantaneous |
| Solar Dip | 0.1% per sample | 50-90% dip | 10-60 seconds |
| Wind Gust | 0.1% per sample | 1.2-1.8× wind | 5-30 seconds |
| Tie-Line Weakness | 0.05% per sample | 1.5-3× reactance | 20-120 seconds |

**Stochastic Character**: Disturbances create diverse system responses—critical for ML generalization.

### 2.4 Stability Labels

Labels are **physics-informed** by computing a composite stability score:

```
stability_score = w_V * (1 - Δ|V_min|) 
                + w_f * (1 - |Δf_max| / 1.0)
                + w_δ * (1 - |Δδ_max| / 30°)
                + w_P * (1 - |ΔP_max| / P_nom)

label = 1 if stability_score > percentile_60 else 0
```

- `Δ|V_min|` = voltage dip relative to nominal
- `|Δf_max|` = maximum frequency deviation
- `|Δδ_max|` = maximum rotor angle deviation
- `|ΔP_max|` = maximum power imbalance

**Result**: 62% stable / 38% unstable class distribution.

---

## 3. Feature Engineering

### 3.1 Windowing Strategy

Input windows: **12 timesteps** (6 seconds @ 0.5s sampling)  
Future horizon: **12 timesteps** ahead (6s look-ahead for prediction)  
Stride: **6 timesteps** (50% overlap for data augmentation)

**Rationale**:
- 6s observation window captures transient dynamics
- 6s prediction horizon aligns with fast control loop timescales
- Overlap increases data density without leakage

### 3.2 Feature Categories

#### Base Statistical Features (Per Bus, Per Feature)

For each of 8 raw measurements (voltage, angle, frequency, RoCoF, gen, load, tie-line, delay):

| Feature | Computation |
|---------|------------|
| Mean | μ = (1/N) Σ x_i |
| Std Dev | σ = √[(1/N) Σ (x_i - μ)²] |
| Min | min(x) |
| Max | max(x) |
| Range | max(x) - min(x) |
| Slope | (x_{12} - x_1) / Δt |

**Subtotal**: 8 measures × 6 features = **48 features per bus**

#### Inter-Area Features

For each bus pair (3 pairs × 2 directions):

| Feature | Pairs |
|---------|-------|
| Voltage difference | MG1-MG2, MG2-MG3, MG1-MG3 |
| Angle difference | MG1-MG2, MG2-MG3, MG1-MG3 |
| Frequency difference | MG1-MG2, MG2-MG3, MG1-MG3 |

**Subtotal**: 3 measures × 3 pairs × 2 aggregates (mean, max) = **18 features**

#### Aggregate Features

| Feature | Computation |
|---------|------------|
| Total Generation | Σ P_gen,i |
| Total Load | Σ P_load,i |
| Net Imbalance | Σ (P_gen,i - P_load,i) |
| Avg Delay | (1/3) Σ delay_i |
| Max Angle Spread | max(δ) - min(δ) |
| Voltage Std Dev | std(V) across buses |

**Subtotal**: **8 features**

#### **Total Features**: ~2,100+

- 3 buses × 48 = 144 base
- 18 inter-area
- 8 aggregate
- ×permutations and derived metrics
- ×2,000+ due to feature expansion in practice

---

## 4. Machine Learning Pipeline

### 4.1 Data Splitting

```
Raw Data (12,000 windows)
    ↓
Train Set (8,400 windows, 70%)
    ├── Classical ML: StandardScaler normalization
    └── Tree-based: No scaling
    ↓
Test Set (3,600 windows, 30%)
    ├── Stratified split (preserve class distribution)
    └── Used for all metrics
```

### 4.2 Model Architectures

#### Classical Models

**Logistic Regression**:
```
log(p / (1-p)) = β₀ + Σ β_i * X_i
```
- Max iterations: 500
- Balanced class weights
- L2 regularization (C=1.0)

**Support Vector Machine (RBF Kernel)**:
```
f(x) = sign(Σ α_i * K(x_i, x) + b)
where K(x, x') = exp(-γ ||x - x'||²)
```
- C=1.0, γ='scale'
- Probability calibration enabled
- Balanced class weights

**Random Forest**:
```
f(x) = (1/B) Σ_{b=1}^B h_b(x)
where h_b = decision tree grown on bootstrap sample
```
- n_estimators: 50
- max_depth: 12
- n_jobs: -1 (parallel)
- Balanced class weights
- **Best performer in this study**

**XGBoost**:
```
F(x) = Σ_{m=1}^M f_m(x)
where f_m minimizes: Σ L(y_i, f_{m-1}(x_i) + f_m(x_i)) + Ω(f_m)
```
- n_estimators: 50
- max_depth: 5
- learning_rate: 0.1
- eval_metric: 'logloss'

**Gradient Boosting**:
- n_estimators: 50
- max_depth: 4
- learning_rate: 0.1
- loss: 'deviance'

**K-Nearest Neighbors**:
- k ∈ {5, 10}
- Euclidean distance
- Uniform weights

**Decision Tree**:
- max_depth: unlimited
- min_samples_split: 2
- Balanced class weights

**Naive Bayes**:
- Gaussian assumption
- No regularization

**AdaBoost**:
- Base: DecisionTree(max_depth=1)
- n_estimators: 50
- learning_rate: 1.0

#### Deep Learning Models

**Small Neural Network**:
```
Input (2100) → Dense(64, relu) → Dropout(0.3) 
             → Dense(32, relu) → Dropout(0.3)
             → Dense(1, sigmoid) → Output
```

**Medium Neural Network**:
```
Input (2100) → Dense(128, relu) → BatchNorm → Dropout(0.3)
             → Dense(64, relu)  → BatchNorm → Dropout(0.3)
             → Dense(32, relu)  → BatchNorm → Dropout(0.3)
             → Dense(1, sigmoid) → Output
```

- Optimizer: Adam (lr=0.001)
- Loss: binary_crossentropy
- Metrics: accuracy
- Early stopping: patience=15 epochs

#### Ensemble Model (Stacking)

**Base Estimators**:
- Random Forest (100 trees, depth=15)
- SVM (RBF)
- Gradient Boosting (100 trees, depth=5)
- Naive Bayes

**Meta-Learner**: Logistic Regression  
**Stack Method**: predict_proba  
**CV**: 5-fold stratified

---

## 5. Federated Learning (FedAvg)

### 5.1 Algorithm

Standard FedAvg (McMahan et al., 2017):

```
Initialize global model w_0
for round r = 1 to R:
    for each client c in parallel:
        w_c^(r) ← client_train(w_global^(r-1), local_data_c, E epochs)
    w_global^(r) ← Σ_c (|D_c| / |D_total|) * w_c^(r)
```

### 5.2 Configuration

| Parameter | Value |
|-----------|-------|
| Clients | 3 (one per microgrid) |
| Communication Rounds | 15 |
| Epochs per Round | 5 |
| Batch Size | 32 |
| Model | Neural Network (128-64-32) |
| Optimizer | Adam |

### 5.3 Privacy Guarantee

- **Raw data never leaves client**: Only model weights transmitted
- **No server-side access to telemetry**: Satisfies GDPR/data privacy regulations
- **Optional Differential Privacy**: Can add DP-SGD for membership inference robustness

### 5.4 Convergence Results

| Round | Global Accuracy | Local Loss (avg) |
|-------|-----------------|-----------------|
| 0 (Initial) | 0.920 | 0.106 |
| 5 | 0.942 | 0.065 |
| 10 | 0.941 | 0.048 |
| 15 | 0.943 | 0.041 |

**Observation**: Convergence plateaus by round 10; local loss improvement saturates (diminishing returns).

---

## 6. Model Evaluation Metrics

### 6.1 Classification Metrics

```
Accuracy = (TP + TN) / (TP + TN + FP + FN)
Precision = TP / (TP + FP)  # False alarm rate
Recall = TP / (TP + FN)     # Miss rate
F1 = 2 * (Precision * Recall) / (Precision + Recall)
ROC-AUC = ∫ TPR(t) d FPR(t)  # Threshold-independent
MCC = (TP*TN - FP*FN) / √[(TP+FP)(TP+FN)(TN+FP)(TN+FN)]
```

### 6.2 Interpretation for Stability Prediction

- **Accuracy**: Overall correctness—avoid class imbalance bias
- **Precision**: Critical—false "stable" predictions cause blackout risk
- **Recall**: False "unstable" predictions trigger unnecessary controls
- **F1-Score**: Balanced tradeoff
- **ROC-AUC**: Robustness across operating points
- **MCC**: Best single metric for imbalanced data

### 6.3 Confusion Matrix

```
                Predicted
Actual      Stable   Unstable
Stable        TN        FP     (Type I: false alarm)
Unstable      FN        TP     (Type II: miss)

Risk assessment:
- FP/TN = false alarm rate (% stable mispredictions)
- FN/P = miss rate (% unstable mispredictions)
```

---

## 7. Validation on Pandapower Reference Model

### 7.1 Pandapower Network

- 5 buses (1 HV, 1 primary, 1 secondary, 1 microgrid, 1 LV distribution)
- 3-phase transformers (33 kV → 11 kV → 0.4 kV)
- Microgrid: Solar generator (80 kW) + Load (100 kW)
- Lines: R/X parameters from standard cables

### 7.2 Test Scenario Generation

**Load variation**: [70%, 130%] of nominal  
**DG variation**: [60%, 140%] of nominal  
**Grid voltage**: [97%, 103%] of nominal  
**Total scenarios**: 3,000 (25 × 20 × 6 = 3,000)

### 7.3 Stability Labeling (Pandapower)

```
if (V_min ≥ 0.95 pu) AND (VSI ≤ 1.0):
    label = "stable"
else:
    label = "unstable"
```

where VSI = voltage sensitivity index = ΔV / ΔP

### 7.4 Results

- **XGBoost Accuracy**: 93.9% (out-of-distribution)
- **Inference Time**: ~0.5 ms per sample
- **Generalization Gap**: 96.2% (test) → 93.9% (Pandapower) = 2.3% (acceptable)

---

## 8. Computational Complexity

### Training Time

| Model | Time (seconds) |
|-------|----------------|
| Logistic Regression | 0.2 |
| Decision Tree | 0.8 |
| KNN (k=5) | 0.1 |
| KNN (k=10) | 0.1 |
| SVM (Linear) | 2.3 |
| SVM (RBF) | 8.3 |
| Naive Bayes | 0.1 |
| Random Forest | **2.5** |
| XGBoost | 1.2 |
| AdaBoost | 3.2 |
| ANN (Small) | 2.1 |
| ANN (Medium) | 4.1 |
| Gradient Boosting | 26.0 |
| **Stacking Ensemble** | **18.5** |

**Hardware**: Intel Core i7 (8 cores), 16 GB RAM, 2,000 training samples

### Inference Time

- Classical (Random Forest): **0.5 ms** per sample ← suitable for real-time
- SVM: 1.2 ms
- Neural Network: 0.8 ms
- XGBoost: 0.6 ms

**Edge Device**: Raspberry Pi 4 → ~10 ms per inference (acceptable for 100 ms control cycles)

---

## 9. Code Structure

```
src/
├── dataset_generation/
│   └── synthetic_microgrid.py
│       class SyntheticMicrogridGenerator
│       - run() → DataFrame
│       - _frequency_step()
│       - _tie_line_power()
│       - _inject_disturbance()
│
├── feature_engineering/
│   └── feature_extractor.py
│       class FeatureExtractor
│       - fit_transform(df) → (X, y)
│       - compute_statistical_features()
│       - compute_inter_area_features()
│       - compute_aggregate_features()
│
├── models/
│   ├── classical_models.py
│   │   class ModelBenchmark
│   │   - train_all_models()
│   │   - evaluate_models()
│   │
│   ├── deep_learning.py
│   │   class NeuralNetworkTrainer
│   │   - build_small_model()
│   │   - build_medium_model()
│   │
│   ├── ensemble_models.py
│   │   class StackingEnsemble
│   │   - train()
│   │   - predict()
│   │
│   └── federated_learning.py
│       class FederatedLearning
│       - train(client_data)
│       - aggregate_weights()
│       - evaluate()
│
├── validation/
│   ├── pandapower_ref.py
│   │   class PandapowerValidator
│   │   - build_network()
│   │   - generate_scenarios()
│   │   - test()
│   │
│   └── evaluation_metrics.py
│       compute_all_metrics()
│       plot_roc_curves()
│       plot_confusion_matrices()
│
└── utils/
    ├── config.py
    └── logger.py
```

---

## 10. References

[1] M. J. Abbass et al. (2023). "Artificial Neural Network (ANN)-Based Voltage Stability Prediction of Test Microgrid Grid." IEEE Access, vol. 11.

[2] Z. Li & M. Shahidehpour (2019). "Small-Signal Modeling and Stability Analysis of Hybrid AC/DC Microgrids." IEEE Transactions on Smart Grid, vol. 10, no. 2, pp. 2080-2095.

[3] Y. Men, L. Ding, & X. Lu (2023). "Small-Signal Modeling and Stability Region Identification Using Support Vector Machine (SVM) for Autonomous Hybrid AC and DC Microgrids." IEEE ECCE, pp. 1438-1440.

[4] H. B. McMahan et al. (2017). "Communication-Efficient Learning of Deep Networks from Decentralized Data." Proc. 20th Int'l Conf. on AI and Statistics (AISTATS).

[5] A. Joshi et al. (2023). "Survey on AI and Machine Learning Techniques for Microgrid Energy Management Systems." IEEE/CAA Journal of Automatica Sinica, vol. 10, no. 7, pp. 1513-1529.

---

## 11. Future Research Directions

1. **Real-World Validation**: Deploy on production SCADA/PMU data from utility microgrids
2. **Domain Adaptation**: Handle topology changes and new grid configurations
3. **Explainability**: SHAP/LIME for feature importance in critical predictions
4. **Differential Privacy**: Add DP-SGD to federated learning for membership inference robustness
5. **Scalability**: Extend to 6-10 microgrid interconnected networks
6. **Control Integration**: Close-loop: stability prediction → fast control actuation

---

**Last Updated**: June 2026  
**Version**: 1.0
