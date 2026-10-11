"""Canonical metric names and tolerant conversion for all data layers.

The CSV uses human-readable headers, while retrieval, RCA, and live-model
inputs use snake_case.  This module is the single boundary between those two
representations and also tolerates common UTF-8/Windows mojibake variants.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_JSONL = PROJECT_ROOT / "files_load_context_files" / "schema.jsonl"

# Fallback registry. The JSONL file extends this with descriptions/aliases
# when available, but runtime correctness does not depend on the file order.
DEFAULT_FIELDS = {
    "incident_id": "Incident_ID",
    "season": "Season",
    "cell_availability": "Cell Availability (%)",
    "mttr_hours": "MTTR (hours)",
    "throughput_mbps": "Throughput (Mbps)",
    "latency_ms": "Latency (ms)",
    "packet_loss_rate": "Packet Loss Rate (%)",
    "call_drop_rate": "Call Drop Rate (%)",
    "handover_success_rate": "Handover Success Rate (%)",
    "alarm_count": "Alarm Count",
    "critical_alarm_count": "Critical Alarm Count",
    "parameter_changes": "Parameter Changes",
    "successful_configuration_changes": "Successful Configuration Changes (%)",
    "data_usage_gb": "Data Usage (GB)",
    "user_count": "User Count",
    "signal_strength_dbm": "Signal Strength (dBm)",
    "jitter_ms": "Jitter (ms)",
    "connection_setup_success_rate": "Connection Setup Success Rate (%)",
    "security_incidents": "Security Incidents",
    "authentication_failures": "Authentication Failures",
    "temperature_c": "Temperature (°C)",
    "humidity_percent": "Humidity (%)",
    "weather": "Weather",
    "issue_reported": "Issue Reported",
    "city": "City",
    "state": "State",
    "zip": "Zip",
    "fault_occurrence_rate": "Fault Occurrence Rate (%)",
}

COMMON_ALIASES = {
    "availability": "cell_availability",
    "cell availability": "cell_availability",
    "mttr": "mttr_hours",
    "throughput": "throughput_mbps",
    "latency": "latency_ms",
    "delay": "latency_ms",
    "packet loss": "packet_loss_rate",
    "packet loss rate": "packet_loss_rate",
    "call drops": "call_drop_rate",
    "call drop": "call_drop_rate",
    "handover": "handover_success_rate",
    "handover success": "handover_success_rate",
    "alarms": "alarm_count",
    "alarm count": "alarm_count",
    "critical alarms": "critical_alarm_count",
    "parameter changes": "parameter_changes",
    "configuration success": "successful_configuration_changes",
    "successful configuration": "successful_configuration_changes",
    "data usage": "data_usage_gb",
    "users": "user_count",
    "user count": "user_count",
    "signal": "signal_strength_dbm",
    "signal strength": "signal_strength_dbm",
    "jitter": "jitter_ms",
    "connection setup": "connection_setup_success_rate",
    "security incidents": "security_incidents",
    "authentication failures": "authentication_failures",
    "temperature": "temperature_c",
    "temperature c": "temperature_c",
    "humidity": "humidity_percent",
    "fault occurrence": "fault_occurrence_rate",
    "faults": "fault_occurrence_rate",
}


def _clean_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).strip().casefold()
    # Repair common UTF-8 decoded as Windows-1252/Latin-1 spellings.
    text = text.replace("â‚¬", "€").replace("â°", "°")
    text = text.replace("â", "-").replace("â", "-")
    text = text.replace("ï¿½", "°").replace("�", "°")
    return text


def normalized_key(value: Any) -> str:
    """Normalize headers/aliases for matching, including unit punctuation."""
    text = _clean_text(value).replace("Â", "").replace("Ã", "")
    text = text.replace("°", " ")
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _schema_aliases() -> dict[str, str]:
    aliases = {normalized_key(field): field for field in DEFAULT_FIELDS}
    aliases.update({normalized_key(source): field for field, source in DEFAULT_FIELDS.items()})
    aliases.update({normalized_key(alias): field for alias, field in COMMON_ALIASES.items()})
    if SCHEMA_JSONL.is_file():
        try:
            with SCHEMA_JSONL.open("r", encoding="utf-8-sig") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    field = str(item["canonical"])
                    aliases[normalized_key(field)] = field
                    aliases[normalized_key(item.get("source", field))] = field
                    for alias in item.get("aliases", []):
                        aliases[normalized_key(alias)] = field
        except (OSError, TypeError, ValueError, KeyError):
            pass
    return aliases


ALIASES = _schema_aliases()


def canonical_field(name: Any) -> str:
    """Return the canonical snake_case field for any supported spelling."""
    key = normalized_key(name)
    return ALIASES.get(key, key)


def canonicalize_mapping(values: Mapping[str, Any] | None) -> dict[str, Any]:
    """Canonicalize a telemetry/record mapping without discarding unknowns."""
    if not values:
        return {}
    result: dict[str, Any] = {}
    for raw_name, value in values.items():
        field = canonical_field(raw_name)
        # Prefer an already-canonical value over a duplicate source alias.
        if field not in result or normalized_key(raw_name) == field:
            result[field] = value
    return result


def canonicalize_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy whose recognized columns use canonical field names."""
    result = frame.copy()
    renamed: dict[str, str] = {}
    for column in result.columns:
        field = canonical_field(column)
        if field in DEFAULT_FIELDS:
            renamed[column] = field
    result = result.rename(columns=renamed)
    return result


def source_field(name: Any) -> str:
    """Return the stable human-readable CSV/model header for a field."""
    return DEFAULT_FIELDS.get(canonical_field(name), str(name))

