"""
================================================================================
3-INTERCONNECTED MICROGRID SMALL-SIGNAL STABILITY DATASET GENERATOR
================================================================================
Topic: Stability Analysis of Small Signal Disturbances in On-Grid Microgrids
Author: Shrijita
================================================================================

PHYSICS MODEL:
  - Each MG modeled as a first-order frequency dynamic system:
      df/dt = (P_gen - P_load - P_tie) / (2*H) - D*(f - 50)
  - Angle evolves as: dδ/dt = 2*pi*(f - 50)
  - Tie-line power: P_tie = (V_i * V_j / X) * sin(δ_i - δ_j)
  - Droop control: P_gen = P_set - (1/R)*(f - 50)
  - Voltage: V = V_ref - X*(Q_load - Q_gen)

This first-order model is numerically stable and physically motivated for
inverter-based and diesel-synchronized microgrids.

OUTPUT:
  - CSV: FINAL_microgrid_dataset_0.5s_GENERATED.csv
  - Plots: 9 publication-quality figures
================================================================================
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
DT      = 0.5           # output sampling interval (seconds)
T_SIM   = 24 * 3600      # simulation time: 2 hours (change to 24*3600 for full day)
RANDOM_SEED = 42

# Disturbance probabilities (per output timestep)
DIST_PROB_LOAD_STEP  = 0.002
DIST_PROB_SOLAR_DIP  = 0.001
DIST_PROB_WIND_GUST  = 0.001
DIST_PROB_TIE_WEAK   = 0.0005

# Output paths
OUTPUT_CSV = r"C:\Users\Shrijita\Documents\kimi\workspace\FINAL_microgrid_dataset_0.5s_GENERATED.csv"
PLOT_DIR   = r"C:\Users\Shrijita\Documents\kimi\workspace\microgrid_plots"

import os
os.makedirs(PLOT_DIR, exist_ok=True)
np.random.seed(RANDOM_SEED)

print("="*60)
print("3-MICROGRID STABILITY DATASET GENERATOR")
print("="*60)

# ==============================================================================
# 2. MICROGRID PARAMETERS
# ==============================================================================
F_NOM = 50.0
V_NOM = 1.00

MGS = [
    {'name': 'MG1', 'H': 10.0, 'D': 2.0, 'R': 0.05, 'P_nom': 15.0, 'X': 0.15, 'V_ref': 1.02, 'type': 'diesel'},
    {'name': 'MG2', 'H': 0.5,  'D': 0.5, 'R': 0.03, 'P_nom': 8.0,  'X': 0.10, 'V_ref': 1.00, 'type': 'solar'},
    {'name': 'MG3', 'H': 1.0,  'D': 1.0, 'R': 0.04, 'P_nom': 9.0,  'X': 0.12, 'V_ref': 1.01, 'type': 'hybrid'},
]
N_MG = len(MGS)

# Tie-line reactances (pu)
X_TIE = np.array([
    [0.00, 0.30, 0.25],
    [0.30, 0.00, 0.35],
    [0.25, 0.35, 0.00]
])

# ==============================================================================
# 3. BASE PROFILES (Load, Solar, Wind)
# ==============================================================================
print("\n[1/4] Building base profiles...")

n_out = int(T_SIM / DT) + 1
t_out = np.arange(0, T_SIM + DT, DT)
hours = t_out / 3600.0

# Daily load pattern
daily = 0.8 + 0.4 * np.sin(np.pi * (hours - 6) / 12.0)
daily = np.clip(daily, 0.5, 1.2)

load1 = 12.0 * daily + 1.0 * np.sin(2*np.pi*hours/24) + np.random.normal(0, 0.3, n_out)
load2 = 6.0 * (0.7 + 0.6 * np.exp(-((hours - 19)**2)/8.0)) + np.random.normal(0, 0.2, n_out)
load3 = 6.0 * (0.6 + 0.8 * np.exp(-((hours - 14)**2)/18.0)) + np.random.normal(0, 0.2, n_out)
load = np.array([load1, load2, load3])

# Solar irradiance (daytime only, with clouds)
solar = np.maximum(0, np.sin(np.pi * (hours - 6) / 12.0))
solar = np.clip(solar, 0, 1)
cloud = np.random.rand(n_out) < 0.005
solar = np.where(cloud, solar * np.random.uniform(0.3, 0.8, n_out), solar)

# Wind speed
wind = 0.5 + 0.5 * np.sin(2*np.pi*hours/6.0) + 0.2 * np.random.randn(n_out)
wind = np.clip(wind, 0, 1)

# Base generation (before droop)
gen1_set = np.clip(load[0] - 2.0 * solar, 5.0, 15.0)  # diesel balances
gen2_set = 8.0 * solar                               # solar
gen3_set = 5.0 * solar + 4.0 * wind                 # hybrid

gen_set = np.array([gen1_set, gen2_set, gen3_set])

# ==============================================================================
# 4. DYNAMIC SIMULATION
# ==============================================================================
print("[2/4] Running dynamic simulation...")

# State arrays
freq  = np.zeros((N_MG, n_out))     # Hz
angle = np.zeros((N_MG, n_out))     # rad
V     = np.ones((N_MG, n_out))      # pu
P_gen = np.zeros((N_MG, n_out))     # actual gen output (MW)
P_tie = np.zeros((N_MG, n_out))     # net tie-line export (MW)
rocof = np.zeros((N_MG, n_out))     # Hz/s
delay = np.zeros((N_MG, n_out))     # seconds

# Initial conditions
freq[:, 0] = F_NOM
angle[:, 0] = 0.0
V[:, 0] = np.array([mg['V_ref'] for mg in MGS])
P_gen[:, 0] = gen_set[:, 0]

# Disturbance log
disturbances = []

for k in range(1, n_out):
    t = t_out[k]
    
    # --- Operating point ---
    P_load = load[:, k].copy()
    P_set = gen_set[:, k].copy()
    
    # --- Inject disturbances ---
    if np.random.rand() < DIST_PROB_LOAD_STEP:
        idx = np.random.randint(0, N_MG)
        step = np.random.uniform(-0.3, 0.3) * P_load[idx]
        P_load[idx] += step
        disturbances.append((t, 'load_step', f'MG{idx+1} {step:+.2f} MW'))
    
    if np.random.rand() < DIST_PROB_SOLAR_DIP:
        idx = np.random.choice([1, 2])
        dip = np.random.uniform(0.5, 0.9)
        if idx == 1: P_set[1] = 8.0 * solar[k] * dip
        else: P_set[2] = 5.0 * solar[k] * dip + 4.0 * wind[k]
        disturbances.append((t, 'solar_dip', f'MG{idx+1} {dip*100:.0f}%'))
    
    if np.random.rand() < DIST_PROB_WIND_GUST:
        gust = np.random.uniform(1.2, 1.8)
        P_set[2] = 5.0 * solar[k] + 4.0 * min(wind[k]*gust, 1.0)
        disturbances.append((t, 'wind_gust', f'MG3 x{gust:.2f}'))
    
    X_tie_now = X_TIE.copy()
    if np.random.rand() < DIST_PROB_TIE_WEAK:
        i, j = np.random.choice([0,1,2], size=2, replace=False)
        X_tie_now[i,j] *= np.random.uniform(1.5, 3.0)
        X_tie_now[j,i] = X_tie_now[i,j]
        disturbances.append((t, 'tie_weak', f'MG{i+1}-MG{j+1}'))
    
    # --- Droop control: P_gen = P_set - (1/R)*(f - 50) ---
    R = np.array([mg['R'] for mg in MGS])
    P_gen_k = P_set - (1.0/R) * (freq[:, k-1] - F_NOM)
    P_gen_k = np.clip(P_gen_k, 0.0, np.array([mg['P_nom'] for mg in MGS]))
    
    # --- Tie-line power: P_tie_i = sum_j (V_i*V_j/X_ij) * sin(delta_i - delta_j) ---
    P_tie_k = np.zeros(N_MG)
    for i in range(N_MG):
        for j in range(N_MG):
            if i != j:
                p = (V[i, k-1] * V[j, k-1] / X_tie_now[i,j]) * np.sin(angle[i, k-1] - angle[j, k-1])
                P_tie_k[i] += p
    
    # --- Power imbalance ---
    imbalance = P_gen_k - P_load - P_tie_k
    
    # --- Frequency dynamics: df/dt = imbalance/(2H) - D*(f-50) ---
    H = np.array([mg['H'] for mg in MGS])
    D = np.array([mg['D'] for mg in MGS])
    dfreq = imbalance / (2.0 * H) - D * (freq[:, k-1] - F_NOM)
    freq[:, k] = freq[:, k-1] + dfreq * DT
    
    # Clamp frequency to realistic bounds (prevent runaway)
    freq[:, k] = np.clip(freq[:, k], 48.0, 52.0)
    
    # --- Angle dynamics: dδ/dt = 2*pi*(f - 50) ---
    dangle = 2 * np.pi * (freq[:, k] - F_NOM)
    angle[:, k] = angle[:, k-1] + dangle * DT
    
    # Wrap angles to [-pi, pi] to prevent unbounded growth
    angle[:, k] = ((angle[:, k] + np.pi) % (2*np.pi)) - np.pi
    
    # --- ROCOF ---
    rocof[:, k] = (freq[:, k] - freq[:, k-1]) / DT
    
    # --- Voltage: V = V_ref - X*(Q_load - Q_gen) ---
    Q_gen = P_gen_k * 0.2   # simplified power factor ~0.98
    Q_load = P_load * 0.2
    X_self = np.array([mg['X'] for mg in MGS])
    V_ref = np.array([mg['V_ref'] for mg in MGS])
    V[:, k] = V_ref - X_self * (Q_load - Q_gen) + np.random.normal(0, 0.002, N_MG)
    V[:, k] = np.clip(V[:, k], 0.92, 1.08)
    
    # --- Delay: base + stress-correlated + noise ---
    stress = np.abs(P_load - P_gen_k) / np.array([mg['P_nom'] for mg in MGS])
    delay[:, k] = np.random.uniform(0.05, 0.15) + 0.15 * stress + np.random.normal(0, 0.02, N_MG)
    delay[:, k] = np.clip(delay[:, k], 0.05, 0.30)
    
    # Store values
    P_gen[:, k] = P_gen_k
    P_tie[:, k] = P_tie_k

print(f"  Output points: {n_out}")
print(f"  Disturbances: {len(disturbances)}")

# ==============================================================================
# 5. BUILD DATAFRAME
# ==============================================================================
print("[3/4] Building DataFrame...")

dfs = []
for i, mg in enumerate(MGS):
    bus_df = pd.DataFrame({
        'time': t_out,
        'bus': mg['name'],
        'voltage_pu': V[i, :],
        'angle_deg': np.degrees(angle[i, :]),
        'frequency': freq[i, :],
        'rocof': rocof[i, :],
        'gen_p': P_gen[i, :],
        'load_p': load[i, :],
        'tie_line_power': P_tie[i, :],
        'delay': delay[i, :]
    })
    dfs.append(bus_df)

df = pd.concat(dfs, ignore_index=True)
df.to_csv(OUTPUT_CSV, index=False)

print(f"  CSV: {OUTPUT_CSV}")
print(f"  Shape: {df.shape}")

# ==============================================================================
# 6. VALIDATION
# ==============================================================================
print("\n[4/4] Validation statistics...")

for bus in df['bus'].unique():
    b = df[df['bus'] == bus]
    print(f"\n  {bus}:")
    print(f"    Voltage:    [{b['voltage_pu'].min():.4f}, {b['voltage_pu'].max():.4f}] pu")
    print(f"    Frequency:  [{b['frequency'].min():.4f}, {b['frequency'].max():.4f}] Hz")
    print(f"    Angle:      [{b['angle_deg'].min():.4f}, {b['angle_deg'].max():.4f}] deg")
    print(f"    ROCOF:      [{b['rocof'].min():.4f}, {b['rocof'].max():.4f}] Hz/s")
    print(f"    Gen:        [{b['gen_p'].min():.4f}, {b['gen_p'].max():.4f}] MW")
    print(f"    Load:       [{b['load_p'].min():.4f}, {b['load_p'].max():.4f}] MW")
    print(f"    Tie-line:   [{b['tie_line_power'].min():.4f}, {b['tie_line_power'].max():.4f}] MW")

# ==============================================================================
# 7. PLOTS
# ==============================================================================
print("\nGenerating plots...")

# 7.1 Voltage
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
fig.suptitle('Voltage Magnitude (pu) - 3 Microgrids', fontsize=14, fontweight='bold')
for i, bus in enumerate(['MG1', 'MG2', 'MG3']):
    b = df[df['bus'] == bus]
    axes[i].plot(b['time']/3600, b['voltage_pu'], linewidth=0.5, label=bus)
    axes[i].axhline(0.95, color='r', linestyle='--', alpha=0.3)
    axes[i].axhline(1.05, color='r', linestyle='--', alpha=0.3)
    axes[i].set_ylabel('Voltage (pu)')
    axes[i].legend(); axes[i].grid(alpha=0.3)
axes[-1].set_xlabel('Time (hours)')
plt.tight_layout(); plt.savefig(os.path.join(PLOT_DIR, '01_voltage.png'), dpi=200); plt.close()

# 7.2 Frequency
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
fig.suptitle('Frequency (Hz) - 3 Microgrids', fontsize=14, fontweight='bold')
for i, bus in enumerate(['MG1', 'MG2', 'MG3']):
    b = df[df['bus'] == bus]
    axes[i].plot(b['time']/3600, b['frequency'], linewidth=0.5, color=f'C{i}', label=bus)
    axes[i].axhline(49.5, color='r', linestyle='--', alpha=0.3)
    axes[i].axhline(50.5, color='r', linestyle='--', alpha=0.3)
    axes[i].set_ylabel('Frequency (Hz)')
    axes[i].legend(); axes[i].grid(alpha=0.3)
axes[-1].set_xlabel('Time (hours)')
plt.tight_layout(); plt.savefig(os.path.join(PLOT_DIR, '02_frequency.png'), dpi=200); plt.close()

# 7.3 Angle differences
fig, ax = plt.subplots(figsize=(14, 5))
fig.suptitle('Inter-Area Angle Differences', fontsize=14, fontweight='bold')
m1 = df[df['bus']=='MG1']['angle_deg'].values
m2 = df[df['bus']=='MG2']['angle_deg'].values
m3 = df[df['bus']=='MG3']['angle_deg'].values
ax.plot(t_out/3600, m1-m2, linewidth=0.5, label='MG1-MG2')
ax.plot(t_out/3600, m2-m3, linewidth=0.5, label='MG2-MG3')
ax.plot(t_out/3600, m1-m3, linewidth=0.5, label='MG1-MG3')
ax.axhline(10, color='r', linestyle='--', alpha=0.3); ax.axhline(-10, color='r', linestyle='--', alpha=0.3)
ax.set_xlabel('Time (hours)'); ax.set_ylabel('Angle Diff (deg)')
ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig(os.path.join(PLOT_DIR, '03_angle_diff.png'), dpi=200); plt.close()

# 7.4 ROCOF
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
fig.suptitle('Rate of Change of Frequency (ROCOF)', fontsize=14, fontweight='bold')
for i, bus in enumerate(['MG1', 'MG2', 'MG3']):
    b = df[df['bus'] == bus]
    axes[i].plot(b['time']/3600, b['rocof'], linewidth=0.5, color=f'C{i}', label=bus)
    axes[i].axhline(0.5, color='r', linestyle='--', alpha=0.3); axes[i].axhline(-0.5, color='r', linestyle='--', alpha=0.3)
    axes[i].set_ylabel('ROCOF (Hz/s)'); axes[i].legend(); axes[i].grid(alpha=0.3)
axes[-1].set_xlabel('Time (hours)')
plt.tight_layout(); plt.savefig(os.path.join(PLOT_DIR, '04_rocof.png'), dpi=200); plt.close()

# 7.5 Tie-line power
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
fig.suptitle('Net Tie-Line Power Export', fontsize=14, fontweight='bold')
for i, bus in enumerate(['MG1', 'MG2', 'MG3']):
    b = df[df['bus'] == bus]
    axes[i].plot(b['time']/3600, b['tie_line_power'], linewidth=0.5, color=f'C{i}', label=bus)
    axes[i].axhline(0, color='k', linestyle='-', alpha=0.3)
    axes[i].set_ylabel('Power (MW)'); axes[i].legend(); axes[i].grid(alpha=0.3)
axes[-1].set_xlabel('Time (hours)')
plt.tight_layout(); plt.savefig(os.path.join(PLOT_DIR, '05_tie_power.png'), dpi=200); plt.close()

# 7.6 Power imbalance
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
fig.suptitle('Power Imbalance (Gen - Load)', fontsize=14, fontweight='bold')
for i, bus in enumerate(['MG1', 'MG2', 'MG3']):
    b = df[df['bus'] == bus]
    imb = b['gen_p'].values - b['load_p'].values
    axes[i].plot(b['time']/3600, imb, linewidth=0.5, color=f'C{i}', label=bus)
    axes[i].axhline(0, color='k', linestyle='-', alpha=0.3)
    axes[i].set_ylabel('Imbalance (MW)'); axes[i].legend(); axes[i].grid(alpha=0.3)
axes[-1].set_xlabel('Time (hours)')
plt.tight_layout(); plt.savefig(os.path.join(PLOT_DIR, '06_imbalance.png'), dpi=200); plt.close()

# 7.7 Phase portrait
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Phase Portrait: Freq Dev vs Angle', fontsize=14, fontweight='bold')
for i, bus in enumerate(['MG1', 'MG2', 'MG3']):
    b = df[df['bus'] == bus]
    sc = axes[i].scatter(b['angle_deg'], b['frequency']-F_NOM, s=0.1, alpha=0.3, c=b['time'], cmap='viridis')
    axes[i].set_xlabel('Angle (deg)'); axes[i].set_ylabel('Freq Dev (Hz)')
    axes[i].set_title(bus); axes[i].grid(alpha=0.3)
plt.tight_layout(); plt.savefig(os.path.join(PLOT_DIR, '07_phase_portrait.png'), dpi=200); plt.close()

# 7.8 Disturbance timeline
fig, ax = plt.subplots(figsize=(14, 4))
fig.suptitle('Injected Disturbances', fontsize=14, fontweight='bold')
dtypes = {'load_step': 0, 'solar_dip': 1, 'wind_gust': 2, 'tie_weak': 3}
colors = {'load_step': 'red', 'solar_dip': 'orange', 'wind_gust': 'green', 'tie_weak': 'purple'}
for t, dtype, desc in disturbances:
    ax.scatter(t/3600, dtypes[dtype], color=colors[dtype], s=20, alpha=0.7)
ax.set_yticks(list(dtypes.values())); ax.set_yticklabels(list(dtypes.keys()))
ax.set_xlabel('Time (hours)'); ax.set_ylabel('Type'); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig(os.path.join(PLOT_DIR, '08_disturbances.png'), dpi=200); plt.close()

# 7.9 Correlation heatmap
fig, ax = plt.subplots(figsize=(10, 8))
fig.suptitle('Feature Correlation (MG1)', fontsize=14, fontweight='bold')
b = df[df['bus']=='MG1'][['voltage_pu','angle_deg','frequency','rocof','gen_p','load_p','tie_line_power','delay']]
corr = b.corr()
import seaborn as sns
sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdBu_r', center=0, ax=ax, linewidths=0.5)
plt.tight_layout(); plt.savefig(os.path.join(PLOT_DIR, '09_correlation.png'), dpi=200); plt.close()

print("\n" + "="*60)
print("DATASET GENERATION COMPLETE")
print("="*60)
print(f"CSV: {OUTPUT_CSV} ({df.shape[0]} rows, {df.shape[1]} cols)")
print(f"Plots: {PLOT_DIR} (9 files)")
print("\nTo generate a full 24-hour dataset, change:")
print("  T_SIM = 2 * 3600  -->  T_SIM = 24 * 3600")
print("="*60)
