import React, { useMemo, useState } from 'react';
import { predictNetwork } from '../services/api';
import { validatePredictionInputs } from '../utils/predictionValidation';
import ModelAgreementCard from '../components/ModelAgreementCard';

export const FEATURES = [
  ['Cell Availability (%)', 'Cell Availability', '%', 'number', '89.4'],
  ['MTTR (hours)', 'MTTR', 'hours', 'number', '5.25'],
  ['Throughput (Mbps)', 'Observed Throughput', 'Mbps', 'number', '580.0'],
  ['Latency (ms)', 'Latency', 'ms', 'number', '77.2'],
  ['Packet Loss Rate (%)', 'Packet Loss Rate', '%', 'number', '6.24'],
  ['Call Drop Rate (%)', 'Call Drop Rate', '%', 'number', '0.95'],
  ['Handover Success Rate (%)', 'Handover Success', '%', 'number', '95.0'],
  ['Alarm Count', 'Alarm Count', 'total', 'number', '10'],
  ['Critical Alarm Count', 'Critical Alarms', 'total', 'number', '6.75'],
  ['Parameter Changes', 'Parameter Changes', 'total', 'number', '10'],
  ['Successful Configuration Changes (%)', 'Config Changes', '%', 'number', '94.5'],
  ['Data Usage (GB)', 'Data Usage', 'GB', 'number', '25.2'],
  ['User Count', 'User Count', 'users', 'number', '5060'],
  ['Signal Strength (dBm)', 'Signal Strength', 'dBm', 'number', '-90.0'],
  ['Jitter (ms)', 'Jitter', 'ms', 'number', '25.0'],
  ['Connection Setup Success Rate (%)', 'Connection Setup', '%', 'number', '94.9'],
  ['Security Incidents', 'Security Incidents', 'total', 'number', '10'],
  ['Authentication Failures', 'Authentication Failures', 'total', 'number', '8'],
  ['Temperature (Ã‚Â°C)', 'Temperature', '°C', 'number', '17.5'],
  ['Humidity (%)', 'Humidity', '%', 'number', '54.9'],
  ['Season', 'Season', '', 'select', 'Winter', ['Winter', 'Fall', 'Summer', 'Spring']],
  ['Weather', 'Weather', '', 'select', 'Snow', ['Snow', 'Rain', 'Clouds', 'Clear']],
];

export const REQUIRED = new Set(FEATURES.filter(([key]) => key !== 'Throughput (Mbps)').map(([key]) => key));
export const SAMPLE = Object.fromEntries(FEATURES.map(([key, , , type, sample]) => [key, type === 'number' ? Number(sample) : sample]));

export const PERFORMANCE_KEYS = new Set([
  'Cell Availability (%)', 'Alarm Count', 'Critical Alarm Count',
  'Parameter Changes', 'Successful Configuration Changes (%)',
  'Data Usage (GB)', 'User Count', 'Signal Strength (dBm)',
  'Security Incidents', 'Authentication Failures',
  'Humidity (%)', 'Season', 'Weather',
]);
const PERFORMANCE_TEMPERATURE_KEY = FEATURES.find(([key]) => key.startsWith('Temperature ('))?.[0];
if (PERFORMANCE_TEMPERATURE_KEY) PERFORMANCE_KEYS.add(PERFORMANCE_TEMPERATURE_KEY);
const PERFORMANCE_REQUIRED = new Set([...PERFORMANCE_KEYS, 'MTTR (hours)']);
const FAULT_REQUIRED = new Set(FEATURES.map(([key]) => key));

export function valueFor(key, value) {
  const feature = FEATURES.find(([candidate]) => candidate === key);
  return feature?.[3] === 'number' ? Number(value) : value;
}

function tone(label) {
  return `badge ${String(label || '').toLowerCase() === 'critical' ? 'badge-error' : String(label || '').toLowerCase() === 'poor' || String(label || '').toLowerCase() === 'high' ? 'badge-warning' : 'badge-success'}`;
}

export default function PredictionDashboard() {
  const [mode, setMode] = useState('network_performance');
  const [inputs, setInputs] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const visibleFeatures = useMemo(
    () => mode === 'fault_tolerance' ? FEATURES : FEATURES.filter(([key]) => PERFORMANCE_KEYS.has(key) || key === 'MTTR (hours)'),
    [mode],
  );
  const required = mode === 'fault_tolerance' ? FAULT_REQUIRED : PERFORMANCE_REQUIRED;
  const filled = useMemo(() => new Set(Object.entries(inputs).filter(([, value]) => value !== '' && value !== null && value !== undefined).map(([key]) => key)), [inputs]);
  const missing = [...required].filter((key) => !filled.has(key));

  const run = async (event) => {
    event.preventDefault();
    setError(null);
    setResult(null);
    const validationErrors = validatePredictionInputs(inputs, visibleFeatures, required);
    if (validationErrors.length) { setError(validationErrors.slice(0, 3).join(' ')); return; }
    setLoading(true);
    try {
      const response = await predictNetwork(Object.fromEntries(Object.entries(inputs).filter(([, value]) => value !== '' && value !== null && value !== undefined).map(([key, value]) => [key, valueFor(key, value)])), mode);
      if (!response?.prediction) throw new Error('Prediction agent returned no prediction data.');
      setResult(response);
    } catch (exception) {
      setError(exception?.message || 'Prediction request failed.');
    } finally {
      setLoading(false);
    }
  };

  const performance = result?.prediction?.network_performance;
  const fault = result?.prediction?.fault_risk;
  const classification = performance?.classification;
  const predictions = performance?.predictions || {};

  return <div className={`app-container ${mode === 'fault_tolerance' ? 'fault-tolerance-mode' : ''}`}>
    <div className="page-header"><h1 className="page-title">Network Performance &amp; Fault Prediction</h1><p className="page-subtitle">Choose whether to predict performance first or run the fault-tolerance model directly.</p></div>
    <div className="card prediction-mode-card"><div className="card-header"><div><div className="card-title">Prediction Mode</div><div className="card-subtitle">The selected mode controls which form fields and models are used.</div></div></div><div className="prediction-mode-toggle" role="group" aria-label="Prediction mode"><button type="button" className={`btn ${mode === 'network_performance' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => { setMode('network_performance'); setResult(null); setError(null); }}>Network Performance</button><button type="button" className={`btn ${mode === 'fault_tolerance' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => { setMode('fault_tolerance'); setResult(null); setError(null); }}>Fault Tolerance</button></div><p className="prediction-note">{mode === 'network_performance' ? 'Runs the performance model first, then uses its predicted KPIs for fault-risk estimation.' : 'Shows the full telemetry form and runs only the fault-tolerance model. The network-performance model is skipped.'}</p></div>
    <div className="card"><div className="card-header"><div><div className="card-title">{mode === 'fault_tolerance' ? 'Full Fault-Tolerance Telemetry' : 'Network Performance Telemetry'}</div><div className="card-subtitle">{mode === 'fault_tolerance' ? 'All inputs required by the fault-occurrence model.' : 'Performance-model inputs plus MTTR for the chained fault-risk prediction.'}</div></div><span className={`badge ${missing.length ? 'badge-warning' : 'badge-success'}`}>{required.size - missing.length} / {required.size} required</span></div>
      <form onSubmit={run}><div className="prediction-form-grid">{visibleFeatures.map(([key, label, unit, type, placeholder, options]) => <label className="prediction-field" key={key}><span>{label}{key === 'Throughput (Mbps)' && <small>Optional in performance mode</small>}{key === 'MTTR (hours)' && mode === 'network_performance' && <small>Required for fault handoff</small>}</span>{type === 'select' ? <select className="form-input" value={inputs[key] ?? ''} onChange={(event) => setInputs((current) => ({ ...current, [key]: event.target.value }))}><option value="">Select...</option>{options.map((option) => <option key={option} value={option}>{option}</option>)}</select> : <input className="form-input" type={type} step="any" placeholder={placeholder} value={inputs[key] ?? ''} onChange={(event) => setInputs((current) => ({ ...current, [key]: event.target.value }))} />} {unit && <small>{unit}</small>}</label>)}</div>
        <div className="prediction-actions"><div><button type="button" className="btn btn-secondary btn-xs" onClick={() => { setInputs(SAMPLE); setResult(null); setError(null); }}>Load Sample</button><button type="button" className="btn btn-secondary btn-xs" onClick={() => { setInputs({}); setResult(null); setError(null); }}>Clear</button></div><button type="submit" className="btn btn-primary" disabled={loading || missing.length > 0}>{loading ? 'Running prediction...' : `Run ${mode === 'fault_tolerance' ? 'Fault Tolerance' : 'Performance + Fault'} Prediction`}</button></div>
      </form>
    </div>
    {error && <div className="alert alert-error"><strong>Prediction failed: </strong>{error}</div>}
    {result && <>
      <div className="prediction-results"><div className="card"><div className="card-header"><div><div className="card-title">Predicted Network KPIs</div><div className="card-subtitle">ML outputs; not observed measurements</div></div><span className={tone(classification?.overall_risk)}>KPI: {classification?.overall_risk || 'Unavailable'}</span></div><div className="prediction-grid">{Object.entries(predictions).map(([key, value]) => <div className="prediction-value" key={key}><span>{key}</span><strong>{value}</strong></div>)}</div></div>
        <div className="card"><div className="card-header"><div><div className="card-title">Fault Occurrence Risk</div><div className="card-subtitle">Separate fault-risk model using the same telemetry</div></div><span className={tone(fault?.fault_risk)}>{fault?.fault_risk || fault?.status || 'Unavailable'}</span></div><div className="prediction-result-value fault-value">{fault?.predicted_fault_occurrence_rate_percent ?? 'Unavailable'}{fault?.predicted_fault_occurrence_rate_percent !== undefined && '%'}</div><p className="prediction-note">This is a model estimate, separate from performance classification.</p></div></div>
      <ModelAgreementCard prediction={result.prediction} />
      <div className="card"><div className="card-header"><div><div className="card-title">Rule-Based Network Performance Classification</div><div className="card-subtitle">Illustrative thresholds only; not 3GPP requirements or operator SLAs</div></div><span className={tone(classification?.overall_risk)}>{classification?.overall_risk || classification?.status || 'Incomplete'}</span></div>{classification?.performance_score !== null && classification?.performance_score !== undefined && <div className="prediction-result-value">{classification.performance_score}<small> / 100 score</small></div>}<div className="prediction-note">{(classification?.reasons || ['Seven KPI predictions are required for an overall classification.']).map((reason) => <div key={reason}>• {reason}</div>)}</div>{classification?.invalid_predictions && <div className="alert alert-warning">The checked-in performance artifact returned fewer than seven KPI predictions, so the overall score remains unavailable.</div>}</div>
    </>}
  </div>;
}
