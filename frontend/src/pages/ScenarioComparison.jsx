import React, { useMemo, useState } from 'react';
import { predictNetwork } from '../services/api';
import { FEATURES, REQUIRED, SAMPLE, valueFor } from './PredictionDashboard';
import { validatePredictionInputs } from '../utils/predictionValidation';

const EMPTY = {};

function payload(inputs) {
  return Object.fromEntries(
    Object.entries(inputs)
      .filter(([, value]) => value !== '' && value !== null && value !== undefined)
      .map(([key, value]) => [key, valueFor(key, value)])
  );
}

function tone(label) {
  const value = String(label || '').toLowerCase();
  return `badge ${value === 'critical' || value === 'high' ? 'badge-error' : value === 'poor' || value === 'medium' ? 'badge-warning' : 'badge-success'}`;
}

function ResultCard({ title, result }) {
  const performance = result?.prediction?.network_performance;
  const fault = result?.prediction?.fault_risk;
  const classification = performance?.classification;
  const predictions = performance?.predictions || {};

  return <div className="card scenario-result-card">
    <div className="card-header"><div><div className="card-title">{title}</div><div className="card-subtitle">ML predictions and rule-based classification</div></div><span className={`badge ${result?.status === 'success' ? 'badge-success' : 'badge-warning'}`}>{result?.status || 'not run'}</span></div>
    <div className="scenario-summary-grid">
      <div><span>Network status</span><strong className={tone(classification?.overall_risk)}>{classification?.overall_risk || 'Unavailable'}</strong></div>
      <div><span>Performance score</span><strong>{classification?.performance_score ?? '—'}<small>{classification?.performance_score !== null && classification?.performance_score !== undefined ? ' / 100' : ''}</small></strong></div>
      <div><span>Fault risk</span><strong className={tone(fault?.fault_risk)}>{fault?.fault_risk || 'Unavailable'}</strong></div>
      <div><span>Fault rate</span><strong>{fault?.predicted_fault_occurrence_rate_percent ?? '—'}{fault?.predicted_fault_occurrence_rate_percent !== undefined ? '%' : ''}</strong></div>
    </div>
    <div className="scenario-kpi-list">
      {Object.entries(predictions).map(([key, value]) => <div className="scenario-kpi-row" key={key}><span>{key}</span><strong>{value}</strong><small className={tone(classification?.kpi_classifications?.[key]?.classification)}>{classification?.kpi_classifications?.[key]?.classification || 'Unavailable'}</small></div>)}
    </div>
    {classification?.reasons?.length > 0 && <p className="prediction-note">{classification.reasons[0]}</p>}
  </div>;
}

function ScenarioForm({ label, inputs, setInputs, onLoadSample, missing }) {
  return <div className="card">
    <div className="card-header"><div><div className="card-title">{label}</div><div className="card-subtitle">Complete the required telemetry fields</div></div><span className={`badge ${missing.length ? 'badge-warning' : 'badge-success'}`}>{REQUIRED.size - missing.length} / {REQUIRED.size} required</span></div>
    <div className="prediction-form-grid">{FEATURES.map(([key, fieldLabel, unit, type, placeholder, options]) => <label className="prediction-field" key={key}><span>{fieldLabel}{key === 'Throughput (Mbps)' && <small>Optional</small>}</span>{type === 'select' ? <select className="form-input" value={inputs[key] ?? ''} onChange={(event) => setInputs((current) => ({ ...current, [key]: event.target.value }))}><option value="">Select...</option>{options.map((option) => <option key={option} value={option}>{option}</option>)}</select> : <input className="form-input" type={type} step="any" placeholder={placeholder} value={inputs[key] ?? ''} onChange={(event) => setInputs((current) => ({ ...current, [key]: event.target.value }))} />} {unit && <small>{unit}</small>}</label>)}</div>
    <button type="button" className="btn btn-secondary btn-xs" onClick={onLoadSample}>Load sample</button>
  </div>;
}

export default function ScenarioComparison() {
  const [scenarioA, setScenarioA] = useState({ ...SAMPLE });
  const [scenarioB, setScenarioB] = useState({ ...SAMPLE, 'Packet Loss Rate (%)': 1.5, 'Latency (ms)': 35, 'Call Drop Rate (%)': 0.3, 'Jitter (ms)': 8 });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const missingA = useMemo(() => [...REQUIRED].filter((key) => scenarioA[key] === '' || scenarioA[key] === undefined || scenarioA[key] === null), [scenarioA]);
  const missingB = useMemo(() => [...REQUIRED].filter((key) => scenarioB[key] === '' || scenarioB[key] === undefined || scenarioB[key] === null), [scenarioB]);

  const compare = async (event) => {
    event.preventDefault();
    setError(null); setResults(null);
    const errors = [...validatePredictionInputs(scenarioA, FEATURES, REQUIRED), ...validatePredictionInputs(scenarioB, FEATURES, REQUIRED)];
    if (errors.length) { setError(errors.slice(0, 4).join(' ')); return; }
    setLoading(true);
    try {
      const [resultA, resultB] = await Promise.all([predictNetwork(payload(scenarioA)), predictNetwork(payload(scenarioB))]);
      if (!resultA?.prediction || !resultB?.prediction) throw new Error('Prediction Agent returned incomplete scenario results.');
      setResults({ a: resultA, b: resultB });
    } catch (exception) { setError(exception?.message || 'Scenario comparison failed.'); }
    finally { setLoading(false); }
  };

  const scoreA = results?.a?.prediction?.network_performance?.classification?.performance_score;
  const scoreB = results?.b?.prediction?.network_performance?.classification?.performance_score;
  const scoreDelta = Number.isFinite(scoreA) && Number.isFinite(scoreB) ? scoreB - scoreA : null;

  return <div className="app-container">
    <div className="page-header"><h1 className="page-title">Scenario Comparison</h1><p className="page-subtitle">Compare two network conditions using the same Prediction Agent and ML models.</p></div>
    <form onSubmit={compare}><div className="scenario-form-grid"><ScenarioForm label="Scenario A · Current network" inputs={scenarioA} setInputs={setScenarioA} onLoadSample={() => setScenarioA({ ...SAMPLE })} missing={missingA} /><ScenarioForm label="Scenario B · What-if network" inputs={scenarioB} setInputs={setScenarioB} onLoadSample={() => setScenarioB({ ...SAMPLE })} missing={missingB} /></div><div className="prediction-actions"><span className="prediction-note">Guardrails reject missing, non-numeric, infinite, out-of-range percentage, and negative counter values.</span><button className="btn btn-primary" type="submit" disabled={loading || missingA.length > 0 || missingB.length > 0}>{loading ? 'Comparing scenarios...' : 'Compare Scenarios'}</button></div></form>
    {error && <div className="alert alert-error"><strong>Comparison failed: </strong>{error}</div>}
    {results && <><div className="prediction-results"><ResultCard title="Scenario A · Current network" result={results.a} /><ResultCard title="Scenario B · What-if network" result={results.b} /></div><div className="card scenario-delta-card"><div className="card-header"><div><div className="card-title">Change Summary</div><div className="card-subtitle">Difference is calculated as Scenario B minus Scenario A.</div></div><span className={tone(scoreDelta !== null && scoreDelta >= 0 ? 'low' : 'high')}>{scoreDelta === null ? 'Unavailable' : `${scoreDelta >= 0 ? '+' : ''}${scoreDelta.toFixed(1)} points`}</span></div><p className="prediction-note">{scoreDelta === null ? 'A performance-score comparison is unavailable because one or both scenarios did not produce a complete score.' : scoreDelta >= 0 ? `The what-if scenario improves the rule-based performance score by ${scoreDelta.toFixed(1)} points.` : `The what-if scenario reduces the rule-based performance score by ${Math.abs(scoreDelta).toFixed(1)} points.`}</p></div></>}
  </div>;
}
