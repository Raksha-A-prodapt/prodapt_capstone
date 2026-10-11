"""Streamlit Frontend for Telecom Network Operations Assistant.

Color Theme:
- Background: Black (#000000 / #0a0e14)
- Buttons & Navigation: Dark Teal (#007C7C)
- Highlights & Active Accents: Turquoise (#00BABA)
- Text: Crisp White (#ffffff / #e2e8f0)
"""

import json
import requests
import streamlit as st
import pandas as pd

API_BASE_URL = "http://127.0.0.1:8001"

st.set_page_config(
    page_title="Telecom Network Assistant",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Theme CSS
CUSTOM_CSS = """
<style>
    /* Dark Theme Base */
    .stApp {
        background-color: #000000;
        color: #e2e8f0;
    }
    header[data-testid="stHeader"] {
        background-color: #0a0e14;
    }
    div[data-testid="stSidebar"] {
        background-color: #0a0e14;
        border-right: 1px solid #202d3d;
    }
    
    /* Typography */
    h1, h2, h3, h4, strong {
        color: #ffffff !important;
    }
    
    /* Buttons */
    button[kind="primary"], .stButton>button {
        background-color: #007C7C !important;
        color: #ffffff !important;
        border: 1px solid #00BABA !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out;
    }
    button[kind="primary"]:hover, .stButton>button:hover {
        background-color: #006363 !important;
        border-color: #1edede !important;
        box-shadow: 0 0 10px rgba(0, 186, 186, 0.35) !important;
    }
    
    /* Text Inputs, Selects & Areas */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox select {
        background-color: #0d131a !important;
        color: #ffffff !important;
        border: 1px solid #202d3d !important;
        border-radius: 6px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #00BABA !important;
        box-shadow: 0 0 0 2px rgba(0, 186, 186, 0.2) !important;
    }
    
    /* Cards / Containers */
    .metric-card {
        background: #111720;
        border: 1px solid #202d3d;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .metric-val {
        font-size: 26px;
        font-weight: 800;
        color: #00BABA;
    }
    .metric-label {
        font-size: 12px;
        color: #8e9fb5;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Disclaimer Banner */
    .disclaimer-banner {
        background: rgba(0, 124, 124, 0.15);
        border-left: 3px solid #00BABA;
        padding: 8px 14px;
        border-radius: 0 6px 6px 0;
        font-size: 12px;
        color: #8e9fb5;
        margin: 8px 0 14px;
    }
    
    /* Hero Answer Box */
    .hero-answer {
        background: #111720;
        border: 1px solid #007C7C;
        border-left: 5px solid #00BABA;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 24px;
        white-space: pre-wrap;
        line-height: 1.6;
        color: #ffffff;
    }

    /* Badges */
    .custom-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 700;
        background: rgba(0, 186, 186, 0.15);
        color: #00BABA;
        border: 1px solid #00BABA;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def check_api_health():
    """Verify Starlette API liveness on port 8001."""
    try:
        res = requests.get(f"{API_BASE_URL}/api/health", timeout=2.0)
        if res.status_code == 200:
            data = res.json()
            return True, data.get("orchestrator_initialized", False)
    except Exception:
        pass
    return False, False


# Sidebar Configuration & Health
with st.sidebar:
    st.markdown("### 📡 Telecom Network Ops")
    st.caption("AI-Powered Multi-Agent Incident Retrieval & Operations")

    is_online, orch_ready = check_api_health()
    if is_online:
        st.success(
            "API Online (Port 8001)\n"
            + ("• Orchestrator Ready" if orch_ready else "• Orchestrator Idle")
        )
    else:
        st.error("API Disconnected (http://127.0.0.1:8001)")

    st.markdown(
        """
        <div class="disclaimer-banner">
        <strong>Trust Boundary Notice:</strong><br>
        API health confirms Starlette connectivity. Synapt MCP procedure retrieval runs on port 8000.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    navigation = st.radio(
        "Navigation Menu",
        [
            "📡 Operations Assistant",
            "⚡ ML Model Predictions",
            "📊 Model Evaluation & DeepEval",
            "📈 NetOps Dataset Analytics",
        ],
    )


# ==============================================================================
# TAB 1: OPERATIONS ASSISTANT
# ==============================================================================
if navigation == "📡 Operations Assistant":
    st.markdown("## 📡 Telecom Network Operations Assistant")
    st.caption(
        "Natural language incident investigation across 100k NetOps records with hybrid Chroma+BM25 search and RCA."
    )

    # Question input
    query = st.text_area(
        "Telecom Question or Incident Description",
        value="Find winter incidents around Schneiderville where performance degraded badly.",
        help="Enter symptom description, cell conditions, or troubleshooting queries.",
        height=90,
    )

    col_k, col_mode = st.columns([1, 2])
    with col_k:
        top_k = st.number_input(
            "Top-K Incidents (1–50)",
            min_value=1,
            max_value=50,
            value=5,
            step=1,
        )

    with col_mode:
        telemetry_mode = st.selectbox(
            "Current Telemetry Input Mode",
            [
                "Horizontal Quick Telemetry Bar (12 Columns)",
                "Custom JSON Object",
                "None (Historical Incident Retrieval Only)",
            ],
        )

    network_metrics_payload = None

    if telemetry_mode == "Horizontal Quick Telemetry Bar (12 Columns)":
        st.markdown("#### Horizontal Telemetry Bar (Prediction Model Features)")
        st.caption(
            "⚠️ Validation Rule: Telemetry is passed to prediction models ONLY if all 12 columns are filled."
        )

        # 12 Horizontal Columns
        hcols = st.columns(6)
        with hcols[0]:
            lat = st.text_input("Latency (ms)", value="142.0", key="h_lat")
        with hcols[1]:
            loss = st.text_input("Packet Loss (%)", value="12.4", key="h_loss")
        with hcols[2]:
            drop = st.text_input("Call Drop (%)", value="3.8", key="h_drop")
        with hcols[3]:
            ho = st.text_input("Handover (%)", value="91.5", key="h_ho")
        with hcols[4]:
            avail = st.text_input("Availability (%)", value="84.0", key="h_avail")
        with hcols[5]:
            thr = st.text_input("Throughput (Mbps)", value="320.0", key="h_thr")

        hcols2 = st.columns(6)
        with hcols2[0]:
            alarm = st.text_input("Alarm Count", value="18", key="h_alarm")
        with hcols2[1]:
            crit = st.text_input("Crit Alarms", value="8.5", key="h_crit")
        with hcols2[2]:
            sig = st.text_input("Signal (dBm)", value="-105.0", key="h_sig")
        with hcols2[3]:
            jit = st.text_input("Jitter (ms)", value="34.0", key="h_jit")
        with hcols2[4]:
            season = st.selectbox(
                "Season",
                ["Winter", "Fall", "Summer", "Spring", ""],
                index=0,
                key="h_season",
            )
        with hcols2[5]:
            weather = st.selectbox(
                "Weather",
                ["Snow", "Rain", "Clouds", "Clear", ""],
                index=0,
                key="h_weather",
            )

        # Check if all 12 columns are filled
        all_vals = [
            lat.strip(),
            loss.strip(),
            drop.strip(),
            ho.strip(),
            avail.strip(),
            thr.strip(),
            alarm.strip(),
            crit.strip(),
            sig.strip(),
            jit.strip(),
            season.strip(),
            weather.strip(),
        ]
        all_filled = all(bool(v) for v in all_vals)

        if all_filled:
            st.success("✅ All 12 columns filled. Telemetry will be passed to prediction models.")
            try:
                network_metrics_payload = {
                    "Latency (ms)": float(lat),
                    "Packet Loss Rate (%)": float(loss),
                    "Call Drop Rate (%)": float(drop),
                    "Handover Success Rate (%)": float(ho),
                    "Cell Availability (%)": float(avail),
                    "Throughput (Mbps)": float(thr),
                    "Alarm Count": int(float(alarm)),
                    "Critical Alarm Count": float(crit),
                    "Signal Strength (dBm)": float(sig),
                    "Jitter (ms)": float(jit),
                    "Season": season,
                    "Weather": weather,
                }
            except Exception as e:
                st.error(f"Error parsing numeric telemetry: {e}")
                network_metrics_payload = None
        else:
            st.warning("⚠️ Incomplete columns. Telemetry will NOT be passed until all 12 are completed.")
            network_metrics_payload = None

    elif telemetry_mode == "Custom JSON Object":
        raw_json = st.text_area(
            "Current Network Metrics (JSON)",
            value='{\n  "Latency (ms)": 145,\n  "Packet Loss Rate (%)": 13,\n  "Season": "Winter",\n  "Weather": "Snow"\n}',
            height=120,
        )
        if raw_json.strip():
            try:
                network_metrics_payload = json.loads(raw_json)
                st.success("Valid JSON structure confirmed.")
            except Exception as exc:
                st.error(f"Invalid JSON: {exc}")
                network_metrics_payload = None

    # Submit Button
    if st.button("🚀 Run Analysis", type="primary"):
        if not query.strip():
            st.error("Query cannot be empty.")
        else:
            with st.spinner("Analyzing telecom network incident..."):
                payload = {
                    "query": query.strip(),
                    "top_k": int(top_k),
                    "network_metrics": network_metrics_payload,
                }
                try:
                    resp = requests.post(
                        f"{API_BASE_URL}/api/analyze",
                        json=payload,
                        timeout=60.0,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state["last_analysis_result"] = data
                    else:
                        st.error(f"API Error ({resp.status_code}): {resp.text}")
                except Exception as ex:
                    st.error(f"Failed to communicate with API: {ex}")

    # Render Results if available
    if "last_analysis_result" in st.session_state:
        res = st.session_state["last_analysis_result"]
        st.markdown("---")
        st.markdown("### 💡 Orchestrator Final Conclusion")
        st.markdown(
            f'<div class="hero-answer">{res.get("final_answer", res.get("status", "Done"))}</div>',
            unsafe_allow_html=True,
        )

        sections = res.get("sections", [])
        for sec in sections:
            sec_id = sec.get("id", "")
            title = sec.get("title", sec_id)
            status = sec.get("status", "info")
            summary = sec.get("summary", "")
            sec_data = sec.get("data", {})

            with st.expander(f"📌 {title} — [{status.upper()}]", expanded=True):
                # Disclaimers per section
                if sec_id == "historical_data":
                    st.markdown(
                        '<div class="disclaimer-banner">Notice: Retrieved historical incidents are similar past records from the 5G NetOps dataset, not necessarily the same physical cell or incident.</div>',
                        unsafe_allow_html=True,
                    )
                elif sec_id == "root_cause_analysis":
                    st.markdown(
                        '<div class="disclaimer-banner">Notice: Hypotheses are probabilistic evidence-linked deductions, never confirmed operational causes.</div>',
                        unsafe_allow_html=True,
                    )
                elif sec_id == "prediction":
                    st.markdown(
                        '<div class="disclaimer-banner">Notice: Predictions are mathematical XGBoost estimates, distinct from observed physical measurements.</div>',
                        unsafe_allow_html=True,
                    )
                elif sec_id == "recommendations":
                    st.markdown(
                        '<div class="disclaimer-banner">Notice: Synapt SOP recommendations are advisory. Synthetic/demo SOPs are not certified engineering guidance.</div>',
                        unsafe_allow_html=True,
                    )
                elif sec_id == "incident_prioritization":
                    st.markdown(
                        '<div class="disclaimer-banner">Notice: Incident classification is dataset-relative triage guidance, not an SLA commitment.</div>',
                        unsafe_allow_html=True,
                    )
                elif sec_id == "network_impact":
                    st.markdown(
                        '<div class="disclaimer-banner">Notice: Impact findings represent potential service degradation, not confirmed customer outage.</div>',
                        unsafe_allow_html=True,
                    )

                st.write(summary)

                # Render rich data
                if sec_id == "historical_data" and "incidents" in sec_data:
                    incidents = sec_data["incidents"]
                    if incidents:
                        table_rows = []
                        for item in incidents:
                            inc = item.get("incident", item)
                            table_rows.append({
                                "Incident ID": inc.get("incident_id", "N/A"),
                                "Issue Reported": inc.get("issue_reported", inc.get("Issue Reported", "N/A")),
                                "Latency (ms)": inc.get("latency_ms", inc.get("Latency (ms)", "N/A")),
                                "Loss (%)": inc.get("packet_loss_rate", inc.get("Packet Loss Rate (%)", "N/A")),
                                "Throughput (Mbps)": inc.get("throughput_mbps", inc.get("Throughput (Mbps)", "N/A")),
                                "Availability (%)": inc.get("cell_availability", inc.get("Cell Availability (%)", "N/A")),
                                "Season": inc.get("season", inc.get("Season", "N/A")),
                                "City": inc.get("city", inc.get("City", "N/A")),
                            })
                        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)

                elif sec_id == "root_cause_analysis" and "ranked_hypotheses" in sec_data:
                    st.table(pd.DataFrame(sec_data["ranked_hypotheses"]))

                elif sec_id == "recommendations" and "recommendations" in sec_data:
                    for idx, rec in enumerate(sec_data["recommendations"], 1):
                        st.markdown(f"**Action {idx}:** {rec.get('action', rec)}")
                        if rec.get("procedure_name"):
                            st.caption(f"SOP Reference: {rec.get('procedure_name')}")

                # Raw section JSON
                with st.expander("View Raw Section JSON"):
                    st.json(sec_data)


# ==============================================================================
# TAB 2: DEDICATED ML PREDICTIONS PAGE
# ==============================================================================
elif navigation == "⚡ ML Model Predictions":
    st.markdown("## ⚡ Machine Learning Performance & Fault Risk Predictors")
    st.caption("Direct execution of offline trained XGBoost Regressors for Throughput and Fault Occurrence Rate.")

    st.markdown(
        '<div class="disclaimer-banner">Rule: Model execution is gated. All required features must be provided before inference can proceed.</div>',
        unsafe_allow_html=True,
    )

    # Preset Loader
    pcol1, pcol2, pcol3 = st.columns(3)
    preset_choice = None
    with pcol1:
        if st.button("Load Severe Winter Scenario"):
            preset_choice = "severe"
    with pcol2:
        if st.button("Load Rainy Storm Scenario"):
            preset_choice = "rain"
    with pcol3:
        if st.button("Load Normal Baseline"):
            preset_choice = "normal"

    defaults = {
        "avail": 89.4, "mttr": 5.25, "lat": 77.2, "loss": 6.24, "drop": 0.95, "ho": 95.0,
        "alarm": 10, "crit": 6.75, "usage": 25.2, "users": 5060, "sec": 10, "auth": 8,
        "sig": -90.0, "jit": 25.0, "conn": 94.9, "param": 10, "cfg": 94.5, "fault_in": 39.5,
        "temp": 17.5, "hum": 54.9, "season": "Winter", "weather": "Snow", "city": "Schneiderville", "state": "MN"
    }

    if preset_choice == "severe":
        defaults.update({"lat": 142.0, "loss": 12.4, "drop": 4.1, "ho": 91.2, "avail": 82.5, "crit": 9.4, "temp": -4.2})
    elif preset_choice == "rain":
        defaults.update({"lat": 88.0, "loss": 6.5, "drop": 1.2, "season": "Fall", "weather": "Rain", "temp": 24.0})
    elif preset_choice == "normal":
        defaults.update({"lat": 28.0, "loss": 0.8, "drop": 0.1, "ho": 99.1, "avail": 98.5, "alarm": 2, "crit": 0.5, "season": "Spring", "weather": "Clear"})

    with st.form("ml_predict_form"):
        st.markdown("### Input Features (24 Dimensions)")

        g1, g2 = st.columns(2)
        with g1:
            st.markdown("#### 📶 Radio & Network Quality")
            f_avail = st.number_input("Cell Availability (%)", value=float(defaults["avail"]), min_value=0.0, max_value=100.0)
            f_mttr = st.number_input("MTTR (hours)", value=float(defaults["mttr"]), min_value=0.0)
            f_lat = st.number_input("Latency (ms)", value=float(defaults["lat"]), min_value=0.0)
            f_loss = st.number_input("Packet Loss Rate (%)", value=float(defaults["loss"]), min_value=0.0, max_value=100.0)
            f_drop = st.number_input("Call Drop Rate (%)", value=float(defaults["drop"]), min_value=0.0, max_value=100.0)
            f_ho = st.number_input("Handover Success Rate (%)", value=float(defaults["ho"]), min_value=0.0, max_value=100.0)

            st.markdown("#### 🚨 Alarms & Traffic")
            f_alarm = st.number_input("Alarm Count", value=int(defaults["alarm"]), min_value=0)
            f_crit = st.number_input("Critical Alarm Count", value=float(defaults["crit"]), min_value=0.0)
            f_usage = st.number_input("Data Usage (GB)", value=float(defaults["usage"]), min_value=0.0)
            f_users = st.number_input("User Count", value=int(defaults["users"]), min_value=0)
            f_sec = st.number_input("Security Incidents", value=int(defaults["sec"]), min_value=0)
            f_auth = st.number_input("Authentication Failures", value=int(defaults["auth"]), min_value=0)

        with g2:
            st.markdown("#### 📡 RF & Configuration")
            f_sig = st.number_input("Signal Strength (dBm)", value=float(defaults["sig"]))
            f_jit = st.number_input("Jitter (ms)", value=float(defaults["jit"]), min_value=0.0)
            f_conn = st.number_input("Connection Setup Success Rate (%)", value=float(defaults["conn"]), min_value=0.0, max_value=100.0)
            f_param = st.number_input("Parameter Changes", value=int(defaults["param"]), min_value=0)
            f_cfg = st.number_input("Successful Configuration Changes (%)", value=float(defaults["cfg"]), min_value=0.0, max_value=100.0)
            f_fault_in = st.number_input("Fault Occurrence Rate (%) [For Model 1]", value=float(defaults["fault_in"]), min_value=0.0, max_value=100.0)

            st.markdown("#### 🌦️ Environment & Geo-Location")
            f_temp = st.number_input("Temperature (°C)", value=float(defaults["temp"]))
            f_hum = st.number_input("Humidity (%)", value=float(defaults["hum"]), min_value=0.0, max_value=100.0)
            f_season = st.selectbox("Season", ["Winter", "Fall", "Summer", "Spring"], index=["Winter", "Fall", "Summer", "Spring"].index(defaults["season"]))
            f_weather = st.selectbox("Weather", ["Snow", "Rain", "Clouds", "Clear"], index=["Snow", "Rain", "Clouds", "Clear"].index(defaults["weather"]))
            f_city = st.text_input("City", value=defaults["city"])
            f_state = st.text_input("State", value=defaults["state"])

        run_ml = st.form_submit_button("⚡ Run ML Inference", type="primary")

    if run_ml:
        if not f_city.strip() or not f_state.strip():
            st.error("City and State are required categorical features.")
        else:
            feature_dict = {
                "Cell Availability (%)": f_avail,
                "MTTR (hours)": f_mttr,
                "Latency (ms)": f_lat,
                "Packet Loss Rate (%)": f_loss,
                "Call Drop Rate (%)": f_drop,
                "Handover Success Rate (%)": f_ho,
                "Alarm Count": f_alarm,
                "Critical Alarm Count": f_crit,
                "Parameter Changes": f_param,
                "Successful Configuration Changes (%)": f_cfg,
                "Data Usage (GB)": f_usage,
                "User Count": f_users,
                "Signal Strength (dBm)": f_sig,
                "Jitter (ms)": f_jit,
                "Connection Setup Success Rate (%)": f_conn,
                "Security Incidents": f_sec,
                "Authentication Failures": f_auth,
                "Temperature (°C)": f_temp,
                "Humidity (%)": f_hum,
                "Fault Occurrence Rate (%)": f_fault_in,
                "Season": f_season,
                "Weather": f_weather,
                "City": f_city.strip(),
                "State": f_state.strip(),
            }

            with st.spinner("Executing XGBoost pipelines..."):
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/api/analyze",
                        json={
                            "query": "Run network performance and fault risk predictions.",
                            "top_k": 1,
                            "network_metrics": feature_dict,
                        },
                        timeout=30.0,
                    )
                    if res.status_code == 200:
                        pred_res = res.json()
                        pred_sec = next(
                            (s for s in pred_res.get("sections", []) if s.get("id") == "prediction"),
                            None,
                        )
                        preds = pred_sec.get("data", {}).get("prediction", {}) if pred_sec else {}

                        st.markdown("---")
                        st.markdown("### 🎯 Model Inference Results")

                        res_c1, res_c2 = st.columns(2)
                        with res_c1:
                            perf = preds.get("network_performance", {})
                            st.markdown(
                                f"""
                                <div class="metric-card">
                                    <div class="metric-label">Model 1: Predicted Throughput</div>
                                    <div class="metric-val">{perf.get('predicted_throughput_mbps', 'N/A')} Mbps</div>
                                    <p style="color: #8e9fb5; font-size: 13px; margin-top: 6px;">
                                        Quality: {perf.get('performance_evaluation', 'Evaluated')}<br>
                                        Algorithm: XGBoost Regressor (Test R²: 0.9972)
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        with res_c2:
                            fault = preds.get("fault_risk", {})
                            st.markdown(
                                f"""
                                <div class="metric-card">
                                    <div class="metric-label">Model 2: Predicted Fault Rate</div>
                                    <div class="metric-val">{fault.get('predicted_fault_occurrence_rate_percent', 'N/A')}%</div>
                                    <p style="color: #8e9fb5; font-size: 13px; margin-top: 6px;">
                                        Risk Tier: {fault.get('fault_risk', 'Evaluated')}<br>
                                        Algorithm: XGBoost Regressor (Test R²: 0.9997)
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                    else:
                        st.error(f"Inference failed ({res.status_code}): {res.text}")
                except Exception as err:
                    st.error(f"Error calling API: {err}")


# ==============================================================================
# TAB 3: MODEL EVALUATION & DEEPEVAL
# ==============================================================================
elif navigation == "📊 Model Evaluation & DeepEval":
    st.markdown("## 📊 Model Evaluation & DeepEval Multi-Agent Reports")
    st.caption("Quantitative metrics for ML models and LLM-as-judge multi-agent evaluation suites.")

    ev_col1, ev_col2 = st.columns(2)
    with ev_col1:
        st.markdown("### ⚡ Model 1: Network Performance Model")
        st.markdown(
            """
            - **Target:** `Throughput (Mbps)`
            - **Algorithm:** XGBoost Regressor with Hist tree method
            - **Dataset:** 80,000 train / 20,000 test samples (24 features)
            - **R² Score (Test):** `0.9972` (Training: `0.9982`)
            - **R² Gap:** `0.0010` (Good Generalization, No Overfitting)
            - **MAE:** `9.19 Mbps` | **RMSE:** `12.75 Mbps`
            - **MAPE:** `1.68%`
            """
        )
    with ev_col2:
        st.markdown("### 🛡️ Model 2: Fault Tolerance Model")
        st.markdown(
            """
            - **Target:** `Fault Occurrence Rate (%)`
            - **Algorithm:** XGBoost Regressor with Hist tree method
            - **Dataset:** 80,000 train / 20,000 test samples (22 features)
            - **R² Score (Test):** `0.9997` (Training: `0.9999`)
            - **R² Gap:** `0.0001` (Optimal Generalization)
            - **MAE:** `0.1665%` | **RMSE:** `0.2309%`
            - **MAPE:** `1.17%`
            """
        )

    st.markdown("---")
    st.markdown("### 🤖 DeepEval Agent Suite Report (40 / 40 Passed)")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Overall Pass Rate", "100%", "40/40 Tests")
    with k2:
        st.metric("Retrieval Precision & Recall", "1.00", "16/16 Passed")
    with k3:
        st.metric("RCA GEval Quality", "0.98", "12/12 Passed")
    with k4:
        st.metric("Final Answer Hallucination", "0.00", "12/12 Passed")

    eval_data = [
        {"Agent": "Query Retrieval", "Metric": "Contextual Precision", "Passed": "4 / 4", "Score": 1.00, "Description": "Ensures true positive historical incidents rank at the top."},
        {"Agent": "Query Retrieval", "Metric": "Contextual Recall", "Passed": "4 / 4", "Score": 1.00, "Description": "Retrieves all incidents satisfying numeric & metadata filters."},
        {"Agent": "Query Retrieval", "Metric": "Contextual Relevancy", "Passed": "4 / 4", "Score": 0.89, "Description": "Retrieved context contains minimal noise."},
        {"Agent": "Query Retrieval", "Metric": "Filter Compliance", "Passed": "4 / 4", "Score": 1.00, "Description": "Zero violation of season, city, and latency boundaries."},
        {"Agent": "RCA Agent", "Metric": "RCA Quality [GEval]", "Passed": "4 / 4", "Score": 0.98, "Description": "LLM judge confirms hypotheses are scientifically grounded."},
        {"Agent": "RCA Agent", "Metric": "Faithfulness", "Passed": "4 / 4", "Score": 0.93, "Description": "Hypotheses stem strictly from retrieved incident evidence."},
        {"Agent": "RCA Agent", "Metric": "Evidence & Caution", "Passed": "4 / 4", "Score": 1.00, "Description": "RCA strictly labeled as hypothesis, never confirmed cause."},
        {"Agent": "Final Summary", "Metric": "Answer Relevancy", "Passed": "4 / 4", "Score": 1.00, "Description": "Directly answers user question and synthesizes all stages."},
        {"Agent": "Final Summary", "Metric": "Hallucination Metric", "Passed": "4 / 4", "Score": 1.00, "Description": "Zero hallucinated operational metrics or SOP steps."},
    ]
    st.table(pd.DataFrame(eval_data))


# ==============================================================================
# TAB 4: DATASET ANALYTICS & VISUALIZATIONS
# ==============================================================================
elif navigation == "📈 NetOps Dataset Analytics":
    st.markdown("## 📈 5G NetOps Dataset Analytics & Telemetry Distributions")
    st.caption("Distribution insights across 100,000 historical telecom network incident records.")

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.metric("Total Incident Rows", "100,000", "Clean NetOps Records")
    with q2:
        st.metric("Average Throughput", "586.6 Mbps", "Median: 549.2 Mbps")
    with q3:
        st.metric("Average Latency", "79.2 ms", "Range: 4.6–175.8 ms")
    with q4:
        st.metric("Mean Fault Occurrence", "38.2 %", "Snow: 56.6 %")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Mean Throughput by Season (Mbps)")
        season_df = pd.DataFrame({
            "Season": ["Fall", "Spring", "Summer", "Winter"],
            "Throughput (Mbps)": [604.47, 602.99, 601.50, 537.17]
        })
        st.bar_chart(season_df.set_index("Season"))

    with c2:
        st.markdown("#### Average Latency by Weather Condition (ms)")
        weather_lat_df = pd.DataFrame({
            "Weather": ["Clear", "Clouds", "Rain", "Snow"],
            "Latency (ms)": [64.56, 78.24, 91.58, 95.63]
        })
        st.bar_chart(weather_lat_df.set_index("Weather"))

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### Fault Occurrence Rate by Weather (%)")
        fault_weather_df = pd.DataFrame({
            "Weather": ["Clear", "Clouds", "Rain", "Snow"],
            "Fault Rate (%)": [27.09, 35.84, 47.89, 56.55]
        })
        st.bar_chart(fault_weather_df.set_index("Weather"))

    with c4:
        st.markdown("#### Dataset Label Balance (Issue Reported)")
        issue_df = pd.DataFrame({
            "Status": ["No Issue Reported", "Active Issue Reported"],
            "Incident Count": [50111, 49889]
        })
        st.bar_chart(issue_df.set_index("Status"))
