# import csv
# import json
# from pathlib import Path


# # ============================================================
# # CONFIGURATION
# # ============================================================

# INPUT_CSV = "D:/raksha/capstone/try2/data/telecom_network_incidents_with_id.csv"
# OUTPUT_JSONL = "incident_documents.jsonl"


# # ============================================================
# # EXPECTED DATASET COLUMNS
# # ============================================================

# REQUIRED_COLUMNS = [
#     "Incident_ID",
#     "Season",
#     "Cell Availability (%)",
#     "MTTR (hours)",
#     "Throughput (Mbps)",
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
#     "Weather",
#     "Issue Reported",
#     "City",
#     "State",
#     "Zip",
#     "Fault Occurrence Rate (%)",
# ]


# # ============================================================
# # HELPER FUNCTIONS
# # ============================================================

# def clean_string(value):
#     """Clean string values."""
#     if value is None:
#         return ""

#     return str(value).strip()


# def to_float(value):
#     """Convert value to float safely."""
#     try:
#         return float(value)
#     except (ValueError, TypeError):
#         return None


# def to_int(value):
#     """Convert value to integer safely."""
#     try:
#         return int(float(value))
#     except (ValueError, TypeError):
#         return None


# # ============================================================
# # CREATE SEMANTIC TEXT
# # ============================================================

# def create_semantic_text(row):
#     """
#     Create natural-language representation of one incident.

#     This text will later be embedded for semantic search.

#     IMPORTANT:
#     The numerical values are included for context,
#     but numerical filtering/similarity should be handled
#     separately using metadata.
#     """

#     return (
#         f"Telecom network incident {clean_string(row['Incident_ID'])} "
#         f"in {clean_string(row['City'])}, {clean_string(row['State'])} "
#         f"during {clean_string(row['Season'])} under "
#         f"{clean_string(row['Weather'])} weather. "

#         f"Network performance showed "
#         f"{clean_string(row['Cell Availability (%)'])}% cell availability, "
#         f"{clean_string(row['Throughput (Mbps)'])} Mbps throughput, "
#         f"{clean_string(row['Latency (ms)'])} ms latency, "
#         f"{clean_string(row['Packet Loss Rate (%)'])}% packet loss, "
#         f"{clean_string(row['Call Drop Rate (%)'])}% call drop rate, "
#         f"{clean_string(row['Handover Success Rate (%)'])}% "
#         f"handover success rate, "
#         f"{clean_string(row['Signal Strength (dBm)'])} dBm signal strength, "
#         f"and {clean_string(row['Jitter (ms)'])} ms jitter. "

#         f"The connection setup success rate was "
#         f"{clean_string(row['Connection Setup Success Rate (%)'])}%. "

#         f"Operational conditions included "
#         f"{clean_string(row['Alarm Count'])} alarms, "
#         f"{clean_string(row['Critical Alarm Count'])} critical alarms, "
#         f"{clean_string(row['Parameter Changes'])} parameter changes, "
#         f"and {clean_string(row['Successful Configuration Changes (%)'])}% "
#         f"successful configuration changes. "

#         f"MTTR was {clean_string(row['MTTR (hours)'])} hours. "

#         f"The network had "
#         f"{clean_string(row['User Count'])} users and "
#         f"{clean_string(row['Data Usage (GB)'])} GB data usage. "

#         f"There were "
#         f"{clean_string(row['Security Incidents'])} security incidents "
#         f"and "
#         f"{clean_string(row['Authentication Failures'])} "
#         f"authentication failures. "

#         f"Environmental conditions included "
#         f"{clean_string(row['Temperature (°C)'])} degrees Celsius "
#         f"temperature and "
#         f"{clean_string(row['Humidity (%)'])}% humidity. "
#     )


# # ============================================================
# # CREATE METADATA
# # ============================================================

# def create_metadata(row):
#     """
#     Store structured information separately.

#     This metadata will be used for:
#     - filtering
#     - numeric conditions
#     - analytics
#     - ML models
#     - exact incident lookup
#     """

#     return {
#         # Identification
#         "incident_id": clean_string(row["Incident_ID"]),

#         # Location / context
#         "city": clean_string(row["City"]),
#         "state": clean_string(row["State"]),
#         "zip": clean_string(row["Zip"]),
#         "season": clean_string(row["Season"]),
#         "weather": clean_string(row["Weather"]),

#         # Keep Issue Reported as metadata.
#         # Do NOT treat "yes/no" as semantic issue description.
#         "issue_reported": clean_string(row["Issue Reported"]),

#         # Network performance
#         "cell_availability": to_float(
#             row["Cell Availability (%)"]
#         ),

#         "throughput_mbps": to_float(
#             row["Throughput (Mbps)"]
#         ),

#         "latency_ms": to_float(
#             row["Latency (ms)"]
#         ),

#         "packet_loss_rate": to_float(
#             row["Packet Loss Rate (%)"]
#         ),

#         "call_drop_rate": to_float(
#             row["Call Drop Rate (%)"]
#         ),

#         "handover_success_rate": to_float(
#             row["Handover Success Rate (%)"]
#         ),

#         "signal_strength_dbm": to_float(
#             row["Signal Strength (dBm)"]
#         ),

#         "jitter_ms": to_float(
#             row["Jitter (ms)"]
#         ),

#         "connection_setup_success_rate": to_float(
#             row["Connection Setup Success Rate (%)"]
#         ),

#         # Operations
#         "mttr_hours": to_float(
#             row["MTTR (hours)"]
#         ),

#         "alarm_count": to_float(
#             row["Alarm Count"]
#         ),

#         "critical_alarm_count": to_float(
#             row["Critical Alarm Count"]
#         ),

#         "parameter_changes": to_float(
#             row["Parameter Changes"]
#         ),

#         "successful_configuration_changes": to_float(
#             row["Successful Configuration Changes (%)"]
#         ),

#         # Usage
#         "data_usage_gb": to_float(
#             row["Data Usage (GB)"]
#         ),

#         "user_count": to_int(
#             row["User Count"]
#         ),

#         # Security
#         "security_incidents": to_float(
#             row["Security Incidents"]
#         ),

#         "authentication_failures": to_float(
#             row["Authentication Failures"]
#         ),

#         # Environment
#         "temperature_c": to_float(
#             row["Temperature (°C)"]
#         ),

#         "humidity_percent": to_float(
#             row["Humidity (%)"]
#         ),

#         # Fault / risk
#         "fault_occurrence_rate": to_float(
#             row["Fault Occurrence Rate (%)"]
#         ),
#     }


# # ============================================================
# # VALIDATE CSV
# # ============================================================

# def validate_columns(fieldnames):
#     """Check that the CSV contains the expected columns."""

#     missing_columns = [
#         column
#         for column in REQUIRED_COLUMNS
#         if column not in fieldnames
#     ]

#     if missing_columns:
#         raise ValueError(
#             "Missing columns in CSV:\n"
#             + "\n".join(missing_columns)
#         )


# # ============================================================
# # CONVERT CSV → JSONL
# # ============================================================

# def convert_csv_to_jsonl(input_csv, output_jsonl):

#     input_path = Path(input_csv)
#     output_path = Path(output_jsonl)

#     if not input_path.exists():
#         raise FileNotFoundError(
#             f"CSV file not found: {input_path}"
#         )

#     processed = 0
#     skipped = 0

#     with open(
#         input_path,
#         "r",
#         encoding="utf-8-sig",
#         newline=""
#     ) as csv_file:

#         reader = csv.DictReader(csv_file)

#         # Validate columns
#         validate_columns(reader.fieldnames)

#         with open(
#             output_path,
#             "w",
#             encoding="utf-8"
#         ) as jsonl_file:

#             for row in reader:

#                 incident_id = clean_string(
#                     row["Incident_ID"]
#                 )

#                 # Skip rows without Incident ID
#                 if not incident_id:
#                     skipped += 1
#                     continue

#                 document = {
#                     "id": incident_id,

#                     # Semantic representation
#                     "text": create_semantic_text(row),

#                     # Structured information
#                     "metadata": create_metadata(row)
#                 }

#                 # Write one JSON object per line
#                 jsonl_file.write(
#                     json.dumps(
#                         document,
#                         ensure_ascii=False
#                     )
#                     + "\n"
#                 )

#                 processed += 1

#     print("=" * 60)
#     print("CSV → JSONL conversion completed")
#     print("=" * 60)

#     print(f"Input file       : {input_path}")
#     print(f"Output file      : {output_path}")
#     print(f"Records created  : {processed}")
#     print(f"Records skipped  : {skipped}")
#     print("=" * 60)


# # ============================================================
# # MAIN
# # ============================================================

# if __name__ == "__main__":

#     convert_csv_to_jsonl(
#         INPUT_CSV,
#         OUTPUT_JSONL
#     )

######################3333
            #################################
#############################33
              ######################################
import csv
import json
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_CSV = "D:/raksha/capstone/try2/data/telecom_network_incidents_with_id.csv"
OUTPUT_JSONL = "incident_documents.jsonl"


# ============================================================
# EXPECTED DATASET COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "Incident_ID",
    "Season",
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
    "Weather",
    "Issue Reported",
    "City",
    "State",
    "Zip",
    "Fault Occurrence Rate (%)",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_string(value):
    """Clean string values safely."""

    if value is None:
        return ""

    return str(value).strip()


def to_float(value):
    """Convert value to float safely."""

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def to_int(value):
    """Convert value to integer safely."""

    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


# ============================================================
# ISSUE REPORTED → NATURAL LANGUAGE
# ============================================================

def create_issue_statement(row):
    """
    Convert Issue Reported into natural language.

    This is included in the semantic text so that
    embedding-based search can understand queries such as:

    - incidents where an issue was reported
    - incidents with no reported issue
    - reported network problems
    """

    issue_reported = clean_string(
        row["Issue Reported"]
    ).lower()

    if issue_reported == "yes":
        return (
            "A network issue was reported for this incident."
        )

    elif issue_reported == "no":
        return (
            "No network issue was reported for this incident."
        )

    else:
        return (
            f"The issue reported status was "
            f"{clean_string(row['Issue Reported'])}."
        )


# ============================================================
# CREATE SEMANTIC TEXT
# ============================================================

def create_semantic_text(row):
    """
    Create a natural-language representation of one incident.

    This text will later be converted into an embedding
    for semantic search.

    All important telecom/network fields are represented
    in natural language.

    Structured metadata is also stored separately.
    """

    issue_statement = create_issue_statement(row)

    return (
        # ----------------------------------------------------
        # INCIDENT + LOCATION + TIME + WEATHER
        # ----------------------------------------------------

        f"Telecom network incident "
        f"{clean_string(row['Incident_ID'])} "

        f"occurred in "
        f"{clean_string(row['City'])}, "
        f"{clean_string(row['State'])}, "
        f"ZIP code {clean_string(row['Zip'])} "

        f"during the {clean_string(row['Season'])} season "
        f"under {clean_string(row['Weather'])} weather. "

        f"{issue_statement} "

        # ----------------------------------------------------
        # NETWORK PERFORMANCE
        # ----------------------------------------------------

        f"Network performance showed "
        f"{clean_string(row['Cell Availability (%)'])}% "
        f"cell availability, "

        f"{clean_string(row['Throughput (Mbps)'])} Mbps "
        f"throughput, "

        f"{clean_string(row['Latency (ms)'])} ms latency, "

        f"{clean_string(row['Packet Loss Rate (%)'])}% "
        f"packet loss rate, "

        f"{clean_string(row['Call Drop Rate (%)'])}% "
        f"call drop rate, "

        f"{clean_string(row['Handover Success Rate (%)'])}% "
        f"handover success rate, "

        f"{clean_string(row['Signal Strength (dBm)'])} dBm "
        f"signal strength, "

        f"and {clean_string(row['Jitter (ms)'])} ms jitter. "

        # ----------------------------------------------------
        # CONNECTION
        # ----------------------------------------------------

        f"The connection setup success rate was "
        f"{clean_string(row['Connection Setup Success Rate (%)'])}%. "

        # ----------------------------------------------------
        # OPERATIONAL CONDITIONS
        # ----------------------------------------------------

        f"Operational conditions included "

        f"{clean_string(row['Alarm Count'])} alarms, "

        f"{clean_string(row['Critical Alarm Count'])} critical alarms, "

        f"{clean_string(row['Parameter Changes'])} parameter changes, "

        f"and "
        f"{clean_string(row['Successful Configuration Changes (%)'])}% "
        f"successful configuration changes. "

        # ----------------------------------------------------
        # MTTR
        # ----------------------------------------------------

        f"The mean time to repair (MTTR) was "
        f"{clean_string(row['MTTR (hours)'])} hours. "

        # ----------------------------------------------------
        # USAGE
        # ----------------------------------------------------

        f"The network had "
        f"{clean_string(row['User Count'])} users "

        f"and "
        f"{clean_string(row['Data Usage (GB)'])} GB "
        f"of data usage. "

        # ----------------------------------------------------
        # SECURITY
        # ----------------------------------------------------

        f"There were "
        f"{clean_string(row['Security Incidents'])} security incidents "

        f"and "
        f"{clean_string(row['Authentication Failures'])} "
        f"authentication failures. "

        # ----------------------------------------------------
        # ENVIRONMENT
        # ----------------------------------------------------

        f"Environmental conditions included "

        f"{clean_string(row['Temperature (°C)'])} degrees Celsius "
        f"temperature "

        f"and "
        f"{clean_string(row['Humidity (%)'])}% humidity. "

        # ----------------------------------------------------
        # FAULT
        # ----------------------------------------------------

        f"The fault occurrence rate was "
        f"{clean_string(row['Fault Occurrence Rate (%)'])}%."
    )


# ============================================================
# CREATE METADATA
# ============================================================

def create_metadata(row):
    """
    Store all structured information separately.

    Metadata is useful for:

    - ChromaDB filtering
    - numeric conditions
    - analytics
    - ML models
    - exact incident lookup
    - displaying incident details
    """

    return {

        # ----------------------------------------------------
        # IDENTIFICATION
        # ----------------------------------------------------

        "incident_id": clean_string(
            row["Incident_ID"]
        ),

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        "city": clean_string(
            row["City"]
        ),

        "state": clean_string(
            row["State"]
        ),

        "zip": clean_string(
            row["Zip"]
        ),

        # ----------------------------------------------------
        # CONTEXT
        # ----------------------------------------------------

        "season": clean_string(
            row["Season"]
        ),

        "weather": clean_string(
            row["Weather"]
        ),

        "issue_reported": clean_string(
            row["Issue Reported"]
        ),

        # ----------------------------------------------------
        # NETWORK PERFORMANCE
        # ----------------------------------------------------

        "cell_availability": to_float(
            row["Cell Availability (%)"]
        ),

        "throughput_mbps": to_float(
            row["Throughput (Mbps)"]
        ),

        "latency_ms": to_float(
            row["Latency (ms)"]
        ),

        "packet_loss_rate": to_float(
            row["Packet Loss Rate (%)"]
        ),

        "call_drop_rate": to_float(
            row["Call Drop Rate (%)"]
        ),

        "handover_success_rate": to_float(
            row["Handover Success Rate (%)"]
        ),

        "signal_strength_dbm": to_float(
            row["Signal Strength (dBm)"]
        ),

        "jitter_ms": to_float(
            row["Jitter (ms)"]
        ),

        "connection_setup_success_rate": to_float(
            row["Connection Setup Success Rate (%)"]
        ),

        # ----------------------------------------------------
        # OPERATIONS
        # ----------------------------------------------------

        "mttr_hours": to_float(
            row["MTTR (hours)"]
        ),

        "alarm_count": to_float(
            row["Alarm Count"]
        ),

        "critical_alarm_count": to_float(
            row["Critical Alarm Count"]
        ),

        "parameter_changes": to_float(
            row["Parameter Changes"]
        ),

        "successful_configuration_changes": to_float(
            row["Successful Configuration Changes (%)"]
        ),

        # ----------------------------------------------------
        # USAGE
        # ----------------------------------------------------

        "data_usage_gb": to_float(
            row["Data Usage (GB)"]
        ),

        "user_count": to_int(
            row["User Count"]
        ),

        # ----------------------------------------------------
        # SECURITY
        # ----------------------------------------------------

        "security_incidents": to_float(
            row["Security Incidents"]
        ),

        "authentication_failures": to_float(
            row["Authentication Failures"]
        ),

        # ----------------------------------------------------
        # ENVIRONMENT
        # ----------------------------------------------------

        "temperature_c": to_float(
            row["Temperature (°C)"]
        ),

        "humidity_percent": to_float(
            row["Humidity (%)"]
        ),

        # ----------------------------------------------------
        # FAULT / RISK
        # ----------------------------------------------------

        "fault_occurrence_rate": to_float(
            row["Fault Occurrence Rate (%)"]
        ),
    }


# ============================================================
# VALIDATE CSV
# ============================================================

def validate_columns(fieldnames):
    """
    Check that the CSV contains every expected column.
    """

    if fieldnames is None:
        raise ValueError(
            "CSV does not contain a header row."
        )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in fieldnames
    ]

    if missing_columns:

        raise ValueError(
            "Missing columns in CSV:\n"
            + "\n".join(missing_columns)
        )

    print("All required columns found.")


# ============================================================
# CONVERT CSV → JSONL
# ============================================================

def convert_csv_to_jsonl(
    input_csv,
    output_jsonl
):

    input_path = Path(input_csv)
    output_path = Path(output_jsonl)

    # --------------------------------------------------------
    # CHECK INPUT
    # --------------------------------------------------------

    if not input_path.exists():

        raise FileNotFoundError(
            f"CSV file not found: {input_path}"
        )

    processed = 0
    skipped = 0

    # --------------------------------------------------------
    # READ CSV
    # --------------------------------------------------------

    with open(
        input_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        # ----------------------------------------------------
        # VALIDATE COLUMNS
        # ----------------------------------------------------

        validate_columns(
            reader.fieldnames
        )

        # ----------------------------------------------------
        # WRITE JSONL
        #
        # "w" automatically replaces the previous JSONL file.
        # ----------------------------------------------------

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as jsonl_file:

            for row in reader:

                # ------------------------------------------------
                # INCIDENT ID
                # ------------------------------------------------

                incident_id = clean_string(
                    row["Incident_ID"]
                )

                # ------------------------------------------------
                # SKIP INVALID ROWS
                # ------------------------------------------------

                if not incident_id:

                    skipped += 1

                    continue

                # ------------------------------------------------
                # CREATE DOCUMENT
                # ------------------------------------------------

                document = {

                    # Unique ChromaDB ID
                    "id": incident_id,

                    # Natural-language representation
                    # used for embedding
                    "text": create_semantic_text(row),

                    # Structured fields
                    # used as metadata
                    "metadata": create_metadata(row)
                }

                # ------------------------------------------------
                # WRITE ONE JSON OBJECT PER LINE
                # ------------------------------------------------

                jsonl_file.write(
                    json.dumps(
                        document,
                        ensure_ascii=False
                    )
                    + "\n"
                )

                processed += 1

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 60)
    print("CSV → JSONL CONVERSION COMPLETED")
    print("=" * 60)

    print(
        f"Input file       : {input_path}"
    )

    print(
        f"Output file      : {output_path}"
    )

    print(
        f"Records created  : {processed}"
    )

    print(
        f"Records skipped  : {skipped}"
    )

    print(
        f"Required fields  : {len(REQUIRED_COLUMNS)}"
    )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    convert_csv_to_jsonl(
        INPUT_CSV,
        OUTPUT_JSONL
    )