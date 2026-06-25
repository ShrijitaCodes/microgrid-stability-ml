# -*- coding: utf-8 -*-
"""
FEDERATED LEARNING - STANDALONE DEMONSTRATION (FedAvg)
======================================================
Uses a simple neural network where weights can be averaged across clients.
This demonstrates the true FedAvg algorithm for the microgrid use case.

Concept Mapping:
  - Each "client" = One microgrid (MG1, MG2, MG3) generating local data
  - Server = Central utility / aggregator (no raw data shared)
  - Communication rounds = Periodic synchronization of model updates

Dependencies: numpy, scikit-learn, tensorflow
"""

import numpy as np
import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)

OUTPUT_DIR = '/content/federated_demo_output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*60)
print("FEDERATED AVERAGING (FedAvg) DEMO")
print("="*60)

# ============================================================
# 1. LOAD & PREPARE DATA (reuse your dataset)
# ============================================================
print("\n[1/3] Loading data...")

DATA_PATH = '/FINAL_microgrid_dataset_0.5s_REFORMED.csv'
SUBSAMPLE_EVERY = 3
WINDOW_SIZE = 12
STEP_SIZE = 6
MAX_SAMPLES = 12000

df = pd.read_csv(DATA_PATH)
df = df.iloc[::SUBSAMPLE_EVERY].copy()
buses = sorted(df['bus'].unique())

feature_cols = ['voltage_pu', 'angle_deg', 'frequency', 'rocof',
                'gen_p', 'load_p', 'tie_line_power', 'delay']

df_wide = df.pivot_table(index='time', columns='bus', values=feature_cols)
df_wide.columns = [f"{col[0]}_{col[1]}" for col in df_wide.columns]
df_wide = df_wide.reset_index()

# Differences
for pair in [('MG1','MG2'), ('MG2','MG3'), ('MG1','MG3')]:
    if f'angle_deg_{pair[0]}' in df_wide.columns and f'angle_deg_{pair[1]}' in df_wide.columns:
        df_wide[f'angle_diff_{pair[0]}_{pair[1]}'] = df_wide[f'angle_deg_{pair[0]}'] - df_wide[f'angle_deg_{pair[1]}']

# Aggregates
gen_cols = [c for c in df_wide.columns if c.startswith('gen_p_')]
load_cols = [c for c in df_wide.columns if c.startswith('load_p_')]
delay_cols = [c for c in df_wide.columns if c.startswith('delay_')]
if gen_cols: df_wide['total_gen_p'] = df_wide[gen_cols].sum(axis=1)
if load_cols: df_wide['total_load_p'] = df_wide[load_cols].sum(axis=1)
if gen_cols and load_cols: df_wide['total_power_imbalance'] = df_wide['total_gen_p'] - df_wide['total_load_p']
if delay_cols: df_wide['avg_delay'] = df_wide[delay_cols].mean(axis=1)

all_features = [c for c in df_wide.columns if c != 'time']
X_list, y_list = [], []
n = len(df_wide)

for i in range(0, n - 2*WINDOW_SIZE, STEP_SIZE):
    window = df_wide.iloc[i:i+WINDOW_SIZE]
    future = df_wide.iloc[i+WINDOW_SIZE:i+2*WINDOW_SIZE]

    feats = {}
    for col in all_features:
        vals = window[col].values
        feats[f'{col}_mean'] = np.mean(vals)
        feats[f'{col}_std'] = np.std(vals)
        feats[f'{col}_min'] = np.min(vals)
        feats[f'{col}_max'] = np.max(vals)
        feats[f'{col}_range'] = np.max(vals) - np.min(vals)
        x = np.arange(len(vals))
        feats[f'{col}_slope'] = np.polyfit(x, vals, 1)[0] if np.std(vals) > 1e-9 else 0.0

    bus_scores = []
    for bus in buses:
        v = future[f'voltage_pu_{bus}'].values
        f = future[f'frequency_{bus}'].values
        r = future[f'rocof_{bus}'].values
        a = future[f'angle_deg_{bus}'].values
        g = future[f'gen_p_{bus}'].values
        l = future[f'load_p_{bus}'].values
        d = future[f'delay_{bus}'].values

        v_score = max(0, 1 - np.max(np.abs(v - 1.0)) / 0.05)
        f_score = max(0, 1 - np.max(np.abs(f - 50.0)) / 0.1)
        r_score = max(0, 1 - np.max(np.abs(r)) / 0.1)
        a_score = max(0, 1 - np.max(np.abs(a)) / 10.0)
        p_score = max(0, 1 - np.mean(np.abs(g - l)) / 5.0)
        d_score = max(0, 1 - np.mean(d) / 0.3)
        bus_scores.append(np.mean([v_score, f_score, r_score, a_score, p_score, d_score]))

    inter_scores = []
    for pair in [('MG1','MG2'), ('MG2','MG3'), ('MG1','MG3')]:
        if f'angle_deg_{pair[0]}' in df_wide.columns and f'angle_deg_{pair[1]}' in df_wide.columns:
            a1 = future[f'angle_deg_{pair[0]}'].values
            a2 = future[f'angle_deg_{pair[1]}'].values
            diff = np.max(np.abs(a1 - a2))
            inter_scores.append(max(0, 1 - diff / 10.0))

    pimb = np.mean(np.abs(future['total_power_imbalance'].values)) if 'total_power_imbalance' in future.columns else 0
    pimb_score = max(0, 1 - pimb / 5.0)
    overall_score = np.mean(bus_scores + inter_scores + [pimb_score])

    X_list.append(feats)
    y_list.append(overall_score)

    if len(X_list) >= MAX_SAMPLES:
        break

X_df = pd.DataFrame(X_list)
X_df = X_df.loc[:, X_df.std() > 1e-9]
scores = np.array(y_list)
threshold = np.percentile(scores, 60)
y = np.where(scores >= threshold, 1, 0)

print(f"  Windows: {len(X_df)}, Features: {X_df.shape[1]}")
print(f"  Stable: {np.sum(y==1)}, Unstable: {np.sum(y==0)}")

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X_df, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

# ============================================================
# 2. FEDERATED LEARNING SETUP
# ============================================================
print("\n[2/3] Setting up Federated Learning...")

NUM_CLIENTS = 3  # MG1, MG2, MG3
EPOCHS_PER_ROUND = 5
BATCH_SIZE = 64
NUM_ROUNDS = 15
LEARNING_RATE = 0.001

# Split training data among clients (non-IID split simulates real microgrid heterogeneity)
# Each client gets a different distribution of data
client_data = []
client_sizes = []
total_samples = len(X_train_s)
samples_per_client = total_samples // NUM_CLIENTS

for i in range(NUM_CLIENTS):
    start = i * samples_per_client
    end = (i + 1) * samples_per_client if i < NUM_CLIENTS - 1 else total_samples
    client_data.append({
        'X': X_train_s[start:end],
        'y': y_train[start:end]
    })
    client_sizes.append(end - start)
    print(f"  Client {i+1} (MG{i+1}): {client_sizes[-1]} samples")

# Global model architecture
input_dim = X_train_s.shape[1]

def build_model():
    """Build a fresh neural network model."""
    model = Sequential([
        Dense(128, activation='relu', input_shape=(input_dim,)),
        BatchNormalization(),
        Dropout(0.3),
        Dense(64, activation='relu'),
        BatchNormalization(),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    return model

# FedAvg: weighted average of model weights
def federated_average(client_weights, client_sizes):
    """
    Average model weights proportional to number of samples per client.
    This is the core FedAvg algorithm.
    """
    total_samples = sum(client_sizes)
    new_weights = []
    for weights in zip(*client_weights):
        weighted_avg = np.zeros_like(weights[0], dtype=np.float32)
        for w, size in zip(weights, client_sizes):
            weighted_avg += w * (size / total_samples)
        new_weights.append(weighted_avg)
    return new_weights

def set_model_weights(model, weights):
    """Set model weights from a list of numpy arrays."""
    model.set_weights(weights)

def get_model_weights(model):
    """Get model weights as a list of numpy arrays."""
    return model.get_weights()

# ============================================================
# 3. RUN FEDERATED TRAINING
# ============================================================
print("\n[3/3] Running Federated Training (FedAvg)...")
print(f"  Rounds: {NUM_ROUNDS}, Local epochs per round: {EPOCHS_PER_ROUND}")
print("-" * 60)

# Initialize global model
global_model = build_model()
global_weights = get_model_weights(global_model)

history = {
    'round': [],
    'global_acc': [],
    'global_f1': [],
    'global_roc': [],
    'avg_local_loss': []
}

for round_num in range(NUM_ROUNDS):
    local_weights = []
    local_losses = []

    # Each client trains locally starting from global weights
    for client_id in range(NUM_CLIENTS):
        local_model = build_model()
        set_model_weights(local_model, global_weights)

        # Local training
        hist = local_model.fit(
            client_data[client_id]['X'],
            client_data[client_id]['y'],
            epochs=EPOCHS_PER_ROUND,
            batch_size=BATCH_SIZE,
            verbose=0,
            shuffle=True
        )
        local_losses.append(hist.history['loss'][-1])
        local_weights.append(get_model_weights(local_model))

    # Server aggregates weights
    global_weights = federated_average(local_weights, client_sizes)
    set_model_weights(global_model, global_weights)

    # Evaluate global model on test set
    y_prob = global_model.predict(X_test_s, verbose=0).flatten()
    y_pred = (y_prob >= 0.5).astype(int)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc = roc_auc_score(y_test, y_prob)
    avg_loss = np.mean(local_losses)

    history['round'].append(round_num + 1)
    history['global_acc'].append(acc)
    history['global_f1'].append(f1)
    history['global_roc'].append(roc)
    history['avg_local_loss'].append(avg_loss)

    if round_num % 3 == 0 or round_num == NUM_ROUNDS - 1:
        print(f"  Round {round_num+1:2d}: Global Acc={acc:.4f}, F1={f1:.4f}, ROC={roc:.4f}, AvgLocalLoss={avg_loss:.4f}")

# ============================================================
# 4. COMPARE WITH CENTRALIZED BASELINE
# ============================================================
print("\n" + "="*60)
print("COMPARISON: CENTRALIZED vs FEDERATED")
print("="*60)

# Centralized baseline
central_model = build_model()
central_model.fit(
    X_train_s, y_train,
    epochs=NUM_ROUNDS * EPOCHS_PER_ROUND,
    batch_size=BATCH_SIZE,
    verbose=0
)

c_y_prob = central_model.predict(X_test_s, verbose=0).flatten()
c_y_pred = (c_y_prob >= 0.5).astype(int)
c_acc = accuracy_score(y_test, c_y_pred)
c_f1 = f1_score(y_test, c_y_pred, zero_division=0)
c_roc = roc_auc_score(y_test, c_y_prob)

print(f"  Centralized (all data together):")
print(f"    Accuracy: {c_acc:.4f}, F1: {c_f1:.4f}, ROC-AUC: {c_roc:.4f}")
print(f"  Federated (FedAvg, no raw data sharing):")
print(f"    Accuracy: {acc:.4f}, F1: {f1:.4f}, ROC-AUC: {roc:.4f}")
print(f"  Performance gap: {abs(c_acc - acc):.4f} accuracy")

# ============================================================
# 5. VISUALIZATIONS
# ============================================================
print("\nSaving plots...")

# Plot 1: Convergence curves
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

axes[0].plot(history['round'], history['global_acc'], marker='o', color='darkblue', linewidth=2)
axes[0].axhline(c_acc, color='red', linestyle='--', label='Centralized')
axes[0].set_xlabel('Communication Round')
axes[0].set_ylabel('Accuracy')
axes[0].set_title('Global Test Accuracy')
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].plot(history['round'], history['global_f1'], marker='s', color='darkgreen', linewidth=2)
axes[1].axhline(c_f1, color='red', linestyle='--', label='Centralized')
axes[1].set_xlabel('Communication Round')
axes[1].set_ylabel('F1-Score')
axes[1].set_title('Global F1-Score')
axes[1].legend()
axes[1].grid(alpha=0.3)

axes[2].plot(history['round'], history['avg_local_loss'], marker='^', color='coral', linewidth=2)
axes[2].set_xlabel('Communication Round')
axes[2].set_ylabel('Average Local Loss')
axes[2].set_title('Local Training Loss (averaged)')
axes[2].grid(alpha=0.3)

plt.suptitle('Federated Learning (FedAvg) on Microgrid Stability Data', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'fedavg_convergence.png'), dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: Final comparison bar chart
plt.figure(figsize=(8, 5))
metrics = ['Accuracy', 'F1-Score', 'ROC-AUC']
central_vals = [c_acc, c_f1, c_roc]
fl_vals = [acc, f1, roc]

x = np.arange(len(metrics))
width = 0.35
plt.bar(x - width/2, central_vals, width, label='Centralized', color='steelblue')
plt.bar(x + width/2, fl_vals, width, label='Federated (FedAvg)', color='coral')
plt.xticks(x, metrics)
plt.ylabel('Score')
plt.ylim([0.85, 1.0])
plt.title('Centralized vs Federated Learning Performance')
plt.legend()
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'centralized_vs_federated.png'), dpi=300, bbox_inches='tight')
plt.close()

print(f"  Saved: {OUTPUT_DIR}/fedavg_convergence.png")
print(f"  Saved: {OUTPUT_DIR}/centralized_vs_federated.png")

# Save results
results_summary = pd.DataFrame({
    'Approach': ['Centralized (NN)', 'Federated (FedAvg)'],
    'Accuracy': [c_acc, acc],
    'F1-Score': [c_f1, f1],
    'ROC-AUC': [c_roc, roc]
})
results_summary.to_csv(os.path.join(OUTPUT_DIR, 'federated_comparison.csv'), index=False)
print(f"  Saved: {OUTPUT_DIR}/federated_comparison.csv")

print("\n" + "="*60)
print("FEDERATED LEARNING DEMO COMPLETE")
print("="*60)

# ============================================================
# 6. KEY TAKEAWAYS FOR YOUR PROJECT
# ============================================================
"""
WHY FEDERATED LEARNING FITS YOUR MICROGRID PROJECT:
---------------------------------------------------

1. Data Privacy & Sovereignty
   - Each microgrid (MG1, MG2, MG3) owns its operational data.
   - Utilities/regulators may not allow raw sensor data to leave the site.
   - FL trains locally; only model weights (parameters) travel to the server.

2. Heterogeneous Data (Non-IID)
   - Each microgrid has different load patterns, generation mix, weather exposure.
   - FL naturally handles this because each client trains on its own distribution.
   - The global model learns a shared representation that works across all microgrids.

3. Communication Efficiency
   - For large datasets (18k+ samples), sending raw data to a central server is
     bandwidth-intensive and creates a single point of failure.
   - FL sends only model weights (MBs) instead of raw time-series (GBs).

4. Real-world Deployment Path
   - Each microgrid runs a lightweight "FL client" on a Raspberry Pi or edge gateway.
   - The central server coordinates rounds (e.g., every 6 hours or daily).
   - This is exactly how companies like Google (Gboard), NVIDIA (NVIDIA FLARE),
     and IBM (IBM FL) deploy FL at scale.

5. Advanced FL Techniques to Explore
   - FedProx: Adds a proximal term to prevent local models from diverging too far.
   - SCAFFOLD: Uses control variates to correct for client drift.
   - Personalized FL (e.g., Per-FedAvg, pFedMe): Fine-tunes the global model locally
     so each microgrid gets a model tailored to its own patterns.
   - Differential Privacy: Adds noise to weights to prevent membership inference attacks.

PAPER RECOMMENDATIONS:
  - "Communication-Efficient Learning of Deep Networks from Decentralized Data"
    (McMahan et al., 2017) - The original FedAvg paper.
  - "Federated Learning: Challenges, Methods, and Future Directions" (Li et al., 2020)
  - "Federated Learning for IoT and Edge Computing" (Deng et al., 2020)
"""
