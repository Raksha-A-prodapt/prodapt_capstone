# """Train the seven-KPI network-performance model used by the agent."""

# from __future__ import annotations

# import os
# from pathlib import Path

# import joblib
# import pandas as pd
# from sklearn.compose import ColumnTransformer
# from sklearn.impute import SimpleImputer
# from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
# from sklearn.model_selection import train_test_split
# from sklearn.multioutput import MultiOutputRegressor
# from sklearn.pipeline import Pipeline
# from sklearn.preprocessing import OneHotEncoder
# from xgboost import XGBRegressor


# PROJECT_ROOT = Path(__file__).resolve().parents[1]
# DATA_PATH = PROJECT_ROOT / "data" / "telecom_network_incidents_with_id.csv"
# MODEL_PATH = Path(os.getenv(
#     "NETWORK_PERFORMANCE_MODEL_OUTPUT",
#     str(PROJECT_ROOT / "ml_model" / "models" / "network_performance_model.joblib"),
# ))

# NUMERIC_FEATURES = [
#     "Cell Availability (%)", "MTTR (hours)", "Latency (ms)",
#     "Packet Loss Rate (%)", "Call Drop Rate (%)", "Handover Success Rate (%)",
#     "Alarm Count", "Critical Alarm Count", "Parameter Changes",
#     "Successful Configuration Changes (%)", "Data Usage (GB)", "User Count",
#     "Signal Strength (dBm)", "Jitter (ms)", "Connection Setup Success Rate (%)",
#     "Security Incidents", "Authentication Failures", "Temperature (�C)",
#     "Humidity (%)", "Fault Occurrence Rate (%)",
# ]
# CATEGORICAL_FEATURES = ["Season", "Weather", "City", "State"]
# TARGETS = [
#     "Throughput (Mbps)", "Latency (ms)", "Packet Loss Rate (%)",
#     "Call Drop Rate (%)", "Handover Success Rate (%)", "Jitter (ms)",
#     "Connection Setup Success Rate (%)",
# ]
# FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


# def _canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
#     """Normalize the historical temperature-header encoding variation."""
#     for column in list(df.columns):
#         if str(column).startswith("Temperature (") and column != "Temperature (�C)":
#             df = df.rename(columns={column: "Temperature (�C)"})
#     return df


# def build_model() -> tuple[Pipeline, pd.DataFrame, pd.DataFrame]:
#     if not DATA_PATH.exists():
#         raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

#     df = _canonicalize_columns(pd.read_csv(DATA_PATH))
#     df.columns = df.columns.str.strip()
#     missing = [column for column in FEATURES + TARGETS if column not in df.columns]
#     if missing:
#         raise ValueError(f"Missing columns: {missing}")

#     for column in NUMERIC_FEATURES + TARGETS:
#         df[column] = pd.to_numeric(df[column], errors="coerce")
#     df = df.dropna(subset=TARGETS).copy()
#     if len(df) < 20:
#         raise ValueError("At least 20 complete rows are required.")

#     x_train, x_test, y_train, y_test = train_test_split(
#         df[FEATURES], df[TARGETS], test_size=0.2, random_state=42
#     )
#     preprocessing = ColumnTransformer([
#         ("numeric", SimpleImputer(strategy="median"), NUMERIC_FEATURES),
#         ("categorical", Pipeline([
#             ("imputer", SimpleImputer(strategy="most_frequent")),
#             ("encoder", OneHotEncoder(handle_unknown="ignore")),
#         ]), CATEGORICAL_FEATURES),
#     ])
#     model = Pipeline([
#         ("preprocessing", preprocessing),
#         ("regressor", MultiOutputRegressor(XGBRegressor(
#             n_estimators=50,
#             learning_rate=0.05,
#             max_depth=8,
#             min_child_weight=3,
#             subsample=0.8,
#             colsample_bytree=0.8,
#             objective="reg:squarederror",
#             eval_metric="rmse",
#             tree_method="hist",
#             random_state=42,
#             n_jobs=1,
#         ))),
#     ])
#     model.fit(x_train, y_train)
#     return model, x_test, y_test


# def main() -> None:
#     model, x_test, y_test = build_model()
#     predictions = model.predict(x_test)
#     print("Seven-KPI Network Performance Model Evaluation")
#     for index, target in enumerate(TARGETS):
#         actual = y_test[target]
#         predicted = predictions[:, index]
#         print(
#             f"{target}: MAE={mean_absolute_error(actual, predicted):.4f}, "
#             f"RMSE={mean_squared_error(actual, predicted) ** 0.5:.4f}, "
#             f"R2={r2_score(actual, predicted):.4f}"
#         )

#     MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
#     # Save the pipeline itself. The runtime agent expects .predict(DataFrame).
#     joblib.dump(model, MODEL_PATH)
#     sample_prediction = model.predict(x_test.iloc[[0]])[0]
#     print(f"Saved seven-output model: {MODEL_PATH}")
#     print(f"Validated output shape: {(1, len(sample_prediction))}")
#     for target, value in zip(TARGETS, sample_prediction):
#         print(f"  {target}: {value:.3f}")


# if __name__ == "__main__":
#     main()

"""Train the seven-KPI network-performance prediction model."""

from __future__ import annotations

import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor


# --------------------------------------------------
# PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "telecom_network_incidents_with_id.csv"
)

MODEL_PATH = Path(
    os.getenv(
        "NETWORK_PERFORMANCE_MODEL_OUTPUT",
        str(
            PROJECT_ROOT
            / "ml_model"
            / "models"
            / "network_performance_model.joblib"
        ),
    )
)


# --------------------------------------------------
# INPUT FEATURES
# 12 numeric + 2 categorical = 14 inputs
# --------------------------------------------------

NUMERIC_FEATURES = [
    "Cell Availability (%)",
    "Alarm Count",
    "Critical Alarm Count",
    "Parameter Changes",
    "Successful Configuration Changes (%)",
    "Data Usage (GB)",
    "User Count",
    "Signal Strength (dBm)",
    "Security Incidents",
    "Authentication Failures",
    "Temperature (°C)",
    "Humidity (%)",
]

CATEGORICAL_FEATURES = [
    "Season",
    "Weather",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


# --------------------------------------------------
# SEVEN OUTPUT KPIs
# --------------------------------------------------

TARGETS = [
    "Throughput (Mbps)",
    "Latency (ms)",
    "Packet Loss Rate (%)",
    "Call Drop Rate (%)",
    "Handover Success Rate (%)",
    "Jitter (ms)",
    "Connection Setup Success Rate (%)",
]


# --------------------------------------------------
# DATA PREPARATION
# --------------------------------------------------

def canonicalize_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize column names and temperature encoding."""

    df.columns = df.columns.str.strip()

    for column in list(df.columns):
        if column.startswith("Temperature ("):
            df = df.rename(
                columns={
                    column: "Temperature (°C)"
                }
            )

    return df


def build_model():
    """Prepare data, train model, and return test data."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)
    df = canonicalize_columns(df)

    required_columns = FEATURES + TARGETS

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing dataset columns: {missing_columns}"
        )

    # Convert numeric columns safely.
    for column in NUMERIC_FEATURES + TARGETS:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # Remove rows without valid target values.
    df = df.dropna(subset=TARGETS).copy()

    if len(df) < 20:
        raise ValueError(
            "At least 20 usable rows are required."
        )

    X = df[FEATURES]
    y = df[TARGETS]

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
        )
    )

    # Numeric preprocessing.
    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
        ]
    )

    # Categorical preprocessing.
    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
            ),
        ]
    )

    preprocessing = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    # Base regression model.
    base_model = XGBRegressor(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=5,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        eval_metric="rmse",
        random_state=42,
        n_jobs=1,
        tree_method="hist",
    )

    # One regressor per KPI.
    model = Pipeline(
        steps=[
            (
                "preprocessing",
                preprocessing,
            ),
            (
                "regressor",
                MultiOutputRegressor(
                    base_model
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)

    return model, X_test, y_test


# --------------------------------------------------
# MODEL EVALUATION
# --------------------------------------------------

def evaluate_model(
    model,
    X_test: pd.DataFrame,
    y_test: pd.DataFrame,
) -> None:
    """Print evaluation metrics for every KPI."""

    predictions = model.predict(X_test)

    print("\nSeven-KPI Network Performance Evaluation")
    print("=" * 55)
    print(f"Test samples: {len(X_test)}")
    print(f"Input features: {len(FEATURES)}")
    print(f"Predicted KPIs: {len(TARGETS)}")
    print("=" * 55)

    for index, target in enumerate(TARGETS):
        actual = y_test[target]
        predicted = predictions[:, index]

        mae = mean_absolute_error(
            actual,
            predicted,
        )

        rmse = mean_squared_error(
            actual,
            predicted,
        ) ** 0.5

        r2 = r2_score(
            actual,
            predicted,
        )

        print(f"\nTarget: {target}")
        print(f"MAE : {mae:.4f}")
        print(f"RMSE: {rmse:.4f}")
        print(f"R²  : {r2:.4f}")


# --------------------------------------------------
# SAVE AND VERIFY MODEL
# --------------------------------------------------

def save_and_verify_model(
    model,
    X_test: pd.DataFrame,
) -> None:
    """Save the model and verify its seven-output contract."""

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(model, MODEL_PATH)

    # Reload the saved artifact.
    loaded_model = joblib.load(MODEL_PATH)

    # Verify predictions on one sample.
    sample_input = X_test.iloc[[0]]
    sample_prediction = loaded_model.predict(
        sample_input
    )

    expected_shape = (1, len(TARGETS))

    if sample_prediction.shape != expected_shape:
        raise RuntimeError(
            "Unexpected prediction shape: "
            f"{sample_prediction.shape}; "
            f"expected {expected_shape}"
        )

    print(f"\nModel saved successfully: {MODEL_PATH}")
    print(
        "Verified prediction output shape: "
        f"{sample_prediction.shape}"
    )

    print("\nSample predictions:")

    for target, value in zip(
        TARGETS,
        sample_prediction[0],
    ):
        print(f"{target}: {value:.3f}")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main() -> None:
    model, X_test, y_test = build_model()

    evaluate_model(
        model,
        X_test,
        y_test,
    )

    save_and_verify_model(
        model,
        X_test,
    )


if __name__ == "__main__":
    main()
