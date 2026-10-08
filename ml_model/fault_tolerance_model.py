import os
import time
import joblib
import numpy as np
import pandas as pd

from xgboost import XGBRegressor

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    explained_variance_score
)


# ============================================================
# CONFIGURATION
# ============================================================

DATA_PATH = "D:/raksha/capstone/try2/data/telecom_network_incidents_with_id.csv"

MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "fault_tolerance_model.joblib")
INFO_PATH = os.path.join(MODEL_DIR, "fault_tolerance_model_info.txt")

TARGET = "Fault Occurrence Rate (%)"


# ============================================================
# FEATURES
# ============================================================

NUMERIC_FEATURES = [
    "Cell Availability (%)",
    "MTTR (hours)",
    "Throughput (Mbps)",
    "Latency (ms)",
    "Packet Loss Rate (%)",
    "Call Drop Rate (%)",
    "Handover Success Rate (%)",
    "Alarm Count",
    "Critical Alarm Count",
    "Parameter Changes",
    "Successful Configuration Changes (%)",
    "Data Usage (GB)",
    "User Count",
    "Signal Strength (dBm)",
    "Jitter (ms)",
    "Connection Setup Success Rate (%)",
    "Security Incidents",
    "Authentication Failures",
    "Temperature (°C)",
    "Humidity (%)"
]

CATEGORICAL_FEATURES = [
    "Season",
    "Weather"
]

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


# ============================================================
# METRIC FUNCTIONS
# ============================================================

def safe_mape(y_true, y_pred):
    """
    MAPE that ignores zero actual values.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    mask = y_true != 0

    if mask.sum() == 0:
        return np.nan

    return np.mean(
        np.abs(
            (y_true[mask] - y_pred[mask])
            / y_true[mask]
        )
    ) * 100


def adjusted_r2(r2, n, p):
    """
    Adjusted R².

    p here represents the original input feature count.
    """
    if n <= p + 1:
        return np.nan

    return 1 - ((1 - r2) * (n - 1) / (n - p - 1))


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("XGBOOST FAULT OCCURRENCE RATE PREDICTION")
print("=" * 70)

print("\nLoading dataset...")

df = pd.read_csv(DATA_PATH)

print(f"Dataset shape: {df.shape}")


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_columns = ALL_FEATURES + [TARGET]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    print("\nERROR: Missing columns:")
    for col in missing_columns:
        print(f"  - {col}")

    raise ValueError(
        "Dataset does not contain all required columns."
    )


# ============================================================
# PREPARE DATA
# ============================================================

X = df[ALL_FEATURES].copy()
y = df[TARGET].copy()


# Convert target to numeric
y = pd.to_numeric(y, errors="coerce")


# Convert numeric columns
for col in NUMERIC_FEATURES:
    X[col] = pd.to_numeric(
        X[col],
        errors="coerce"
    )


# Remove rows where target is missing
valid_target = y.notna()

X = X.loc[valid_target].reset_index(drop=True)
y = y.loc[valid_target].reset_index(drop=True)


print(f"Usable rows: {len(X)}")
print(f"Target: {TARGET}")

print("\nTarget statistics:")
print(y.describe())


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print("\nTrain samples:", len(X_train))
print("Test samples :", len(X_test))


# ============================================================
# PREPROCESSING
# ============================================================

numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median")
        )
    ]
)


categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
        ),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore"
            )
        )
    ]
)


preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            numeric_pipeline,
            NUMERIC_FEATURES
        ),
        (
            "categorical",
            categorical_pipeline,
            CATEGORICAL_FEATURES
        )
    ]
)


# ============================================================
# XGBOOST MODEL
# ============================================================

model = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=8,
    min_child_weight=3,
    subsample=0.8,
    colsample_bytree=0.8,

    objective="reg:squarederror",
    eval_metric="rmse",

    random_state=42,
    n_jobs=-1,
    tree_method="hist"
)


# ============================================================
# COMPLETE PIPELINE
# ============================================================

pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            model
        )
    ]
)


# ============================================================
# TRAIN
# ============================================================

print("\n" + "=" * 70)
print("TRAINING XGBOOST")
print("=" * 70)

start_time = time.time()

pipeline.fit(
    X_train,
    y_train
)

training_time = time.time() - start_time

print(f"Training completed in {training_time:.2f} seconds")


# ============================================================
# PREDICTIONS
# ============================================================

print("\nGenerating predictions...")

prediction_start = time.time()

y_train_pred = pipeline.predict(X_train)
y_test_pred = pipeline.predict(X_test)

prediction_time = time.time() - prediction_start


# Keep predictions within percentage range
y_train_pred = np.clip(
    y_train_pred,
    0,
    100
)

y_test_pred = np.clip(
    y_test_pred,
    0,
    100
)


# ============================================================
# EVALUATION
# ============================================================

train_r2 = r2_score(
    y_train,
    y_train_pred
)

test_r2 = r2_score(
    y_test,
    y_test_pred
)

mae = mean_absolute_error(
    y_test,
    y_test_pred
)

mse = mean_squared_error(
    y_test,
    y_test_pred
)

rmse = np.sqrt(mse)

mape = safe_mape(
    y_test,
    y_test_pred
)

explained_variance = explained_variance_score(
    y_test,
    y_test_pred
)

adjusted_r2_value = adjusted_r2(
    test_r2,
    len(y_test),
    len(ALL_FEATURES)
)

r2_gap = train_r2 - test_r2


# ============================================================
# MODEL QUALITY
# ============================================================

if test_r2 >= 0.90:
    quality = "Excellent"

elif test_r2 >= 0.80:
    quality = "Very Good"

elif test_r2 >= 0.70:
    quality = "Good"

elif test_r2 >= 0.60:
    quality = "Moderate"

elif test_r2 >= 0.50:
    quality = "Weak"

else:
    quality = "Poor"


# ============================================================
# OVERFITTING CHECK
# ============================================================

if r2_gap > 0.15:

    generalization = "Possible Overfitting"

elif r2_gap > 0.08:

    generalization = "Mild Overfitting"

else:

    generalization = "Good Generalization"


# ============================================================
# PRINT EVALUATION FIRST
# ============================================================

print("\n" + "=" * 70)
print("MODEL EVALUATION")
print("=" * 70)

print(f"\nTraining R²        : {train_r2:.4f}")
print(f"Testing R²         : {test_r2:.4f}")
print(f"Adjusted R²        : {adjusted_r2_value:.4f}")

print(f"\nMAE                : {mae:.4f}")
print(f"MSE                : {mse:.4f}")
print(f"RMSE               : {rmse:.4f}")
print(f"MAPE               : {mape:.2f}%")
print(f"Explained Variance : {explained_variance:.4f}")

print(f"\nR² Gap             : {r2_gap:.4f}")

print(f"\nModel Quality      : {quality}")
print(f"Generalization     : {generalization}")

print(f"\nTraining Time      : {training_time:.2f} seconds")
print(f"Prediction Time    : {prediction_time:.4f} seconds")

print("\n" + "=" * 70)


# ============================================================
# SAMPLE PREDICTION
# ============================================================

print("SAMPLE PREDICTION")
print("=" * 70)

sample_input = X_test.iloc[[0]].copy()

sample_actual = y_test.iloc[0]

sample_prediction = pipeline.predict(
    sample_input
)[0]

sample_prediction = np.clip(
    sample_prediction,
    0,
    100
)

print(f"\nActual Fault Occurrence Rate    : {sample_actual:.2f}%")
print(f"Predicted Fault Occurrence Rate : {sample_prediction:.2f}%")

print("\nInput used:")

for col in ALL_FEATURES:
    print(
        f"{col}: {sample_input.iloc[0][col]}"
    )


# ============================================================
# SAVE MODEL ONLY AFTER EVALUATION
# ============================================================

print("\n" + "=" * 70)
print("SAVING MODEL")
print("=" * 70)

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


# Save COMPLETE pipeline
# This includes:
# - imputation
# - one-hot encoding
# - XGBoost model

joblib.dump(
    pipeline,
    MODEL_PATH
)


# ============================================================
# SAVE INFORMATION / REPORT
# ============================================================

report = f"""
============================================================
XGBOOST FAULT OCCURRENCE RATE PREDICTION MODEL
============================================================

MODEL
------------------------------------------------------------
Algorithm: XGBoost Regressor
Target: {TARGET}

Dataset
------------------------------------------------------------
Dataset path: {DATA_PATH}
Total usable rows: {len(X)}
Training samples: {len(X_train)}
Testing samples: {len(X_test)}

Features
------------------------------------------------------------

Numeric Features:
{chr(10).join("- " + x for x in NUMERIC_FEATURES)}

Categorical Features:
{chr(10).join("- " + x for x in CATEGORICAL_FEATURES)}

Preprocessing
------------------------------------------------------------
Numeric:
- Median imputation

Categorical:
- Most frequent imputation
- One-hot encoding
- Unknown categories ignored

XGBoost Configuration
------------------------------------------------------------
n_estimators       = 300
learning_rate      = 0.05
max_depth          = 8
min_child_weight   = 3
subsample          = 0.8
colsample_bytree   = 0.8
objective          = reg:squarederror
eval_metric        = rmse
tree_method        = hist
random_state       = 42
n_jobs             = -1

Evaluation
------------------------------------------------------------
Training R²        : {train_r2:.4f}
Testing R²         : {test_r2:.4f}
Adjusted R²        : {adjusted_r2_value:.4f}

MAE                : {mae:.4f}
MSE                : {mse:.4f}
RMSE               : {rmse:.4f}
MAPE               : {mape:.2f}%
Explained Variance : {explained_variance:.4f}

R² Gap             : {r2_gap:.4f}

Model Quality      : {quality}
Generalization     : {generalization}

Performance
------------------------------------------------------------
Training Time      : {training_time:.2f} seconds
Prediction Time    : {prediction_time:.4f} seconds

Output
------------------------------------------------------------
Model file:
{MODEL_PATH}

The saved JOBLIB file contains the complete sklearn pipeline,
including preprocessing and the trained XGBoost model.

This means the backend can load the single JOBLIB file and
directly provide raw feature values for prediction.

Sample Prediction
------------------------------------------------------------
Actual:
{sample_actual:.2f}%

Predicted:
{sample_prediction:.2f}%

============================================================
IMPORTANT
============================================================

Fault Occurrence Rate (%) should be checked for possible
data leakage.

If the target was mathematically calculated from some of
the input features, a very high R² may not represent real
predictive performance.

============================================================
"""

with open(
    INFO_PATH,
    "w",
    encoding="utf-8"
) as f:

    f.write(report)


# ============================================================
# FINAL
# ============================================================

print(f"\nModel saved successfully:")
print(MODEL_PATH)

print(f"\nModel information saved:")
print(INFO_PATH)

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)