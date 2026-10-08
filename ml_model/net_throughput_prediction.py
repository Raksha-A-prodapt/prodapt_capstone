
# """
# ============================================================
# NETWORK PERFORMANCE PREDICTION MODEL
# ============================================================

# Purpose:
#     Predict network throughput (Mbps) from telecom network
#     conditions.

# Model:
#     XGBoost Regressor

# Target:
#     Throughput (Mbps)

# Dataset:
#     100,000 telecom network incidents

# Current stage:
#     TRAIN + EVALUATE ONLY

# IMPORTANT:
#     No pickle/joblib model is saved at this stage.
#     After reviewing the evaluation results, the model
#     can be saved in a later version.

# Evaluation Metrics:
#     - R²
#     - Adjusted R²
#     - MAE
#     - MSE
#     - RMSE
#     - MAPE
#     - Explained Variance
#     - Training R²
#     - Testing R²
#     - Train-Test R² Gap
# ============================================================
# """

# import os
# import time

# import numpy as np
# import pandas as pd

# from xgboost import XGBRegressor

# from sklearn.model_selection import train_test_split

# from sklearn.metrics import (
#     mean_absolute_error,
#     mean_squared_error,
#     r2_score,
#     mean_absolute_percentage_error,
#     explained_variance_score
# )

# from sklearn.preprocessing import OneHotEncoder
# from sklearn.compose import ColumnTransformer
# from sklearn.pipeline import Pipeline


# # ============================================================
# # CONFIGURATION
# # ============================================================

# DATA_PATH = (
#     "D:/raksha/capstone/try2/data/"
#     "telecom_network_incidents_with_id.csv"
# )

# TARGET = "Throughput (Mbps)"


# # ============================================================
# # FEATURES
# # ============================================================

# NUMERIC_FEATURES = [

#     "Cell Availability (%)",

#     "MTTR (hours)",

#     "Latency (ms)",

#     "Packet Loss Rate (%)",

#     "Call Drop Rate (%)",

#     "Handover Success Rate (%)",

#     "Alarm Count",

#     "Critical Alarm Count",

#     "Parameter Changes",

#     "Successful Configuration Changes (%)",

#     "Data Usage (GB)",

#     "User Count",

#     "Signal Strength (dBm)",

#     "Jitter (ms)",

#     "Connection Setup Success Rate (%)",

#     "Security Incidents",

#     "Authentication Failures",

#     "Temperature (°C)",

#     "Humidity (%)",

#     "Fault Occurrence Rate (%)"
# ]


# CATEGORICAL_FEATURES = [

#     "Season",

#     "Weather",

#     "City",

#     "State"
# ]


# # ============================================================
# # LOAD DATA
# # ============================================================

# def load_data(path):

#     print()
#     print("=" * 70)
#     print("STEP 1 — LOADING DATASET")
#     print("=" * 70)

#     if not os.path.exists(path):

#         raise FileNotFoundError(
#             f"Dataset not found:\n{path}"
#         )

#     df = pd.read_csv(path)

#     print()
#     print("Dataset loaded successfully.")

#     print(f"Rows       : {len(df):,}")
#     print(f"Columns    : {len(df.columns)}")

#     print()
#     print("Target:")
#     print(f"    {TARGET}")

#     print()
#     print("Numeric features:")
#     print(f"    {len(NUMERIC_FEATURES)}")

#     print()
#     print("Categorical features:")
#     print(f"    {len(CATEGORICAL_FEATURES)}")

#     return df


# # ============================================================
# # PREPARE DATA
# # ============================================================

# def prepare_data(df):

#     print()
#     print("=" * 70)
#     print("STEP 2 — PREPARING DATA")
#     print("=" * 70)

#     required_columns = (
#         NUMERIC_FEATURES
#         + CATEGORICAL_FEATURES
#         + [TARGET]
#     )

#     missing_columns = [

#         column
#         for column in required_columns
#         if column not in df.columns

#     ]

#     if missing_columns:

#         raise ValueError(
#             "Missing columns:\n"
#             + "\n".join(missing_columns)
#         )

#     data = df[required_columns].copy()

#     # --------------------------------------------------------
#     # Convert numeric columns
#     # --------------------------------------------------------

#     print()
#     print("Converting numeric columns...")

#     for column in NUMERIC_FEATURES + [TARGET]:

#         data[column] = pd.to_numeric(
#             data[column],
#             errors="coerce"
#         )

#     rows_before = len(data)

#     # --------------------------------------------------------
#     # Remove missing target
#     # --------------------------------------------------------

#     data = data.dropna(
#         subset=[TARGET]
#     )

#     rows_after_target = len(data)

#     print(
#         f"Rows after target cleaning : "
#         f"{rows_after_target:,}"
#     )

#     # --------------------------------------------------------
#     # Remove missing feature values
#     # --------------------------------------------------------

#     data = data.dropna(
#         subset=NUMERIC_FEATURES + CATEGORICAL_FEATURES
#     )

#     rows_after_features = len(data)

#     print(
#         f"Rows after feature cleaning: "
#         f"{rows_after_features:,}"
#     )

#     removed = rows_before - rows_after_features

#     print(
#         f"Rows removed               : "
#         f"{removed:,}"
#     )

#     # --------------------------------------------------------
#     # X and y
#     # --------------------------------------------------------

#     X = data[
#         NUMERIC_FEATURES + CATEGORICAL_FEATURES
#     ]

#     y = data[TARGET]

#     print()
#     print("Final dataset:")
#     print(f"    X rows : {len(X):,}")
#     print(f"    y rows : {len(y):,}")

#     return X, y


# # ============================================================
# # BUILD XGBOOST MODEL
# # ============================================================

# def build_model():

#     print()
#     print("=" * 70)
#     print("STEP 3 — BUILDING XGBOOST MODEL")
#     print("=" * 70)

#     # --------------------------------------------------------
#     # Preprocessing
#     # --------------------------------------------------------

#     preprocessor = ColumnTransformer(

#         transformers=[

#             (
#                 "numeric",

#                 "passthrough",

#                 NUMERIC_FEATURES
#             ),

#             (
#                 "categorical",

#                 OneHotEncoder(
#                     handle_unknown="ignore"
#                 ),

#                 CATEGORICAL_FEATURES
#             )
#         ]
#     )

#     # --------------------------------------------------------
#     # XGBoost
#     # --------------------------------------------------------

#     model = XGBRegressor(

#         n_estimators=300,

#         learning_rate=0.05,

#         max_depth=8,

#         min_child_weight=3,

#         subsample=0.8,

#         colsample_bytree=0.8,

#         objective="reg:squarederror",

#         eval_metric="rmse",

#         random_state=42,

#         n_jobs=-1,

#         tree_method="hist"
#     )

#     pipeline = Pipeline(

#         steps=[

#             (
#                 "preprocessor",
#                 preprocessor
#             ),

#             (
#                 "model",
#                 model
#             )
#         ]
#     )

#     print()
#     print("Model: XGBRegressor")

#     print("Configuration:")
#     print(f"    n_estimators     : 300")
#     print(f"    learning_rate    : 0.05")
#     print(f"    max_depth        : 8")
#     print(f"    min_child_weight: 3")
#     print(f"    subsample        : 0.8")
#     print(f"    colsample_bytree : 0.8")
#     print(f"    tree_method      : hist")
#     print(f"    n_jobs           : -1")

#     return pipeline


# # ============================================================
# # TRAIN MODEL
# # ============================================================

# def train_model(
#     X_train,
#     y_train
# ):

#     print()
#     print("=" * 70)
#     print("STEP 4 — TRAINING MODEL")
#     print("=" * 70)

#     print()
#     print(
#         f"Training samples: "
#         f"{len(X_train):,}"
#     )

#     print(
#         f"Training target mean: "
#         f"{y_train.mean():.4f} Mbps"
#     )

#     print()
#     print("Training XGBoost...")
#     print("Please wait...")

#     start_time = time.time()

#     pipeline = build_model()

#     pipeline.fit(
#         X_train,
#         y_train
#     )

#     training_time = time.time() - start_time

#     print()
#     print("Training completed.")

#     print(
#         f"Training time: "
#         f"{training_time:.2f} seconds"
#     )

#     print(
#         f"Training time: "
#         f"{training_time / 60:.2f} minutes"
#     )

#     return pipeline


# # ============================================================
# # EVALUATE MODEL
# # ============================================================

# def evaluate_model(
#     model,
#     X_train,
#     y_train,
#     X_test,
#     y_test
# ):

#     print()
#     print("=" * 70)
#     print("STEP 5 — MODEL EVALUATION")
#     print("=" * 70)

#     # --------------------------------------------------------
#     # Predictions
#     # --------------------------------------------------------

#     print()
#     print("Generating predictions...")

#     prediction_start = time.time()

#     train_predictions = model.predict(
#         X_train
#     )

#     test_predictions = model.predict(
#         X_test
#     )

#     prediction_time = (
#         time.time() - prediction_start
#     )

#     print(
#         f"Prediction time: "
#         f"{prediction_time:.2f} seconds"
#     )

#     # ========================================================
#     # TRAINING METRICS
#     # ========================================================

#     train_r2 = r2_score(
#         y_train,
#         train_predictions
#     )

#     # ========================================================
#     # TEST METRICS
#     # ========================================================

#     mae = mean_absolute_error(
#         y_test,
#         test_predictions
#     )

#     mse = mean_squared_error(
#         y_test,
#         test_predictions
#     )

#     rmse = np.sqrt(mse)

#     r2 = r2_score(
#         y_test,
#         test_predictions
#     )

#     mape = (
#         mean_absolute_percentage_error(
#             y_test,
#             test_predictions
#         )
#         * 100
#     )

#     explained_variance = (
#         explained_variance_score(
#             y_test,
#             test_predictions
#         )
#     )

#     # ========================================================
#     # ADJUSTED R2
#     # ========================================================

#     n = len(y_test)

#     # Number of original input features
#     p = len(
#         NUMERIC_FEATURES
#         + CATEGORICAL_FEATURES
#     )

#     if n > p + 1:

#         adjusted_r2 = (

#             1
#             -
#             (
#                 (1 - r2)
#                 * (n - 1)
#             )
#             /
#             (n - p - 1)

#         )

#     else:

#         adjusted_r2 = np.nan

#     # ========================================================
#     # TRAIN-TEST GAP
#     # ========================================================

#     r2_difference = (
#         train_r2 - r2
#     )

#     # ========================================================
#     # PRINT EVALUATION
#     # ========================================================

#     print()
#     print("=" * 70)
#     print("          NETWORK PERFORMANCE MODEL")
#     print("              EVALUATION RESULTS")
#     print("=" * 70)

#     print()
#     print("MODEL")
#     print("-" * 70)

#     print(
#         "Algorithm             : XGBoost Regressor"
#     )

#     print(
#         "Target                : Throughput (Mbps)"
#     )

#     print(
#         f"Training samples      : {len(X_train):,}"
#     )

#     print(
#         f"Testing samples       : {len(X_test):,}"
#     )

#     print()
#     print("REGRESSION METRICS")
#     print("-" * 70)

#     print(
#         f"R² Score              : {r2:.4f}"
#     )

#     print(
#         f"Adjusted R²           : {adjusted_r2:.4f}"
#     )

#     print(
#         f"MAE                   : {mae:.4f} Mbps"
#     )

#     print(
#         f"MSE                   : {mse:.4f}"
#     )

#     print(
#         f"RMSE                  : {rmse:.4f} Mbps"
#     )

#     print(
#         f"MAPE                  : {mape:.2f}%"
#     )

#     print(
#         f"Explained Variance    : "
#         f"{explained_variance:.4f}"
#     )

#     # ========================================================
#     # GENERALIZATION
#     # ========================================================

#     print()
#     print("MODEL GENERALIZATION")
#     print("-" * 70)

#     print(
#         f"Training R²           : "
#         f"{train_r2:.4f}"
#     )

#     print(
#         f"Testing R²            : "
#         f"{r2:.4f}"
#     )

#     print(
#         f"Train-Test R² Gap     : "
#         f"{r2_difference:.4f}"
#     )

#     # ========================================================
#     # OVERFITTING CHECK
#     # ========================================================

#     print()
#     print("OVERFITTING CHECK")
#     print("-" * 70)

#     if r2_difference > 0.15:

#         model_status = (
#             "Possible Overfitting"
#         )

#     elif r2_difference > 0.08:

#         model_status = (
#             "Mild Overfitting"
#         )

#     else:

#         model_status = (
#             "Good Generalization"
#         )

#     print(
#         f"Model Status          : "
#         f"{model_status}"
#     )

#     # ========================================================
#     # MODEL QUALITY
#     # ========================================================

#     print()
#     print("OVERALL MODEL QUALITY")
#     print("-" * 70)

#     if r2 >= 0.90:

#         quality = "Excellent"

#     elif r2 >= 0.80:

#         quality = "Very Good"

#     elif r2 >= 0.70:

#         quality = "Good"

#     elif r2 >= 0.60:

#         quality = "Moderate"

#     elif r2 >= 0.50:

#         quality = "Weak"

#     else:

#         quality = "Poor"

#     print(
#         f"Overall Model Quality : "
#         f"{quality}"
#     )

#     print("=" * 70)

#     # ========================================================
#     # RETURN METRICS
#     # ========================================================

#     return {

#         "r2": r2,

#         "adjusted_r2": adjusted_r2,

#         "mae": mae,

#         "mse": mse,

#         "rmse": rmse,

#         "mape": mape,

#         "explained_variance":
#             explained_variance,

#         "train_r2":
#             train_r2,

#         "r2_gap":
#             r2_difference
#     }


# # ============================================================
# # EXAMPLE PREDICTION
# # ============================================================

# def predict_throughput(
#     model,
#     network_data
# ):

#     input_df = pd.DataFrame(
#         [network_data]
#     )

#     prediction = model.predict(
#         input_df
#     )

#     return float(
#         prediction[0]
#     )


# # ============================================================
# # MAIN
# # ============================================================

# def main():

#     overall_start = time.time()

#     print()
#     print("=" * 70)
#     print("        TELECOM NETWORK PERFORMANCE PREDICTION")
#     print("=" * 70)

#     print()
#     print("CURRENT MODE")
#     print("-" * 70)

#     print(
#         "Training + Evaluation only"
#     )

#     print(
#         "Model will NOT be saved."
#     )

#     # --------------------------------------------------------
#     # 1. Load
#     # --------------------------------------------------------

#     df = load_data(
#         DATA_PATH
#     )

#     # --------------------------------------------------------
#     # 2. Prepare
#     # --------------------------------------------------------

#     X, y = prepare_data(
#         df
#     )

#     # --------------------------------------------------------
#     # 3. Train-test split
#     # --------------------------------------------------------

#     print()
#     print("=" * 70)
#     print("STEP 3.5 — TRAIN / TEST SPLIT")
#     print("=" * 70)

#     X_train, X_test, y_train, y_test = (
#         train_test_split(

#             X,
#             y,

#             test_size=0.20,

#             random_state=42
#         )
#     )

#     print()
#     print(
#         f"Training samples : "
#         f"{len(X_train):,}"
#     )

#     print(
#         f"Testing samples  : "
#         f"{len(X_test):,}"
#     )

#     print(
#         f"Training ratio   : 80%"
#     )

#     print(
#         f"Testing ratio    : 20%"
#     )

#     # --------------------------------------------------------
#     # 4. Train
#     # --------------------------------------------------------

#     model = train_model(
#         X_train,
#         y_train
#     )

#     # --------------------------------------------------------
#     # 5. Evaluate
#     # --------------------------------------------------------

#     metrics = evaluate_model(

#         model,

#         X_train,
#         y_train,

#         X_test,
#         y_test
#     )

#     # --------------------------------------------------------
#     # 6. Example prediction
#     # --------------------------------------------------------

#     print()
#     print("=" * 70)
#     print("STEP 6 — EXAMPLE THROUGHPUT PREDICTION")
#     print("=" * 70)

#     example_network = {

#         "Cell Availability (%)": 98.0,

#         "MTTR (hours)": 3.0,

#         "Latency (ms)": 74.3,

#         "Packet Loss Rate (%)": 6.4,

#         "Call Drop Rate (%)": 1.47,

#         "Handover Success Rate (%)": 99.29,

#         "Alarm Count": 13,

#         "Critical Alarm Count": 6.7,

#         "Parameter Changes": 18,

#         "Successful Configuration Changes (%)":
#             91.85,

#         "Data Usage (GB)": 47.49,

#         "User Count": 2442,

#         "Signal Strength (dBm)": -110.12,

#         "Jitter (ms)": 15.67,

#         "Connection Setup Success Rate (%)":
#             99.0,

#         "Security Incidents": 8,

#         "Authentication Failures": 2,

#         "Temperature (°C)": -6.75,

#         "Humidity (%)": 28.79,

#         "Fault Occurrence Rate (%)": 33.58,

#         "Season": "Winter",

#         "Weather": "Clouds",

#         "City": "Schneiderville",

#         "State": "MN"
#     }

#     predicted = predict_throughput(
#         model,
#         example_network
#     )

#     print()

#     print(
#         f"Predicted Throughput : "
#         f"{predicted:.2f} Mbps"
#     )

#     print()
#     print("=" * 70)

#     # --------------------------------------------------------
#     # Total runtime
#     # --------------------------------------------------------

#     total_time = (
#         time.time() - overall_start
#     )

#     print()
#     print(
#         f"Total execution time : "
#         f"{total_time / 60:.2f} minutes"
#     )

#     print()
#     print("=" * 70)
#     print("TRAINING + EVALUATION COMPLETED")
#     print("=" * 70)

#     print()
#     print(
#         "NO MODEL FILE WAS SAVED."
#     )

#     print(
#         "Review the evaluation results first."
#     )

#     print("=" * 70)

#     return model, metrics


# # ============================================================
# # RUN
# # ============================================================

# if __name__ == "__main__":

#     model, metrics = main()



"""
============================================================
TELECOM NETWORK PERFORMANCE PREDICTION MODEL
============================================================

Purpose:
    Predict network throughput (Mbps) from telecom network
    conditions.

Model:
    XGBoost Regressor

Target:
    Throughput (Mbps)

Dataset:
    Telecom network incident dataset

Outputs:
    1. Trained XGBoost pipeline (.joblib)
    2. Model information + evaluation report (.txt)

Evaluation Metrics:
    - R²
    - Adjusted R²
    - MAE
    - MSE
    - RMSE
    - MAPE
    - Explained Variance
    - Training R²
    - Testing R²
    - Train-Test R² Gap

The saved .joblib file contains:
    - Numerical preprocessing
    - Categorical OneHotEncoder
    - Trained XGBoost model

Therefore, the complete pipeline can be loaded directly
in the agent/backend without rebuilding preprocessing.
============================================================
"""

import os
import time
import joblib
import numpy as np
import pandas as pd

from datetime import datetime

from xgboost import XGBRegressor

from sklearn.model_selection import train_test_split

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error,
    explained_variance_score
)

from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline


# ============================================================
# CONFIGURATION
# ============================================================

DATA_PATH = (
    "D:/raksha/capstone/try2/data/"
    "telecom_network_incidents_with_id.csv"
)

MODEL_DIR = "models"

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "network_performance_model.joblib"
)

INFO_PATH = os.path.join(
    MODEL_DIR,
    "network_performance_model_info.txt"
)

TARGET = "Throughput (Mbps)"

RANDOM_STATE = 42

TEST_SIZE = 0.20


# ============================================================
# FEATURES
# ============================================================

NUMERIC_FEATURES = [

    "Cell Availability (%)",

    "MTTR (hours)",

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

    "Humidity (%)",

    "Fault Occurrence Rate (%)"
]


CATEGORICAL_FEATURES = [

    "Season",

    "Weather",

    "City",

    "State"
]


ALL_FEATURES = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data(path):

    print()
    print("=" * 70)
    print("STEP 1 — LOADING DATASET")
    print("=" * 70)

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"\nDataset not found:\n{path}"
        )

    df = pd.read_csv(path)

    print()
    print("Dataset loaded successfully.")

    print(f"Rows       : {len(df):,}")
    print(f"Columns    : {len(df.columns)}")

    print()
    print(f"Target     : {TARGET}")

    print(
        f"Numeric features     : "
        f"{len(NUMERIC_FEATURES)}"
    )

    print(
        f"Categorical features : "
        f"{len(CATEGORICAL_FEATURES)}"
    )

    return df


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(df):

    print()
    print("=" * 70)
    print("STEP 2 — PREPARING DATA")
    print("=" * 70)

    required_columns = (
        ALL_FEATURES
        + [TARGET]
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "\nMissing required columns:\n"
            + "\n".join(
                f"- {column}"
                for column in missing_columns
            )
        )

    data = df[
        required_columns
    ].copy()

    print()
    print("Converting numerical columns...")

    for column in NUMERIC_FEATURES + [TARGET]:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    rows_before = len(data)

    # --------------------------------------------------------
    # Remove missing target
    # --------------------------------------------------------

    data = data.dropna(
        subset=[TARGET]
    )

    rows_after_target = len(data)

    # --------------------------------------------------------
    # Remove missing features
    # --------------------------------------------------------

    data = data.dropna(
        subset=ALL_FEATURES
    )

    rows_after_features = len(data)

    removed = (
        rows_before
        - rows_after_features
    )

    print()
    print(
        f"Original rows            : "
        f"{rows_before:,}"
    )

    print(
        f"After target cleaning    : "
        f"{rows_after_target:,}"
    )

    print(
        f"After feature cleaning   : "
        f"{rows_after_features:,}"
    )

    print(
        f"Rows removed             : "
        f"{removed:,}"
    )

    # --------------------------------------------------------
    # X and y
    # --------------------------------------------------------

    X = data[
        ALL_FEATURES
    ]

    y = data[TARGET]

    print()
    print("Final dataset:")
    print(
        f"    Features : {len(X):,} rows"
    )

    print(
        f"    Target   : {len(y):,} rows"
    )

    print(
        f"    Target mean : "
        f"{y.mean():.4f} Mbps"
    )

    print(
        f"    Target min  : "
        f"{y.min():.4f} Mbps"
    )

    print(
        f"    Target max  : "
        f"{y.max():.4f} Mbps"
    )

    return X, y


# ============================================================
# BUILD MODEL
# ============================================================

def build_model():

    print()
    print("=" * 70)
    print("STEP 3 — BUILDING XGBOOST MODEL")
    print("=" * 70)

    # --------------------------------------------------------
    # Preprocessor
    # --------------------------------------------------------

    preprocessor = ColumnTransformer(

        transformers=[

            (
                "numeric",

                "passthrough",

                NUMERIC_FEATURES
            ),

            (
                "categorical",

                OneHotEncoder(
                    handle_unknown="ignore"
                ),

                CATEGORICAL_FEATURES
            )
        ]
    )

    # --------------------------------------------------------
    # XGBoost
    # --------------------------------------------------------

    model = XGBRegressor(

        n_estimators=300,

        learning_rate=0.05,

        max_depth=8,

        min_child_weight=3,

        subsample=0.8,

        colsample_bytree=0.8,

        objective="reg:squarederror",

        eval_metric="rmse",

        random_state=RANDOM_STATE,

        n_jobs=-1,

        tree_method="hist"
    )

    # --------------------------------------------------------
    # Complete pipeline
    # --------------------------------------------------------

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

    print()
    print("Model: XGBRegressor")

    print()
    print("Configuration:")
    print(
        "    n_estimators      : 300"
    )
    print(
        "    learning_rate     : 0.05"
    )
    print(
        "    max_depth         : 8"
    )
    print(
        "    min_child_weight  : 3"
    )
    print(
        "    subsample         : 0.8"
    )
    print(
        "    colsample_bytree  : 0.8"
    )
    print(
        "    tree_method       : hist"
    )
    print(
        "    random_state      : 42"
    )
    print(
        "    n_jobs            : -1"
    )

    return pipeline


# ============================================================
# TRAIN MODEL
# ============================================================

def train_model(X_train, y_train):

    print()
    print("=" * 70)
    print("STEP 4 — TRAINING MODEL")
    print("=" * 70)

    print()
    print(
        f"Training samples : "
        f"{len(X_train):,}"
    )

    print(
        f"Training target mean : "
        f"{y_train.mean():.4f} Mbps"
    )

    print()
    print("Training XGBoost...")
    print("Please wait...")

    start_time = time.time()

    pipeline = build_model()

    pipeline.fit(
        X_train,
        y_train
    )

    training_time = (
        time.time()
        - start_time
    )

    print()
    print("Training completed.")

    print(
        f"Training time : "
        f"{training_time:.2f} seconds"
    )

    print(
        f"Training time : "
        f"{training_time / 60:.2f} minutes"
    )

    return pipeline, training_time


# ============================================================
# EVALUATE MODEL
# ============================================================

def evaluate_model(
    model,
    X_train,
    y_train,
    X_test,
    y_test
):

    print()
    print("=" * 70)
    print("STEP 5 — MODEL EVALUATION")
    print("=" * 70)

    print()
    print("Generating predictions...")

    prediction_start = time.time()

    train_predictions = model.predict(
        X_train
    )

    test_predictions = model.predict(
        X_test
    )

    prediction_time = (
        time.time()
        - prediction_start
    )

    # ========================================================
    # TRAINING R2
    # ========================================================

    train_r2 = r2_score(
        y_train,
        train_predictions
    )

    # ========================================================
    # TEST METRICS
    # ========================================================

    mae = mean_absolute_error(
        y_test,
        test_predictions
    )

    mse = mean_squared_error(
        y_test,
        test_predictions
    )

    rmse = np.sqrt(mse)

    r2 = r2_score(
        y_test,
        test_predictions
    )

    mape = (
        mean_absolute_percentage_error(
            y_test,
            test_predictions
        )
        * 100
    )

    explained_variance = (
        explained_variance_score(
            y_test,
            test_predictions
        )
    )

    # ========================================================
    # ADJUSTED R2
    # ========================================================

    n = len(y_test)

    # Number of original input features.
    # This uses 24 source-level features:
    # 20 numeric + 4 categorical.

    p = len(ALL_FEATURES)

    if n > p + 1:

        adjusted_r2 = (

            1
            -
            (
                (1 - r2)
                * (n - 1)
            )
            /
            (
                n - p - 1
            )
        )

    else:

        adjusted_r2 = np.nan

    # ========================================================
    # TRAIN-TEST GAP
    # ========================================================

    r2_gap = (
        train_r2
        - r2
    )

    # ========================================================
    # OVERFITTING STATUS
    # ========================================================

    if r2_gap > 0.15:

        model_status = (
            "Possible Overfitting"
        )

    elif r2_gap > 0.08:

        model_status = (
            "Mild Overfitting"
        )

    else:

        model_status = (
            "Good Generalization"
        )

    # ========================================================
    # MODEL QUALITY
    # ========================================================

    if r2 >= 0.90:

        quality = "Excellent"

    elif r2 >= 0.80:

        quality = "Very Good"

    elif r2 >= 0.70:

        quality = "Good"

    elif r2 >= 0.60:

        quality = "Moderate"

    elif r2 >= 0.50:

        quality = "Weak"

    else:

        quality = "Poor"

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print()
    print("=" * 70)
    print("NETWORK PERFORMANCE MODEL")
    print("EVALUATION RESULTS")
    print("=" * 70)

    print()
    print("REGRESSION METRICS")
    print("-" * 70)

    print(
        f"R² Score              : "
        f"{r2:.4f}"
    )

    print(
        f"Adjusted R²           : "
        f"{adjusted_r2:.4f}"
    )

    print(
        f"MAE                   : "
        f"{mae:.4f} Mbps"
    )

    print(
        f"MSE                   : "
        f"{mse:.4f}"
    )

    print(
        f"RMSE                  : "
        f"{rmse:.4f} Mbps"
    )

    print(
        f"MAPE                  : "
        f"{mape:.2f}%"
    )

    print(
        f"Explained Variance    : "
        f"{explained_variance:.4f}"
    )

    print()
    print("MODEL GENERALIZATION")
    print("-" * 70)

    print(
        f"Training R²           : "
        f"{train_r2:.4f}"
    )

    print(
        f"Testing R²            : "
        f"{r2:.4f}"
    )

    print(
        f"Train-Test R² Gap     : "
        f"{r2_gap:.4f}"
    )

    print()
    print("OVERFITTING CHECK")
    print("-" * 70)

    print(
        f"Model Status          : "
        f"{model_status}"
    )

    print()
    print("OVERALL MODEL QUALITY")
    print("-" * 70)

    print(
        f"Overall Model Quality : "
        f"{quality}"
    )

    print()
    print(
        f"Prediction time       : "
        f"{prediction_time:.4f} seconds"
    )

    print("=" * 70)

    # ========================================================
    # RETURN METRICS
    # ========================================================

    metrics = {

        "r2": float(r2),

        "adjusted_r2": float(
            adjusted_r2
        ),

        "mae": float(mae),

        "mse": float(mse),

        "rmse": float(rmse),

        "mape": float(mape),

        "explained_variance":
            float(explained_variance),

        "train_r2":
            float(train_r2),

        "r2_gap":
            float(r2_gap),

        "model_status":
            model_status,

        "model_quality":
            quality,

        "training_samples":
            len(X_train),

        "testing_samples":
            len(X_test),

        "prediction_time_seconds":
            float(prediction_time)
    }

    return metrics


# ============================================================
# SAVE MODEL
# ============================================================

def save_model(model):

    print()
    print("=" * 70)
    print("STEP 6 — SAVING TRAINED MODEL")
    print("=" * 70)

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    joblib.dump(
        model,
        MODEL_PATH
    )

    file_size_mb = (
        os.path.getsize(
            MODEL_PATH
        )
        / (1024 * 1024)
    )

    print()
    print("Model saved successfully.")

    print(
        f"Model file : {MODEL_PATH}"
    )

    print(
        f"File size  : "
        f"{file_size_mb:.2f} MB"
    )

    return MODEL_PATH


# ============================================================
# SAVE MODEL INFORMATION
# ============================================================

def save_model_info(
    metrics,
    training_time,
    dataset_rows,
    cleaned_rows
):

    print()
    print("=" * 70)
    print("STEP 7 — SAVING MODEL INFORMATION")
    print("=" * 70)

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    generated_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    lines = []

    lines.append(
        "============================================================"
    )

    lines.append(
        "TELECOM NETWORK PERFORMANCE PREDICTION MODEL"
    )

    lines.append(
        "MODEL INFORMATION AND EVALUATION REPORT"
    )

    lines.append(
        "============================================================"
    )

    lines.append("")

    lines.append(
        f"Generated on: {generated_at}"
    )

    lines.append("")

    # --------------------------------------------------------
    # PURPOSE
    # --------------------------------------------------------

    lines.append(
        "1. MODEL PURPOSE"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "The model predicts network throughput in Mbps "
        "using telecom network performance, operational, "
        "environmental, and configuration conditions."
    )

    lines.append("")

    lines.append(
        "The prediction can be used by the telecom "
        "network analysis workflow to estimate the "
        "expected network performance under the given "
        "conditions."
    )

    lines.append("")

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    lines.append(
        "2. MODEL ALGORITHM"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "Algorithm: XGBoost Regressor"
    )

    lines.append(
        "Task: Regression"
    )

    lines.append(
        "Target: Throughput (Mbps)"
    )

    lines.append("")

    lines.append(
        "XGBoost configuration:"
    )

    lines.append(
        "    n_estimators     = 300"
    )

    lines.append(
        "    learning_rate    = 0.05"
    )

    lines.append(
        "    max_depth        = 8"
    )

    lines.append(
        "    min_child_weight = 3"
    )

    lines.append(
        "    subsample        = 0.8"
    )

    lines.append(
        "    colsample_bytree = 0.8"
    )

    lines.append(
        "    objective        = reg:squarederror"
    )

    lines.append(
        "    eval_metric      = rmse"
    )

    lines.append(
        "    random_state     = 42"
    )

    lines.append(
        "    tree_method      = hist"
    )

    lines.append("")

    # --------------------------------------------------------
    # DATASET
    # --------------------------------------------------------

    lines.append(
        "3. DATASET"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"Dataset path: {DATA_PATH}"
    )

    lines.append(
        f"Original rows: {dataset_rows:,}"
    )

    lines.append(
        f"Rows used after cleaning: {cleaned_rows:,}"
    )

    lines.append(
        f"Training samples: "
        f"{metrics['training_samples']:,}"
    )

    lines.append(
        f"Testing samples: "
        f"{metrics['testing_samples']:,}"
    )

    lines.append(
        "Train/Test split: 80% / 20%"
    )

    lines.append(
        "Random state: 42"
    )

    lines.append("")

    # --------------------------------------------------------
    # FEATURES
    # --------------------------------------------------------

    lines.append(
        "4. INPUT FEATURES"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"Total source-level features: "
        f"{len(ALL_FEATURES)}"
    )

    lines.append("")

    lines.append(
        "Numeric features:"
    )

    for feature in NUMERIC_FEATURES:

        lines.append(
            f"    - {feature}"
        )

    lines.append("")

    lines.append(
        "Categorical features:"
    )

    for feature in CATEGORICAL_FEATURES:

        lines.append(
            f"    - {feature}"
        )

    lines.append("")

    # --------------------------------------------------------
    # PREPROCESSING
    # --------------------------------------------------------

    lines.append(
        "5. PREPROCESSING"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "Numeric features:"
    )

    lines.append(
        "    Passed through without scaling."
    )

    lines.append("")

    lines.append(
        "Categorical features:"
    )

    lines.append(
        "    OneHotEncoder"
    )

    lines.append(
        "    handle_unknown = ignore"
    )

    lines.append("")

    lines.append(
        "The preprocessing and trained XGBoost model "
        "are stored together inside the Joblib pipeline."
    )

    lines.append("")

    # --------------------------------------------------------
    # EVALUATION
    # --------------------------------------------------------

    lines.append(
        "6. EVALUATION RESULTS"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"R² Score: "
        f"{metrics['r2']:.4f}"
    )

    lines.append(
        f"Adjusted R²: "
        f"{metrics['adjusted_r2']:.4f}"
    )

    lines.append(
        f"MAE: "
        f"{metrics['mae']:.4f} Mbps"
    )

    lines.append(
        f"MSE: "
        f"{metrics['mse']:.4f}"
    )

    lines.append(
        f"RMSE: "
        f"{metrics['rmse']:.4f} Mbps"
    )

    lines.append(
        f"MAPE: "
        f"{metrics['mape']:.2f}%"
    )

    lines.append(
        f"Explained Variance: "
        f"{metrics['explained_variance']:.4f}"
    )

    lines.append("")

    # --------------------------------------------------------
    # GENERALIZATION
    # --------------------------------------------------------

    lines.append(
        "7. GENERALIZATION RESULTS"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"Training R²: "
        f"{metrics['train_r2']:.4f}"
    )

    lines.append(
        f"Testing R²: "
        f"{metrics['r2']:.4f}"
    )

    lines.append(
        f"Train-Test R² Gap: "
        f"{metrics['r2_gap']:.4f}"
    )

    lines.append(
        f"Model Status: "
        f"{metrics['model_status']}"
    )

    lines.append(
        f"Overall Model Quality: "
        f"{metrics['model_quality']}"
    )

    lines.append("")

    # --------------------------------------------------------
    # RUNTIME
    # --------------------------------------------------------

    lines.append(
        "8. TRAINING INFORMATION"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        f"Training time: "
        f"{training_time:.2f} seconds"
    )

    lines.append(
        f"Training time: "
        f"{training_time / 60:.2f} minutes"
    )

    lines.append(
        f"Prediction evaluation time: "
        f"{metrics['prediction_time_seconds']:.4f} seconds"
    )

    lines.append("")

    # --------------------------------------------------------
    # MODEL USAGE
    # --------------------------------------------------------

    lines.append(
        "9. HOW TO LOAD THE MODEL"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "Use the following code:"
    )

    lines.append("")

    lines.append(
        "import joblib"
    )

    lines.append("")

    lines.append(
        "model = joblib.load("
    )

    lines.append(
        "    'models/network_performance_model.joblib'"
    )

    lines.append(
        ")"
    )

    lines.append("")

    # --------------------------------------------------------
    # PREDICTION
    # --------------------------------------------------------

    lines.append(
        "10. HOW TO MAKE A PREDICTION"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "Create a dictionary containing the same input "
        "feature names used during training."
    )

    lines.append("")

    lines.append(
        "input_df = pd.DataFrame([network_data])"
    )

    lines.append(
        "prediction = model.predict(input_df)"
    )

    lines.append(
        "throughput = float(prediction[0])"
    )

    lines.append("")

    lines.append(
        "The output represents predicted network "
        "throughput in Mbps."
    )

    lines.append("")

    # --------------------------------------------------------
    # AGENT INTEGRATION
    # --------------------------------------------------------

    lines.append(
        "11. AGENTIC AI INTEGRATION"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "This model should be used as a predictive ML "
        "component inside the existing network analysis "
        "workflow."
    )

    lines.append("")

    lines.append(
        "It does NOT need to be implemented as a new agent."
    )

    lines.append("")

    lines.append(
        "The existing analysis agent can call this model "
        "when network performance prediction is required."
    )

    lines.append("")

    lines.append(
        "Example information returned to the agent:"
    )

    lines.append(
        "    predicted_throughput_mbps"
    )

    lines.append("")

    lines.append(
        "The prediction can then be passed as additional "
        "evidence to the recommendation stage."
    )

    lines.append("")

    # --------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------

    lines.append(
        "12. IMPORTANT NOTES"
    )

    lines.append(
        "------------------------------------------------------------"
    )

    lines.append(
        "1. The saved Joblib file contains the complete "
        "preprocessing + XGBoost pipeline."
    )

    lines.append(
        "2. New inputs must use the same feature names."
    )

    lines.append(
        "3. Unknown categorical values are supported because "
        "OneHotEncoder uses handle_unknown='ignore'."
    )

    lines.append(
        "4. The model predicts throughput; it does not directly "
        "identify the root cause of an incident."
    )

    lines.append(
        "5. Root-cause analysis should continue to use the "
        "existing retrieval/analysis workflow."
    )

    lines.append(
        "6. The model should be loaded once when the backend "
        "starts rather than loading it for every request."
    )

    lines.append("")

    lines.append(
        "============================================================"
    )

    lines.append(
        "END OF MODEL INFORMATION REPORT"
    )

    lines.append(
        "============================================================"
    )

    report_text = "\n".join(lines)

    with open(
        INFO_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            report_text
        )

    print()
    print(
        f"Model information saved to:"
    )

    print(
        f"{INFO_PATH}"
    )

    return INFO_PATH


# ============================================================
# LOAD MODEL
# ============================================================

def load_saved_model():

    if not os.path.exists(
        MODEL_PATH
    ):

        raise FileNotFoundError(
            f"Saved model not found:\n"
            f"{MODEL_PATH}"
        )

    model = joblib.load(
        MODEL_PATH
    )

    return model


# ============================================================
# PREDICT THROUGHPUT
# ============================================================

def predict_throughput(
    model,
    network_data
):

    input_df = pd.DataFrame(
        [network_data]
    )

    # Validate input columns

    missing_features = [
        feature
        for feature in ALL_FEATURES
        if feature not in input_df.columns
    ]

    if missing_features:

        raise ValueError(
            "Missing prediction features:\n"
            + "\n".join(
                f"- {feature}"
                for feature in missing_features
            )
        )

    input_df = input_df[
        ALL_FEATURES
    ]

    prediction = model.predict(
        input_df
    )

    return float(
        prediction[0]
    )


# ============================================================
# MAIN
# ============================================================

def main():

    overall_start = time.time()

    print()
    print("=" * 70)
    print("TELECOM NETWORK PERFORMANCE PREDICTION")
    print("=" * 70)

    print()
    print(
        "MODE: TRAIN + EVALUATE + SAVE"
    )

    # --------------------------------------------------------
    # 1. Load dataset
    # --------------------------------------------------------

    df = load_data(
        DATA_PATH
    )

    original_rows = len(df)

    # --------------------------------------------------------
    # 2. Prepare dataset
    # --------------------------------------------------------

    X, y = prepare_data(
        df
    )

    cleaned_rows = len(X)

    # --------------------------------------------------------
    # 3. Train/test split
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("STEP 3.5 — TRAIN / TEST SPLIT")
    print("=" * 70)

    X_train, X_test, y_train, y_test = (
        train_test_split(

            X,
            y,

            test_size=TEST_SIZE,

            random_state=RANDOM_STATE
        )
    )

    print()
    print(
        f"Training samples : "
        f"{len(X_train):,}"
    )

    print(
        f"Testing samples  : "
        f"{len(X_test):,}"
    )

    print(
        f"Training ratio   : "
        f"{(1 - TEST_SIZE) * 100:.0f}%"
    )

    print(
        f"Testing ratio    : "
        f"{TEST_SIZE * 100:.0f}%"
    )

    # --------------------------------------------------------
    # 4. Train
    # --------------------------------------------------------

    model, training_time = train_model(
        X_train,
        y_train
    )

    # --------------------------------------------------------
    # 5. Evaluate
    # --------------------------------------------------------

    metrics = evaluate_model(

        model,

        X_train,
        y_train,

        X_test,
        y_test
    )

    # --------------------------------------------------------
    # 6. Save trained model
    # --------------------------------------------------------

    save_model(
        model
    )

    # --------------------------------------------------------
    # 7. Save information TXT
    # --------------------------------------------------------

    save_model_info(

        metrics,

        training_time,

        original_rows,

        cleaned_rows
    )

    # --------------------------------------------------------
    # 8. Example prediction
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("STEP 8 — EXAMPLE THROUGHPUT PREDICTION")
    print("=" * 70)

    example_network = {

        "Cell Availability (%)": 98.0,

        "MTTR (hours)": 3.0,

        "Latency (ms)": 74.3,

        "Packet Loss Rate (%)": 6.4,

        "Call Drop Rate (%)": 1.47,

        "Handover Success Rate (%)": 99.29,

        "Alarm Count": 13,

        "Critical Alarm Count": 6.7,

        "Parameter Changes": 18,

        "Successful Configuration Changes (%)":
            91.85,

        "Data Usage (GB)": 47.49,

        "User Count": 2442,

        "Signal Strength (dBm)": -110.12,

        "Jitter (ms)": 15.67,

        "Connection Setup Success Rate (%)":
            99.0,

        "Security Incidents": 8,

        "Authentication Failures": 2,

        "Temperature (°C)": -6.75,

        "Humidity (%)": 28.79,

        "Fault Occurrence Rate (%)": 33.58,

        "Season": "Winter",

        "Weather": "Clouds",

        "City": "Schneiderville",

        "State": "MN"
    }

    predicted = predict_throughput(
        model,
        example_network
    )

    print()

    print(
        f"Predicted Throughput : "
        f"{predicted:.2f} Mbps"
    )

    # --------------------------------------------------------
    # 9. Total runtime
    # --------------------------------------------------------

    total_time = (
        time.time()
        - overall_start
    )

    print()
    print("=" * 70)

    print(
        f"Total execution time : "
        f"{total_time / 60:.2f} minutes"
    )

    print()

    print(
        "TRAINING + EVALUATION + SAVING COMPLETED"
    )

    print()

    print(
        f"Model file : {MODEL_PATH}"
    )

    print(
        f"Info file  : {INFO_PATH}"
    )

    print("=" * 70)

    return model, metrics


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    model, metrics = main()