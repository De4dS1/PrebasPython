"""
Generador de dataset sintético para detección de artefactos en ECG.

Problema: clasificación binaria (limpia vs artefacto) pero el enfoque es
DETECCIÓN DE ANOMALÍAS no supervisada con Random Cut Forest (RCF) en SageMaker.
Las etiquetas solo se usan para evaluación posterior (ROC, precision/recall).

Variables generadas (coinciden con las del documento del proyecto):
  - timestamp                : marca de tiempo ISO8601 del latido
  - time_offset_seconds      : segundos desde el inicio del registro
  - rr_interval_ms           : intervalo RR (ms)
  - pr_interval_ms           : intervalo PR (ms)
  - p_wave_amplitude_mv      : amplitud de la onda P (mV)
  - t_wave_amplitude_mv      : amplitud de la onda T (mV)
  - morphology_score         : similitud al template de latido limpio (0-1)
  - heart_rate_bpm           : frecuencia cardíaca derivada del RR
  - is_artifact              : etiqueta ground truth (0 = limpio, 1 = artefacto)

Tipos de artefactos simulados (realistas en un Holter o telemetría):
  1. Pérdida de contacto del electrodo → amplitudes muy bajas, morfología pobre
  2. Ruido muscular (EMG) → alta variabilidad, morfología degradada
  3. Artefacto de movimiento → RR extremos (latidos prematuros o pausas)
  4. Deriva de línea base → amplitudes desplazadas, morfología ligeramente alterada

Salida:
  dataset/train.csv         (80%, con headers, para entrenamiento RCF)
  dataset/validation.csv    (20%, con headers, para evaluación con etiqueta)
"""

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

OUT_DIR = Path(__file__).parent / "dataset"
OUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
N_NORMAL = 1800
N_ART_CONTACT = 60    # pérdida de electrodo
N_ART_EMG = 60        # ruido muscular
N_ART_MOTION = 40     # artefacto de movimiento
N_ART_BASELINE = 40   # deriva de línea base

BASE_TIME = datetime(2026, 4, 24, 10, 0, 0)


# ---------------------------------------------------------------------------
# Generar latidos normales
# ---------------------------------------------------------------------------
def gen_normal(n: int) -> pd.DataFrame:
    return pd.DataFrame({
        "rr_interval_ms":       rng.normal(800, 50, n).clip(650, 1000),
        "pr_interval_ms":       rng.normal(160, 15, n).clip(120, 210),
        "p_wave_amplitude_mv":  rng.normal(0.15, 0.03, n).clip(0.08, 0.28),
        "t_wave_amplitude_mv":  rng.normal(0.30, 0.06, n).clip(0.15, 0.55),
        "morphology_score":     rng.normal(0.93, 0.03, n).clip(0.80, 1.00),
        "is_artifact":          0,
    })


# ---------------------------------------------------------------------------
# Generadores por tipo de artefacto
# ---------------------------------------------------------------------------
def gen_electrode_loss(n: int) -> pd.DataFrame:
    """Contacto pobre → amplitudes bajas, morfología muy pobre."""
    return pd.DataFrame({
        "rr_interval_ms":       rng.normal(820, 150, n).clip(450, 1400),
        "pr_interval_ms":       rng.normal(170, 55, n).clip(80, 290),
        "p_wave_amplitude_mv":  rng.normal(0.03, 0.02, n).clip(0.00, 0.08),
        "t_wave_amplitude_mv":  rng.normal(0.06, 0.04, n).clip(0.00, 0.18),
        "morphology_score":     rng.normal(0.45, 0.12, n).clip(0.15, 0.70),
        "is_artifact":          1,
    })


def gen_emg_noise(n: int) -> pd.DataFrame:
    """Ruido muscular → T varía mucho, morfología media, amplitudes dispersas."""
    return pd.DataFrame({
        "rr_interval_ms":       rng.normal(780, 180, n).clip(480, 1350),
        "pr_interval_ms":       rng.normal(175, 45, n).clip(95, 270),
        "p_wave_amplitude_mv":  rng.normal(0.20, 0.10, n).clip(0.02, 0.55),
        "t_wave_amplitude_mv":  rng.normal(0.40, 0.25, n).clip(0.02, 1.10),
        "morphology_score":     rng.normal(0.62, 0.10, n).clip(0.35, 0.85),
        "is_artifact":          1,
    })


def gen_motion_artifact(n: int) -> pd.DataFrame:
    """Movimiento → RR extremos (premature beats + pausas), amplitudes anómalas."""
    half = n // 2
    rr = np.concatenate([
        rng.normal(310, 45, half).clip(180, 480),               # latidos prematuros
        rng.normal(1420, 160, n - half).clip(1150, 2000),       # pausas largas
    ])
    rng.shuffle(rr)
    return pd.DataFrame({
        "rr_interval_ms":       rr,
        "pr_interval_ms":       rng.normal(165, 50, n).clip(90, 310),
        "p_wave_amplitude_mv":  rng.normal(0.28, 0.18, n).clip(0.03, 0.85),
        "t_wave_amplitude_mv":  rng.normal(0.48, 0.22, n).clip(0.05, 1.00),
        "morphology_score":     rng.normal(0.72, 0.10, n).clip(0.50, 0.90),
        "is_artifact":          1,
    })


def gen_baseline_drift(n: int) -> pd.DataFrame:
    """Deriva → RR y PR casi normales, pero amplitudes bajas y morfología atípica."""
    return pd.DataFrame({
        "rr_interval_ms":       rng.normal(810, 55, n).clip(640, 1020),
        "pr_interval_ms":       rng.normal(195, 25, n).clip(140, 255),
        "p_wave_amplitude_mv":  rng.normal(0.07, 0.03, n).clip(0.01, 0.14),
        "t_wave_amplitude_mv":  rng.normal(0.14, 0.05, n).clip(0.04, 0.28),
        "morphology_score":     rng.normal(0.76, 0.05, n).clip(0.65, 0.88),
        "is_artifact":          1,
    })


# ---------------------------------------------------------------------------
# Ensamblado
# ---------------------------------------------------------------------------
df = pd.concat([
    gen_normal(N_NORMAL),
    gen_electrode_loss(N_ART_CONTACT),
    gen_emg_noise(N_ART_EMG),
    gen_motion_artifact(N_ART_MOTION),
    gen_baseline_drift(N_ART_BASELINE),
], ignore_index=True)

df["heart_rate_bpm"] = (60000.0 / df["rr_interval_ms"]).round(2)

# Mezclar el orden y asignar timestamps secuenciales (simulando monitoreo continuo)
df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)

timestamps = []
offsets = []
current = BASE_TIME
for rr_ms in df["rr_interval_ms"]:
    timestamps.append(current.isoformat(timespec="milliseconds"))
    offsets.append((current - BASE_TIME).total_seconds())
    current += timedelta(milliseconds=float(rr_ms))
df["timestamp"] = timestamps
df["time_offset_seconds"] = np.round(offsets, 3)

# Redondear columnas numéricas para que los CSV sean legibles
for col in ["rr_interval_ms", "pr_interval_ms",
            "p_wave_amplitude_mv", "t_wave_amplitude_mv",
            "morphology_score"]:
    df[col] = df[col].round(4)

# Reordenar columnas en el orden lógico del documento
df = df[[
    "timestamp",
    "time_offset_seconds",
    "rr_interval_ms",
    "pr_interval_ms",
    "p_wave_amplitude_mv",
    "t_wave_amplitude_mv",
    "morphology_score",
    "heart_rate_bpm",
    "is_artifact",
]]


# ---------------------------------------------------------------------------
# Split train / validation (80 / 20 estratificado por etiqueta)
# ---------------------------------------------------------------------------
normal_idx = df.index[df["is_artifact"] == 0].tolist()
artifact_idx = df.index[df["is_artifact"] == 1].tolist()
rng.shuffle(normal_idx)
rng.shuffle(artifact_idx)

n_train_normal = int(0.8 * len(normal_idx))
n_train_artifact = int(0.8 * len(artifact_idx))

train_idx = sorted(normal_idx[:n_train_normal] + artifact_idx[:n_train_artifact])
val_idx = sorted(normal_idx[n_train_normal:] + artifact_idx[n_train_artifact:])

train_df = df.loc[train_idx].reset_index(drop=True)
val_df = df.loc[val_idx].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Guardar
# ---------------------------------------------------------------------------
train_path = OUT_DIR / "train.csv"
val_path = OUT_DIR / "validation.csv"
train_df.to_csv(train_path, index=False)
val_df.to_csv(val_path, index=False)

print(f"Generados:")
print(f"  {train_path}  ({len(train_df)} filas, "
      f"{(train_df['is_artifact'] == 1).sum()} artefactos)")
print(f"  {val_path}  ({len(val_df)} filas, "
      f"{(val_df['is_artifact'] == 1).sum()} artefactos)")
print(f"\nTasa de artefactos global: "
      f"{df['is_artifact'].mean() * 100:.2f}%")
print(f"\nPrimeras filas:")
print(train_df.head().to_string(index=False))
