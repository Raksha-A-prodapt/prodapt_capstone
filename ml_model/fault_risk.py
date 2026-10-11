"""Train the fault-occurrence-rate model used by the Prediction Agent."""

from __future__ import annotations

import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "telecom_network_incidents_with_id.csv"
MODEL_PATH = Path(os.getenv(
    "FAULT_MODEL_OUTPUT",
    str(PROJECT_ROOT / "ml_model" / "models" / "fault_tolerance_model.joblib"),
))
TARGET = "Fault Occurrence Rate (%)"

NUMERIC_FEATURES = [
    "Cell Availability (%)", "MTTR (hours)", "Throughput (Mbps)",
    "Latency (ms)", "Packet Loss Rate (%)", "Call Drop Rate (%)",
    "Handover Success Rate (%)", "Alarm Count", "Critical Alarm Count",
    "Parameter Changes", "Successful Configuration Changes (%)",
    "Data Usage (GB)", "User Count", "Signal Strength (dBm)",
    "Jitter (ms)", "Connection Setup Success Rate (%)", "Security Incidents",
    "Authentication Failures", "Temperature (�C)", "Humidity (%)",
]
CATEGORICAL_FEATURES = ["Season", "Weather"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def _canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    for column in list(df.columns):
        if str(column).startswith("Temperature (") and column != "Temperature (�C)":
            df = df.rename(columns={column: "Temperature (�C)"})
    return df


def build_model() -> tuple[Pipeline, pd.DataFrame, pd.DataFrame]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")
    df = _canonicalize_columns(pd.read_csv(DATA_PATH))
    df.columns = df.columns.str.strip()
    missing = [column for column in FEATURES + [TARGET] if column not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    for column in NUMERIC_FEATURES + [TARGET]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=[TARGET]).copy()
    if len(df) < 20:
        raise ValueError("At least 20 usable rows are required.")

    x_train, x_test, y_train, y_test = train_test_split(
        df[FEATURES], df[TARGET], test_size=0.2, random_state=42
    )
    preprocessing = ColumnTransformer([
        ("numeric", SimpleImputer(strategy="median"), NUMERIC_FEATURES),
        ("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]), CATEGORICAL_FEATURES),
    ])
    model = Pipeline([
        ("preprocessing", preprocessing),
        ("regressor", XGBRegressor(
            n_estimators=50, learning_rate=0.05, max_depth=8,
            min_child_weight=3, subsample=0.8, colsample_bytree=0.8,
            objective="reg:squarederror", eval_metric="rmse",
            random_state=42, n_jobs=1, tree_method="hist",
        )),
    ])
    model.fit(x_train, y_train)
    return model, x_test, y_test


def risk_category(rate: float) -> str:
    if rate <= 30:
        return "LOW"
    if rate <= 60:
        return "MEDIUM"
    if rate <= 80:
        return "HIGH"
    return "CRITICAL"


def main() -> None:
    model, x_test, y_test = build_model()
    predictions = model.predict(x_test).clip(0, 100)
    mae = mean_absolute_error(y_test, predictions)
    rmse = mean_squared_error(y_test, predictions) ** 0.5
    r2 = r2_score(y_test, predictions)
    print(f"Fault model: MAE={mae:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}")
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Save the pipeline itself; the runtime agent calls .predict(DataFrame).
    joblib.dump(model, MODEL_PATH)
    sample = float(model.predict(x_test.iloc[[0]])[0])
    print(f"Saved fault model: {MODEL_PATH}")
    print(f"Sample prediction: {sample:.3f}% ({risk_category(sample)})")


if __name__ == "__main__":
    main()
