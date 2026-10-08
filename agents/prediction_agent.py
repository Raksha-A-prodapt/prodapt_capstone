"""
Network Prediction Agent
========================

Standalone specialist agent for:

1. Network Performance Prediction
   - Predicts Throughput (Mbps)

2. Network Fault Risk Prediction
   - Predicts Fault Occurrence Rate (%)

The agent is intentionally independent from:
- Query Agent
- Synapt Context Layer
- Incident Retrieval
- RCA Agent
- SOP Recommendation Agent
- LLMs

It can therefore be tested independently and later connected
to the multi-agent flow.

INPUT CONTRACT
--------------

process(
    query: optional string,
    network_features: dictionary
)

network_features must contain the fields required by the
relevant model.

OUTPUT CONTRACT
---------------

{
    "agent": "NetworkPredictionAgent",
    "status": "success | partial | not_applicable | error",

    "prediction": {
        "network_performance": {...},
        "fault_risk": {...}
    },

    "display": {
        ...
    },

    "evidence": [...],

    "trace": {...}
}

If no usable network data is provided, the agent returns
"not_applicable" instead of asking the user for values.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json

import joblib
import pandas as pd

from config.prediction_config import (
    THROUGHPUT_MODEL_PATH,
    FAULT_MODEL_PATH,
    THROUGHPUT_TARGET,
    FAULT_TARGET,
    THROUGHPUT_FEATURES,
    FAULT_FEATURES,
    FAULT_RISK_LOW_MAX,
    FAULT_RISK_MEDIUM_MAX,
    FAULT_RISK_HIGH_MAX,
    PERFORMANCE_GAP_LOW_MAX,
    PERFORMANCE_GAP_MEDIUM_MAX,
    PERFORMANCE_GAP_HIGH_MAX,
    ROUND_DIGITS,
)


class NetworkPredictionAgent:
    """
    Standalone telecom network prediction agent.

    The agent does not perform diagnosis. It produces ML-based
    evidence that can later be consumed by an RCA agent.
    """

    def __init__(
        self,
        throughput_model_path: Optional[str | Path] = None,
        fault_model_path: Optional[str | Path] = None,
    ) -> None:

        self.throughput_model_path = Path(
            throughput_model_path or THROUGHPUT_MODEL_PATH
        )

        self.fault_model_path = Path(
            fault_model_path or FAULT_MODEL_PATH
        )

        self.throughput_model = None
        self.fault_model = None

        self._load_models()

    # =====================================================
    # MODEL LOADING
    # =====================================================

    def _load_models(self) -> None:
        """Load the two already-trained ML models."""

        if not self.throughput_model_path.exists():
            raise FileNotFoundError(
                "Throughput model not found: "
                f"{self.throughput_model_path}"
            )

        if not self.fault_model_path.exists():
            raise FileNotFoundError(
                "Fault occurrence model not found: "
                f"{self.fault_model_path}"
            )

        self.throughput_model = joblib.load(
            self.throughput_model_path
        )

        self.fault_model = joblib.load(
            self.fault_model_path
        )

    # =====================================================
    # MAIN ENTRY POINT
    # =====================================================

    def process(
        self,
        network_features: Optional[Dict[str, Any]] = None,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the prediction agent.

        Parameters
        ----------
        network_features:
            Dictionary containing network/environment/configuration
            values.

        query:
            Optional original user query. It is kept for traceability
            but is NOT used as a substitute for model features.

        Returns
        -------
        dict
            Structured prediction result.
        """

        if not network_features:
            return self._not_applicable(
                reason="No network features were provided.",
                query=query,
            )

        throughput_ready = self._has_all_features(
            network_features,
            THROUGHPUT_FEATURES,
        )

        fault_ready = self._has_all_features(
            network_features,
            FAULT_FEATURES,
        )

        if not throughput_ready and not fault_ready:
            return self._not_applicable(
                reason=(
                    "Required features for both prediction models "
                    "are missing."
                ),
                query=query,
                missing_features={
                    "throughput_model": self._missing_features(
                        network_features,
                        THROUGHPUT_FEATURES,
                    ),
                    "fault_model": self._missing_features(
                        network_features,
                        FAULT_FEATURES,
                    ),
                },
            )

        result = {
            "agent": "NetworkPredictionAgent",
            "status": "success",
            "query": query,
            "prediction": {},
            "display": {},
            "evidence": [],
            "trace": {
                "agent": "NetworkPredictionAgent",
                "models_called": [],
                "models_skipped": [],
                "input_feature_count": len(network_features),
            },
        }

        # -------------------------------------------------
        # Throughput prediction
        # -------------------------------------------------

        if throughput_ready:
            try:
                performance = self._predict_throughput(
                    network_features
                )

                result["prediction"]["network_performance"] = (
                    performance
                )

                result["display"]["network_performance"] = (
                    self._performance_display(performance)
                )

                result["evidence"].extend(
                    self._performance_evidence(performance)
                )

                result["trace"]["models_called"].append(
                    "throughput_prediction_model"
                )

            except Exception as exc:
                result["status"] = "partial"
                result["prediction"]["network_performance"] = {
                    "status": "error",
                    "error": str(exc),
                }

                result["trace"]["models_skipped"].append(
                    "throughput_prediction_model"
                )

        else:
            result["trace"]["models_skipped"].append(
                "throughput_prediction_model"
            )

        # -------------------------------------------------
        # Fault occurrence prediction
        # -------------------------------------------------

        if fault_ready:
            try:
                fault = self._predict_fault_occurrence(
                    network_features
                )

                result["prediction"]["fault_risk"] = fault

                result["display"]["fault_risk"] = (
                    self._fault_display(fault)
                )

                result["evidence"].extend(
                    self._fault_evidence(fault)
                )

                result["trace"]["models_called"].append(
                    "fault_occurrence_prediction_model"
                )

            except Exception as exc:
                result["status"] = "partial"
                result["prediction"]["fault_risk"] = {
                    "status": "error",
                    "error": str(exc),
                }

                result["trace"]["models_skipped"].append(
                    "fault_occurrence_prediction_model"
                )

        else:
            result["trace"]["models_skipped"].append(
                "fault_occurrence_prediction_model"
            )

        if not result["trace"]["models_called"]:
            result["status"] = "not_applicable"

        return result

    # =====================================================
    # THROUGHPUT PREDICTION
    # =====================================================

    def _predict_throughput(
        self,
        network_features: Dict[str, Any],
    ) -> Dict[str, Any]:

        df = pd.DataFrame(
            [
                {
                    feature: network_features[feature]
                    for feature in THROUGHPUT_FEATURES
                }
            ]
        )

        prediction = self.throughput_model.predict(df)[0]

        predicted_throughput = float(prediction)

        # If actual throughput was supplied, compare it with
        # expected throughput.
        actual = network_features.get(
            THROUGHPUT_TARGET
        )

        result: Dict[str, Any] = {
            "status": "success",
            "target": THROUGHPUT_TARGET,
            "predicted_throughput_mbps": round(
                predicted_throughput,
                ROUND_DIGITS,
            ),
        }

        if actual is not None:
            actual = float(actual)

            result["actual_throughput_mbps"] = round(
                actual,
                ROUND_DIGITS,
            )

            if predicted_throughput != 0:
                deviation = (
                    (
                        actual
                        - predicted_throughput
                    )
                    / predicted_throughput
                ) * 100

                gap = abs(deviation)

                result[
                    "performance_deviation_percent"
                ] = round(
                    deviation,
                    ROUND_DIGITS,
                )

                result[
                    "performance_gap_percent"
                ] = round(
                    gap,
                    ROUND_DIGITS,
                )

                result["performance_status"] = (
                    self._performance_status(gap)
                )

        return result

    # =====================================================
    # FAULT OCCURRENCE PREDICTION
    # =====================================================

    def _predict_fault_occurrence(
        self,
        network_features: Dict[str, Any],
    ) -> Dict[str, Any]:

        df = pd.DataFrame(
            [
                {
                    feature: network_features[feature]
                    for feature in FAULT_FEATURES
                }
            ]
        )

        # Your stated model is a Fault Occurrence Rate model.
        # Normally this is a regression model whose prediction
        # is directly the occurrence rate percentage.
        prediction = self.fault_model.predict(df)[0]

        fault_rate = float(prediction)

        # Keep an occurrence rate in a sensible percentage range.
        fault_rate = max(
            0.0,
            min(100.0, fault_rate),
        )

        risk = self._fault_risk(fault_rate)

        return {
            "status": "success",
            "target": FAULT_TARGET,
            "predicted_fault_occurrence_rate_percent": round(
                fault_rate,
                ROUND_DIGITS,
            ),
            "fault_risk": risk,
        }

    # =====================================================
    # DISPLAY OUTPUT
    # =====================================================

    @staticmethod
    def _performance_display(
        performance: Dict[str, Any],
    ) -> Dict[str, Any]:

        display = {
            "label": "Predicted Throughput",
            "value": performance.get(
                "predicted_throughput_mbps"
            ),
            "unit": "Mbps",
        }

        if "actual_throughput_mbps" in performance:
            display["actual"] = {
                "label": "Actual Throughput",
                "value": performance[
                    "actual_throughput_mbps"
                ],
                "unit": "Mbps",
            }

        if "performance_gap_percent" in performance:
            display["deviation"] = {
                "label": "Performance Gap",
                "value": performance[
                    "performance_gap_percent"
                ],
                "unit": "%",
                "risk": performance[
                    "performance_status"
                ],
            }

        return display

    @staticmethod
    def _fault_display(
        fault: Dict[str, Any],
    ) -> Dict[str, Any]:

        return {
            "label": "Fault Occurrence Rate",
            "value": fault[
                "predicted_fault_occurrence_rate_percent"
            ],
            "unit": "%",
            "risk": fault["fault_risk"],
        }

    # =====================================================
    # RISK CLASSIFICATION
    # =====================================================

    @staticmethod
    def _fault_risk(rate: float) -> str:

        if rate <= FAULT_RISK_LOW_MAX:
            return "LOW"

        if rate <= FAULT_RISK_MEDIUM_MAX:
            return "MEDIUM"

        if rate <= FAULT_RISK_HIGH_MAX:
            return "HIGH"

        return "CRITICAL"

    @staticmethod
    def _performance_status(gap: float) -> str:

        if gap <= PERFORMANCE_GAP_LOW_MAX:
            return "LOW"

        if gap <= PERFORMANCE_GAP_MEDIUM_MAX:
            return "MEDIUM"

        if gap <= PERFORMANCE_GAP_HIGH_MAX:
            return "HIGH"

        return "CRITICAL"

    # =====================================================
    # EVIDENCE FOR RCA
    # =====================================================

    @staticmethod
    def _performance_evidence(
        performance: Dict[str, Any],
    ) -> list:

        evidence = [
            {
                "source": "throughput_prediction_model",
                "type": "ml_prediction",
                "metric": "Throughput",
                "value": performance.get(
                    "predicted_throughput_mbps"
                ),
                "unit": "Mbps",
            }
        ]

        if "actual_throughput_mbps" in performance:
            evidence.append(
                {
                    "source": "throughput_prediction_model",
                    "type": "performance_comparison",
                    "actual": performance[
                        "actual_throughput_mbps"
                    ],
                    "predicted": performance[
                        "predicted_throughput_mbps"
                    ],
                    "gap_percent": performance.get(
                        "performance_gap_percent"
                    ),
                    "status": performance.get(
                        "performance_status"
                    ),
                }
            )

        return evidence

    @staticmethod
    def _fault_evidence(
        fault: Dict[str, Any],
    ) -> list:

        return [
            {
                "source": "fault_occurrence_prediction_model",
                "type": "ml_prediction",
                "metric": "Fault Occurrence Rate",
                "value": fault[
                    "predicted_fault_occurrence_rate_percent"
                ],
                "unit": "%",
                "risk": fault["fault_risk"],
            }
        ]

    # =====================================================
    # VALIDATION HELPERS
    # =====================================================

    @staticmethod
    def _has_all_features(
        data: Dict[str, Any],
        features: list,
    ) -> bool:

        return all(
            feature in data
            and data[feature] is not None
            for feature in features
        )

    @staticmethod
    def _missing_features(
        data: Dict[str, Any],
        features: list,
    ) -> list:

        return [
            feature
            for feature in features
            if feature not in data
            or data[feature] is None
        ]

    # =====================================================
    # NOT APPLICABLE
    # =====================================================

    @staticmethod
    def _not_applicable(
        reason: str,
        query: Optional[str] = None,
        missing_features: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        return {
            "agent": "NetworkPredictionAgent",
            "status": "not_applicable",
            "query": query,

            "prediction": {
                "network_performance": {
                    "status": "not_run"
                },
                "fault_risk": {
                    "status": "not_run"
                },
            },

            "display": {},

            "evidence": [],

            "reason": reason,

            "missing_features": (
                missing_features or {}
            ),

            "trace": {
                "agent": "NetworkPredictionAgent",
                "models_called": [],
                "models_skipped": [
                    "throughput_prediction_model",
                    "fault_occurrence_prediction_model",
                ],
                "skipped": True,
            },
        }


# =========================================================
# STANDALONE TEST
# =========================================================

if __name__ == "__main__":

    agent = NetworkPredictionAgent()

    # Example input matching your two model schemas.
    sample_features = {
        "Cell Availability (%)": 98.0,
        "MTTR (hours)": 4.2,
        "Throughput (Mbps)": 300.0,
        "Latency (ms)": 75.0,
        "Packet Loss Rate (%)": 4.5,
        "Call Drop Rate (%)": 1.5,
        "Handover Success Rate (%)": 96.0,
        "Alarm Count": 12,
        "Critical Alarm Count": 2,
        "Parameter Changes": 3,
        "Successful Configuration Changes (%)": 98.0,
        "Data Usage (GB)": 500.0,
        "User Count": 1500,
        "Signal Strength (dBm)": -85.0,
        "Jitter (ms)": 10.0,
        "Connection Setup Success Rate (%)": 97.0,
        "Security Incidents": 1,
        "Authentication Failures": 5,
        "Temperature (°C)": 28.0,
        "Humidity (%)": 65.0,
        "Fault Occurrence Rate (%)": 12.0,

        "Season": "Summer",
        "Weather": "Clear",
        "City": "Chennai",
        "State": "Tamil Nadu",
    }

    result = agent.process(
        query=(
            "Predict network performance and "
            "fault occurrence risk."
        ),
        network_features=sample_features,
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )
