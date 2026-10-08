"""
Prediction Agent configuration.

IMPORTANT:
The trained model files should be complete sklearn pipelines
(or compatible objects) that already contain their preprocessing,
encoding, and estimator.

Update MODEL_PATH values to your actual saved model locations.
"""

from pathlib import Path


# ---------------------------------------------------------
# PROJECT / MODEL PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / "ml_model" / "models"

THROUGHPUT_MODEL_PATH = MODELS_DIR / "network_performance_model.joblib"
FAULT_MODEL_PATH = MODELS_DIR / "fault_tolerance_model.joblib"


# ---------------------------------------------------------
# MODEL TARGETS
# ---------------------------------------------------------

THROUGHPUT_TARGET = "Throughput (Mbps)"
FAULT_TARGET = "Fault Occurrence Rate (%)"


# ---------------------------------------------------------
# THROUGHPUT MODEL FEATURES
# ---------------------------------------------------------

THROUGHPUT_NUMERIC_FEATURES = [
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
    "Fault Occurrence Rate (%)",
]

THROUGHPUT_CATEGORICAL_FEATURES = [
    "Season",
    "Weather",
    "City",
    "State",
]

THROUGHPUT_FEATURES = (
    THROUGHPUT_NUMERIC_FEATURES
    + THROUGHPUT_CATEGORICAL_FEATURES
)


# ---------------------------------------------------------
# FAULT OCCURRENCE MODEL FEATURES
# ---------------------------------------------------------

FAULT_NUMERIC_FEATURES = [
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
    "Humidity (%)",
]

FAULT_CATEGORICAL_FEATURES = [
    "Season",
    "Weather",
]

FAULT_FEATURES = (
    FAULT_NUMERIC_FEATURES
    + FAULT_CATEGORICAL_FEATURES
)


# ---------------------------------------------------------
# RISK THRESHOLDS
# ---------------------------------------------------------

# Fault Occurrence Rate (%) -> risk
FAULT_RISK_LOW_MAX = 30.0
FAULT_RISK_MEDIUM_MAX = 60.0
FAULT_RISK_HIGH_MAX = 80.0

# Actual throughput vs predicted throughput.
# Absolute percentage gap.
PERFORMANCE_GAP_LOW_MAX = 15.0
PERFORMANCE_GAP_MEDIUM_MAX = 30.0
PERFORMANCE_GAP_HIGH_MAX = 50.0


# ---------------------------------------------------------
# OUTPUT SETTINGS
# ---------------------------------------------------------

ROUND_DIGITS = 2
