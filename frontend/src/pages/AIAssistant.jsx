import React, { useState } from 'react';
import { analyzeQuery, submitFeedback } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import AgentFlow from '../components/AgentFlow';
import AnalysisResults from '../components/AnalysisResults';
import ModelAgreementCard from '../components/ModelAgreementCard';
import { FEATURES as MODEL_FEATURES, PERFORMANCE_KEYS, SAMPLE as SAMPLE_TELEMETRY } from './PredictionDashboard';

const EXAMPLE_QUERIES = [
  {
    title: 'Winter Schneiderville Congestion',
    query: 'Find winter incidents around Schneiderville where performance degraded badly.',
  },
  {
    title: 'Handover & Fault Escalation',
    query: 'A network region has increasing fault occurrence and declining handover success. What factors contributed?',
  },
  {
    title: 'Alarms & High Latency',
    query: 'Multiple cells are experiencing poor service quality, high latency, and increasing alarm counts.',
  },
  {
    title: 'SOP Troubleshooting Request',
    query: 'Cell is experiencing high latency, packet loss, and critical alarms. What troubleshooting procedures and actions should be taken?',
  },
  {
    title: 'Metadata Filter Test',
    query: 'Find incidents where the city is Schneiderville during the Winter season.',
  },
];

const TELEMETRY_FIELDS = MODEL_FEATURES.map(([key, label, unit, type, placeholder, options]) => ({
  key,
  label,
  unit,
  type,
  step: 'any',
  placeholder,
  options: options || [],
}));
const PERFORMANCE_TELEMETRY_FIELDS = TELEMETRY_FIELDS.filter((field) => PERFORMANCE_KEYS.has(field.key) || field.key === 'MTTR (hours)');

export default function AIAssistant() {
  const [query, setQuery] = useState(EXAMPLE_QUERIES[0].query);
  const [telemetryOpen, setTelemetryOpen] = useState(false);
  const [telemetryMode, setTelemetryMode] = useState('horizontal'); // 'horizontal' | 'json'
  const [predictionMode, setPredictionMode] = useState('network_performance');
  const [telemetryData, setTelemetryData] = useState({});
  const [jsonMetrics, setJsonMetrics] = useState('');
  
  // Analysis execution states
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [flowModalOpen, setFlowModalOpen] = useState(false);
  const [expandedIncidents, setExpandedIncidents] = useState({});
  const [feedbackRating, setFeedbackRating] = useState(null);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [feedbackState, setFeedbackState] = useState('idle');

  // Count filled telemetry fields
  const activeTelemetryFields = predictionMode === 'fault_tolerance' ? TELEMETRY_FIELDS : PERFORMANCE_TELEMETRY_FIELDS;
  const filledCount = activeTelemetryFields.filter((f) => {
    const val = telemetryData[f.key];
    return val !== undefined && val !== null && String(val).trim() !== '';
  }).length;
  const isTelemetryComplete = filledCount === activeTelemetryFields.length;

  const handleFieldChange = (key, value) => {
    setTelemetryData((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleLoadSampleTelemetry = () => {
    setTelemetryData(SAMPLE_TELEMETRY);
    setTelemetryMode('horizontal');
    setJsonMetrics('');
  };

  const handleClearTelemetry = () => {
    setTelemetryData({});
    setJsonMetrics('');
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setError(null);

    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      setError('Please provide a query or description of the incident.');
      return;
    }

    // Determine network_metrics payload strictly
    let metricsPayload = null;

    if (telemetryMode === 'horizontal') {
      if (isTelemetryComplete) {
        // Construct strictly typed numbers and strings
        const formatted = {};
        activeTelemetryFields.forEach((f) => {
          const val = telemetryData[f.key];
          if (f.type === 'number') {
            formatted[f.key] = parseFloat(val);
          } else {
            formatted[f.key] = val;
          }
        });
        metricsPayload = formatted;
      } else {
        // Strict Scope rule: incomplete telemetry is never submitted as partial object
        metricsPayload = null;
      }
    } else if (telemetryMode === 'json') {
      const trimmedJson = jsonMetrics.trim();
      if (trimmedJson) {
        try {
          const parsed = JSON.parse(trimmedJson);
          if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
            throw new Error('Metrics must be a JSON object with key-value pairs.');
          }
          metricsPayload = parsed;
        } catch (jsonErr) {
          setError(`Invalid JSON metrics: ${jsonErr.message}`);
          return;
        }
      }
    }

    setIsLoading(true);
    setResult(null);
    setFeedbackRating(null);
    setFeedbackComment('');
    setFeedbackState('idle');

    try {
      const data = await analyzeQuery({
        query: trimmedQuery,
        network_metrics: metricsPayload,
        prediction_mode: predictionMode,
      });
      setResult(data);
    } catch (apiErr) {
      setError(apiErr.message || 'Analysis request failed. Ensure API is running on port 8001.');
    } finally {
      setIsLoading(false);
    }
  };

  // Helper to extract sections
  const sections = Array.isArray(result?.sections) ? result.sections : [];
  const getSection = (id) => sections.find((s) => s && s.id === id);
  const displayValue = (value, fallback = '') => {
    if (value === null || value === undefined || value === '') return fallback;
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
  };

  const histSection = getSection('historical_data');
  const predSection = getSection('prediction');
  const rcaSection = getSection('root_cause_analysis');
  const recSection = getSection('recommendations');
  const classSection = getSection('incident_prioritization');
  const impactSection = getSection('network_impact');

  // Other dynamic sections that might be returned outside the 5 standard ones
  const extraSections = sections.filter(
    (s) => s && !['historical_data', 'prediction', 'root_cause_analysis', 'recommendations'].includes(s.id)
  );

  return (
    <div className="app-container">
      {/* Page Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="page-title">
            AI Assistant
          </h1>
          {/* <p className="page-subtitle">
            Autonomous query understanding, hybrid semantic retrieval, predictive modeling, and evidence-grounded root-cause analysis.
          </p> */}
        </div>

        {/* Display Flow Button */}
        <button
          type="button"
          onClick={() => setFlowModalOpen(true)}
          className="btn btn-subtle"
          style={{ fontWeight: 600 }}
        >
          <span>🔀</span> Display Flow
        </button>
      </div>

      {/* Query Form Card */}
      <div className="card">
        <form onSubmit={handleAnalyze}>
          {/* Query Text Input */}
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label className="form-label" htmlFor="ops-query" style={{ margin: 0 }}>
                Telecom Incident Query or Operational Question
              </label>
              <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                Maximum 4,000 characters
              </span>
            </div>
            <textarea
              id="ops-query"
              className="form-textarea"
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Find winter incidents around Schneiderville where performance degraded badly..."
              required
            />
          </div>

          {/* Example Queries Strip */}
          <div style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
            <span style={{ fontSize: '11.5px', color: 'var(--color-text-muted)' }}>Presets:</span>
            {EXAMPLE_QUERIES.map((preset) => (
              <button
                key={preset.title}
                type="button"
                onClick={() => {
                  setQuery(preset.query);
                }}
                className="btn btn-secondary btn-xs"
                style={{ backgroundColor: query === preset.query ? 'var(--color-primary-subtle)' : 'transparent' }}
              >
                {preset.title}
              </button>
            ))}
          </div>

          {/* Telemetry mode */}
          <div style={{ marginBottom: '16px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="form-label">
                  Current Telemetry & Network Metrics (Optional)
                </label>
                <button
                  type="button"
                  onClick={() => setTelemetryOpen(!telemetryOpen)}
                  className="btn btn-secondary btn-xs"
                >
                  {telemetryOpen ? '▲ Collapse Telemetry Form' : `▼ Expand Telemetry Form (${activeTelemetryFields.length} Fields)`}
                </button>
              </div>
              <div className="prediction-mode-toggle" role="group" aria-label="Prediction mode" style={{ marginTop: '10px' }}>
                <button type="button" className={`btn btn-xs ${predictionMode === 'network_performance' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => { setPredictionMode('network_performance'); setResult(null); }}>Network Performance → Fault Tolerance</button>
                <button type="button" className={`btn btn-xs ${predictionMode === 'fault_tolerance' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => { setPredictionMode('fault_tolerance'); setResult(null); }}>Fault Tolerance Only</button>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                {telemetryMode === 'horizontal' ? (
                  isTelemetryComplete ? (
                    <span style={{ color: 'var(--color-accent)' }}>
                      ✅ All telemetry fields complete — metrics will be submitted to prediction models & RCA.
                    </span>
                  ) : (
                    <span style={{ color: 'var(--color-warning)' }}>
                      ⚠️ Telemetry incomplete ({filledCount}/{activeTelemetryFields.length} fields filled). Historical retrieval runs without telemetry; prediction models skipped.
                    </span>
                  )
                ) : (
                  <span>Using custom JSON metrics payload</span>
                )}
                </div>
              </div>
          </div>

          {/* Expandable Horizontal Telemetry Bar */}
          {telemetryOpen && (
            <div
              style={{
                backgroundColor: 'var(--color-input)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)',
                padding: '16px',
                marginBottom: '16px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span className={`badge ${isTelemetryComplete ? 'badge-success' : 'badge-warning'}`}>
                    {filledCount} / {activeTelemetryFields.length} fields filled
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                    {isTelemetryComplete ? 'Ready for ML inference' : `All ${activeTelemetryFields.length} selected fields are required to enable ML models`}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    onClick={handleLoadSampleTelemetry}
                    className="btn btn-secondary btn-xs"
                  >
                    Load Sample Telemetry
                  </button>
                  <button
                    type="button"
                    onClick={handleClearTelemetry}
                    className="btn btn-secondary btn-xs"
                  >
                    Clear
                  </button>
                </div>
              </div>

              {/* Complete model telemetry fields grid */}
              <div className="grid-6">
                {activeTelemetryFields.map((field) => (
                  <div key={field.key}>
                    <label style={{ fontSize: '11px', color: 'var(--color-text)', display: 'block', marginBottom: '4px' }}>
                      {field.label} {field.unit && <span style={{ color: 'var(--color-text-muted)' }}>({field.unit})</span>}
                    </label>

                    {field.type === 'select' ? (
                      <select
                        className="form-select"
                        style={{ padding: '6px 8px', fontSize: '12px' }}
                        value={telemetryData[field.key] || ''}
                        onChange={(e) => handleFieldChange(field.key, e.target.value)}
                      >
                        <option value="">Select...</option>
                        {field.options.map((opt) => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type={field.type}
                        step={field.step}
                        placeholder={field.placeholder}
                        className="form-input"
                        style={{ padding: '6px 8px', fontSize: '12px' }}
                        value={telemetryData[field.key] ?? ''}
                        onChange={(e) => handleFieldChange(field.key, e.target.value)}
                      />
                    )}
                  </div>
                ))}
              </div>

              {/* Alternate JSON mode accordion */}
              <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--color-border)' }}>
                <details style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                  <summary style={{ cursor: 'pointer', color: 'var(--color-accent)' }}>
                    Advanced: Or supply raw JSON metrics object
                  </summary>
                  <div style={{ marginTop: '8px' }}>
                    <textarea
                      rows={3}
                      className="form-textarea"
                      placeholder='{ "Latency (ms)": 142.0, "Packet Loss Rate (%)": 12.4 }'
                      value={jsonMetrics}
                      onChange={(e) => {
                        setJsonMetrics(e.target.value);
                        setTelemetryMode('json');
                      }}
                      style={{ fontSize: '11.5px', fontFamily: 'var(--font-mono)' }}
                    />
                  </div>
                </details>
              </div>
            </div>
          )}

          {/* Form Actions */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
              Target: <code style={{ color: 'var(--color-accent)' }}>POST /api/analyze</code>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary"
              style={{ minWidth: '140px' }}
            >
              {isLoading ? (
                <>
                  <span className="spinner" /> Analyzing...
                </>
              ) : (
                <>
                  <span>⚡</span> Run Analysis
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="alert alert-error">
          <span>⚠️</span>
          <div>
            <strong>Analysis Failed: </strong>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Structured Analysis Results Presentation in EXACT ORDER:
          Card 1: Analysis Summary
          Card 2: Historical Incident Matches and Evidence
          Card 3: Network Prediction Results
          Card 4: Root-Cause Analysis
          Card 5: Recommended Actions
          Followed by additional returned sections */}
      {false && result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* CARD 1: Analysis Summary */}
          <div className="card" style={{ borderColor: 'var(--color-primary)' }}>
            <div className="card-header">
              <div>
                <div className="card-title">
                  <span>📋</span> Card 1: Analysis Summary
                </div>
                <div className="card-subtitle">Synthesized analysis conclusion</div>
              </div>
              <StatusBadge
                status={result.status}
                label={result.status === 'success' ? 'Analysis Complete' : result.status}
              />
            </div>

            <div
              style={{
                fontSize: '14px',
                lineHeight: 1.6,
                color: 'var(--color-text)',
                whiteSpace: 'pre-line',
                backgroundColor: 'var(--color-input)',
                padding: '16px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)',
              }}
            >
              {displayValue(result.user_answer || result.final_answer, 'No analysis summary was returned by the orchestrator.')}
            </div>

            {result.overall_summary_source && (
              <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--color-text-muted)', display: 'flex', gap: '8px' }}>
                <span>Summary Source:</span>
                <code style={{ color: 'var(--color-accent)' }}>{result.overall_summary_source}</code>
              </div>
            )}
          </div>

          {/* Synapt advisory context */}
          {result.trace?.synapt_domain_context && (
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">Synapt Domain Context</div>
                  <div className="card-subtitle">
                    Advisory context used by query planning; historical matches remain dataset evidence.
                  </div>
                </div>
                <StatusBadge status={result.trace.synapt_domain_context.status || 'unavailable'} />
              </div>
              <div style={{ whiteSpace: 'pre-wrap', color: 'var(--color-text)', fontSize: '13px', lineHeight: 1.6 }}>
                {displayValue(result.trace.synapt_domain_context.answer, 'Synapt did not return an answer.')}
              </div>
              {result.trace.synapt_domain_context.trust_signal && (
                <div className="form-helper" style={{ marginTop: '10px' }}>
                  Trust signal: {displayValue(result.trace.synapt_domain_context.trust_signal)}
                   </div>
                  )}
             </div>
           )}

          {/* CARD 2: Historical Incident Matches and Evidence */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">
                  <span>🔍</span> Card 2: Historical Incident Matches and Evidence
                </div>
                <div className="card-subtitle">
                  Retrieved historical records from hybrid Chroma semantic + BM25 search
                </div>
              </div>
              <StatusBadge
                status={histSection?.status || 'success'}
                label={`${histSection?.data?.matching_count ?? (histSection?.data?.incidents?.length || 0)} Matches`}
              />
            </div>

            <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '14px' }}>
              Notice: These records represent statistically similar past incidents from the dataset, not necessarily the same physical network entity.
            </p>

            {(!Array.isArray(histSection?.data?.incidents) || histSection.data.incidents.length === 0) ? (
              <div className="alert alert-warning">
                <span>ℹ️</span>
                <span>No historical incident matches were found matching the query filters.</span>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {histSection.data.incidents.map((item, idx) => {
                  const safeItem = item && typeof item === 'object' ? item : {};
                  const incident = safeItem.incident && typeof safeItem.incident === 'object'
                    ? safeItem.incident
                    : safeItem;
                  const incidentId = safeItem.incident_id || incident.incident_id || `INC-${idx + 1}`;
                  const isExpanded = expandedIncidents[incidentId];

                  return (
                    <div
                      key={incidentId}
                      style={{
                        backgroundColor: 'var(--color-input)',
                        border: '1px solid var(--color-border)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '12px 14px',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          cursor: 'pointer',
                        }}
                        onClick={() =>
                          setExpandedIncidents((prev) => ({
                            ...prev,
                            [incidentId]: !prev[incidentId],
                          }))
                        }
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ fontWeight: 600, color: 'var(--color-accent)', fontFamily: 'var(--font-mono)' }}>
                            {incidentId}
                          </span>
                          {incident.issue_reported && (
                            <span className="badge badge-warning">
                              {incident.issue_reported}
                            </span>
                          )}
                          {typeof safeItem.score === 'number' && (
                            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                              Relevance: {(safeItem.score * 100).toFixed(1)}%
                            </span>
                          )}
                        </div>

                        <span style={{ fontSize: '11.5px', color: 'var(--color-text-muted)' }}>
                          {isExpanded ? '▲ Collapse Evidence' : '▼ Expand Evidence'}
                        </span>
                      </div>

                      {/* Brief metric preview */}
                      <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', marginTop: '6px', fontSize: '12px' }}>
                        {incident.latency_ms !== undefined && (
                          <span>Latency: <strong style={{ color: 'var(--color-text)' }}>{incident.latency_ms} ms</strong></span>
                        )}
                        {incident.packet_loss_rate !== undefined && (
                          <span>Packet Loss: <strong style={{ color: 'var(--color-text)' }}>{incident.packet_loss_rate}%</strong></span>
                        )}
                        {incident.throughput_mbps !== undefined && (
                          <span>Throughput: <strong style={{ color: 'var(--color-text)' }}>{incident.throughput_mbps} Mbps</strong></span>
                        )}
                        {incident.season && (
                          <span style={{ color: 'var(--color-text-muted)' }}>Season: {incident.season}</span>
                        )}
                      </div>

                      {/* Expandable Evidence Details */}
                      {isExpanded && (
                        <div
                          style={{
                            marginTop: '12px',
                            paddingTop: '10px',
                            borderTop: '1px solid var(--color-border)',
                            fontSize: '12px',
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                            gap: '8px',
                          }}
                        >
                          {Object.entries(incident).map(([k, v]) => (
                            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0' }}>
                              <span style={{ color: 'var(--color-text-muted)' }}>{k}:</span>
                              <span style={{ color: 'var(--color-text)', fontFamily: 'var(--font-mono)' }}>
                                {String(v)}
                              </span>
                            </div>
                           ))}
                </div>
                )}
                     </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* CARD 3: Network Prediction Results */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">
                  <span>⚡</span> Card 3: Network Prediction Results
                </div>
                <div className="card-subtitle">
                  Machine learning model estimates (distinct from observed measurements)
                </div>
              </div>
              <StatusBadge status={predSection?.status || 'not_applicable'} />
            </div>

            {predSection?.status === 'not_applicable' || !predSection?.data?.prediction ? (
              <div className="alert alert-info">
                <span>ℹ️</span>
                <div>
                  <strong>Predictions Not Executed: </strong>
                  <span>{displayValue(predSection?.summary, 'Network predictions require complete telemetry input. Supply all model telemetry fields to activate prediction models.')}</span>
                </div>
              </div>
            ) : (
              <div className="grid-2">
                {/* Model 1: Throughput Prediction Result */}
                {predSection.data.prediction.network_performance && (
                  <div style={{ backgroundColor: 'var(--color-input)', padding: '16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                      Model 1: Network Throughput
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-accent)', margin: '8px 0' }}>
                      {predSection.data.prediction.network_performance.predicted_throughput_mbps !== undefined
                        ? `${predSection.data.prediction.network_performance.predicted_throughput_mbps} Mbps`
                        : 'Unavailable'}
                    </div>
                    <div style={{ fontSize: '11.5px', color: 'var(--color-text-muted)' }}>
                       Target: Throughput (Mbps) | Algorithm: XGBoost Regressor
                    </div>
                     {predSection.data.prediction.network_performance.classification && <div style={{ marginTop: '10px', fontSize: '12px' }}><strong>Performance status: </strong>{predSection.data.prediction.network_performance.classification.overall_risk || 'Incomplete'}{predSection.data.prediction.network_performance.classification.performance_score !== null && predSection.data.prediction.network_performance.classification.performance_score !== undefined && <span> · Score {predSection.data.prediction.network_performance.classification.performance_score}/100</span>}</div>}
                  </div>
                )}

                {/* Model 2: Fault Occurrence Rate Result */}
                {predSection.data.prediction.fault_risk && (
                  <div style={{ backgroundColor: 'var(--color-input)', padding: '16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                      Model 2: Fault Occurrence Rate
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-warning)', margin: '8px 0' }}>
                      {predSection.data.prediction.fault_risk.predicted_fault_occurrence_rate_percent !== undefined
                        ? `${predSection.data.prediction.fault_risk.predicted_fault_occurrence_rate_percent}%`
                        : 'Unavailable'}
                    </div>
                    <div style={{ fontSize: '11.5px', color: 'var(--color-text-muted)' }}>
                      Target: Fault Occurrence Rate (%) | Risk Tier: {predSection.data.prediction.fault_risk.fault_risk || 'Evaluated'}
                    </div>
                  </div>
                 )}
               </div>
             )}
           </div>
           {predSection?.data?.prediction && <ModelAgreementCard prediction={predSection.data.prediction} />}

           {/* CARD 4: Root-Cause Analysis */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">
                  <span>🔬</span> Card 4: Root-Cause Analysis
                </div>
                <div className="card-subtitle">
                  Ranked investigative hypotheses (evidence-based, not confirmed physical causes)
                </div>
              </div>
              <StatusBadge status={rcaSection?.status || 'not_applicable'} />
            </div>

            <div style={{ backgroundColor: 'var(--color-input)', padding: '14px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)', marginBottom: '12px' }}>
              <div style={{ fontSize: '13.5px', color: 'var(--color-text)', lineHeight: 1.5 }}>
                {displayValue(rcaSection?.summary, 'Root-cause analysis was not available for this query.')}
              </div>
            </div>

            {/* Hypotheses details if returned */}
            {rcaSection?.data?.hypotheses && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {Array.isArray(rcaSection.data.hypotheses) && rcaSection.data.hypotheses.map((hyp, i) => (
                  <div key={i} style={{ padding: '8px 12px', borderLeft: '3px solid var(--color-primary)', backgroundColor: 'rgba(0, 124, 124, 0.05)', fontSize: '12.5px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <strong style={{ color: 'var(--color-text)' }}>Rank {hyp.rank || i + 1}: {displayValue(hyp.hypothesis || hyp.name, 'Unnamed hypothesis')}</strong>
                      {hyp.score !== undefined && (
                        <span style={{ color: 'var(--color-accent)', fontFamily: 'var(--font-mono)' }}>
                          Score: {hyp.score}
                        </span>
                      )}
                    </div>
                    {hyp.evidence && (
                      <p style={{ fontSize: '11.5px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                        Evidence: {displayValue(hyp.evidence)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* CARD 5: Recommended Actions */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">
                  <span>🛠️</span> Card 5: Recommended Actions
                </div>
                <div className="card-subtitle">
                  Standard Operating Procedures (SOPs) retrieved via Synapt
                </div>
              </div>
              <StatusBadge
                status={recSection?.status || 'not_requested'}
                label={recSection?.status === 'not_requested' ? 'Not Requested' : recSection?.status}
              />
            </div>

            <div style={{ backgroundColor: 'var(--color-input)', padding: '14px 16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)', marginBottom: '12px' }}>
              <div style={{ fontSize: '13.5px', color: 'var(--color-text)', lineHeight: 1.5 }}>
                {displayValue(recSection?.summary, 'No recommendations requested or available.')}
              </div>
            </div>

            {Array.isArray(recSection?.data?.recommendations) && recSection.data.recommendations.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '12px' }}>
                {recSection.data.recommendations.map((item, idx) => (
                  <div key={idx} style={{ padding: '10px 12px', backgroundColor: 'var(--color-input)', borderRadius: '4px', border: '1px solid var(--color-border)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 600, color: 'var(--color-accent)', fontSize: '12.5px' }}>
                        Step {idx + 1}: {displayValue(item.procedure_name || item.procedure_id, 'Operational Procedure')}
                      </span>
                    </div>
                    <p style={{ fontSize: '12px', color: 'var(--color-text)' }}>
                      {displayValue(item.action)}
                    </p>
                  </div>
                ))}
              </div>
            )}

            <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
              Notice: SOP guidance represents synthetic prototype procedures and domain guidelines. Always verify against authorized operational runbooks before execution.
            </div>
          </div>

          {/* ADDITIONAL RETURNED SECTIONS */}
          {classSection && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <span>🏷️</span> Incident Classification and Prioritization
                </div>
                <StatusBadge status={classSection.status} />
              </div>
              <div style={{ fontSize: '13px', color: 'var(--color-text)', lineHeight: 1.5 }}>
                {displayValue(classSection.summary)}
              </div>
            </div>
          )}

          {impactSection && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <span>⚠️</span> Network Impact Assessment
                </div>
                <StatusBadge status={impactSection.status} />
              </div>
              <div style={{ fontSize: '13px', color: 'var(--color-text)', lineHeight: 1.5 }}>
                {displayValue(impactSection.summary)}
              </div>
            </div>
          )}

        </div>
      )}

      {result && <AnalysisResults result={result} />}

      {result && result.response_id && (
        <div className="card feedback-card">
          <div className="card-title">Was this answer useful?</div>
          <div className="feedback-actions">
            <button type="button" className={`btn btn-secondary btn-xs ${feedbackRating === 'helpful' ? 'feedback-selected' : ''}`} disabled={feedbackState === 'submitted'} onClick={() => setFeedbackRating('helpful')}>Helpful</button>
            <button type="button" className={`btn btn-secondary btn-xs ${feedbackRating === 'not_helpful' ? 'feedback-selected' : ''}`} disabled={feedbackState === 'submitted'} onClick={() => setFeedbackRating('not_helpful')}>Not helpful</button>
          </div>
          {feedbackRating && feedbackState !== 'submitted' && <>
            <textarea className="feedback-comment" value={feedbackComment} onChange={(event) => setFeedbackComment(event.target.value)} placeholder="Optional comment" maxLength={4000} />
            <button type="button" className="btn btn-primary btn-xs" disabled={feedbackState === 'submitting'} onClick={async () => { setFeedbackState('submitting'); try { await submitFeedback({ response_id: result.response_id, query: result.query || query, final_response: result.user_answer || result.final_answer || '', rating: feedbackRating, comment: feedbackComment, context: { sections: result.sections, trace: { execution_statuses: result.trace?.execution_statuses, fallback_report: result.trace?.fallback_report } } }); setFeedbackState('submitted'); } catch (feedbackError) { setFeedbackState(`error:${feedbackError.message}`); } }}>Submit Feedback</button>
          </>}
          {feedbackState === 'submitted' && <div className="form-helper">Feedback saved for quality evaluation.</div>}
          {feedbackState.startsWith('error:') && <div className="form-helper">{feedbackState.slice(6)}</div>}
        </div>
      )}

      {/* Agent Workflow Visualization Modal */}
      <AgentFlow
        isOpen={flowModalOpen}
        onClose={() => setFlowModalOpen(false)}
        analysisResult={result}
      />
    </div>
  );
}
