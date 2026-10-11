"""Shared, dataset-relative metric threshold configuration."""

# Query filtering uses per-column quantiles calculated from the loaded dataset.
# These are descriptive bands, not telecom standards or risk thresholds.
QUERY_METRIC_BANDS = {
    "low_upper_percentile": 1 / 3,
    "high_lower_percentile": 2 / 3,
}

# Dataset-relative risk cutoffs used by IncidentClassificationAgent.
# Kept identical to its previous values to preserve existing classifications.
CLASSIFICATION_RISK_THRESHOLDS = (
    ("latency_ms", ">", "high_latency", 129.9218),
    ("packet_loss_rate", ">", "high_packet_loss", 11.88),
    ("call_drop_rate", ">", "high_call_drop_rate", 3.1338),
    ("handover_success_rate", "<", "low_handover_success", 91.01),
    ("cell_availability", "<", "low_cell_availability", 79.4339),
    ("throughput_mbps", "<", "low_throughput", 304.2482),
    ("signal_strength_dbm", "<", "weak_signal", -114.04),
    ("jitter_ms", ">", "high_jitter", 44.98),
    ("alarm_count", ">=", "high_alarm_count", 14.0),
)
