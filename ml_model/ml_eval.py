"""Evaluation report for all telecom ML prediction models.

This script loads each trained joblib pipeline from `ml_model/models/` and
computes standard regression metrics for both the throughput and fault models.
The output is a single summary JSON plus a console report.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    explained_variance_score,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.prediction_config import (
    FAULT_FEATURES,
    FAULT_NUMERIC_FEATURES,
    FAULT_TARGET,
    THROUGHPUT_FEATURES,
    THROUGHPUT_NUMERIC_FEATURES,
    THROUGHPUT_TARGET,
)

DATA_PATH = PROJECT_ROOT / "data" / "telecom_network_incidents_with_id.csv"
MODELS_DIR = PROJECT_ROOT / "ml_model" / "models"
OUTPUT_PATH = MODELS_DIR / "evaluation_summary.json"


def safe_mape(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)
    mask = y_true_arr != 0
    if not np.any(mask):
        return float("nan")
    return float(np.mean(np.abs((y_true_arr[mask] - y_pred_arr[mask]) / y_true_arr[mask])) * 100)


def adjusted_r2(r2_value: float, n_samples: int, n_features: int) -> float:
    if n_samples <= n_features + 1:
        return float("nan")
    return float(1 - ((1 - r2_value) * (n_samples - 1) / (n_samples - n_features - 1)))


def _prepare_dataset(df: pd.DataFrame, features: Sequence[str], target: str) -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()
    df.columns = [str(col).replace("�C", "°C") for col in df.columns]

    required = list(features) + [target]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns for evaluation: {missing}")

    frame = df[required].copy()

    numeric_features = []
    if set(features) == set(THROUGHPUT_FEATURES):
        numeric_features = THROUGHPUT_NUMERIC_FEATURES
    elif set(features) == set(FAULT_FEATURES):
        numeric_features = FAULT_NUMERIC_FEATURES
    else:
        numeric_features = [
            col for col in features if pd.api.types.is_numeric_dtype(df[col])
        ]

    for column in list(numeric_features) + [target]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.dropna(subset=list(numeric_features) + [target]).reset_index(drop=True)
    return frame[features], frame[target]


def evaluate_model(model_path: Path, features: Sequence[str], target: str, model_name: str) -> Dict[str, Any]:
    df = pd.read_csv(DATA_PATH)
    X, y = _prepare_dataset(df, features, target)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
    )

    model = joblib.load(model_path)

    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    if target == FAULT_TARGET:
        y_train_pred = np.clip(y_train_pred, 0, 100)
        y_test_pred = np.clip(y_test_pred, 0, 100)

    train_r2 = float(r2_score(y_train, y_train_pred))
    test_r2 = float(r2_score(y_test, y_test_pred))
    mae = float(mean_absolute_error(y_test, y_test_pred))
    mse = float(mean_squared_error(y_test, y_test_pred))
    rmse = float(np.sqrt(mse))
    mape = float(safe_mape(y_test, y_test_pred))
    explained_variance = float(explained_variance_score(y_test, y_test_pred))
    adj_r2 = float(adjusted_r2(test_r2, len(y_test), len(features)))
    r2_gap = float(train_r2 - test_r2)

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

    if r2_gap > 0.15:
        generalization = "Possible Overfitting"
    elif r2_gap > 0.08:
        generalization = "Mild Overfitting"
    else:
        generalization = "Good Generalization"

    return {
        "model_name": model_name,
        "target": target,
        "training_samples": int(len(X_train)),
        "testing_samples": int(len(X_test)),
        "feature_count": int(len(features)),
        "metrics": {
            "R2": test_r2,
            "Adjusted_R2": adj_r2,
            "MAE": mae,
            "MSE": mse,
            "RMSE": rmse,
            "MAPE_percent": mape,
            "Explained_Variance": explained_variance,
            "Training_R2": train_r2,
            "Testing_R2": test_r2,
            "Train_Test_R2_Gap": r2_gap,
        },
        "quality": quality,
        "generalization": generalization,
    }


def main() -> None:
    summary: Dict[str, Any] = {
        "dataset_path": str(DATA_PATH),
        "models": {},
    }

    model_configs = [
        {
            "name": "network_performance_model",
            "model_path": MODELS_DIR / "network_performance_model.joblib",
            "features": THROUGHPUT_FEATURES,
            "target": THROUGHPUT_TARGET,
        },
        {
            "name": "fault_tolerance_model",
            "model_path": MODELS_DIR / "fault_tolerance_model.joblib",
            "features": FAULT_FEATURES,
            "target": FAULT_TARGET,
        },
    ]

    for config in model_configs:
        summary["models"][config["name"]] = evaluate_model(
            model_path=config["model_path"],
            features=config["features"],
            target=config["target"],
            model_name=config["name"],
        )

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("=" * 80)
    print("ML MODEL EVALUATION SUMMARY")
    print("=" * 80)
    for model_name, result in summary["models"].items():
        metrics = result["metrics"]
        print(f"\nModel: {model_name}")
        print(f"Target: {result['target']}")
        print(f"Training samples: {result['training_samples']}")
        print(f"Testing samples: {result['testing_samples']}")
        print(f"R²: {metrics['R2']:.4f}")
        print(f"Adjusted R²: {metrics['Adjusted_R2']:.4f}")
        print(f"MAE: {metrics['MAE']:.4f}")
        print(f"MSE: {metrics['MSE']:.4f}")
        print(f"RMSE: {metrics['RMSE']:.4f}")
        print(f"MAPE: {metrics['MAPE_percent']:.2f}%")
        print(f"Explained Variance: {metrics['Explained_Variance']:.4f}")
        print(f"Training R²: {metrics['Training_R2']:.4f}")
        print(f"Testing R²: {metrics['Testing_R2']:.4f}")
        print(f"Train-Test R² Gap: {metrics['Train_Test_R2_Gap']:.4f}")
        print(f"Quality: {result['quality']}")
        print(f"Generalization: {result['generalization']}")

    print(f"\nSaved detailed report to: {OUTPUT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
