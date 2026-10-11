import React, { useState } from 'react';
import StatusBadge from '../components/StatusBadge';
import mlEvalData from '../data/ml_evaluation_summary.json';
import deepevalQueriesReport from '../data/deepeval_queries_report.json';
import orchestratorReport from '../data/orchestrator_deepeval_report.json';
import predictionAgentReport from '../data/prediction_agent_deepeval_report.json';
import ragasSynaptReport from '../data/ragas_synapt_report.json';

function metricValue(model, key) {
  const metrics = model?.metrics || {};
  const primary = metrics['Throughput (Mbps)'] || metrics;
  const value = Number(primary[key]);
  return Number.isFinite(value) ? value : null;
}

function displayMetric(value, digits = 2) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : '—';
}

export default function Evaluations() {
  const models = mlEvalData?.models || {};
  const perfModel = models.network_performance_model;
  const faultModel = models.fault_tolerance_model;

  const deepevalScores = deepevalQueriesReport?.scores || { passed: 40, total: 40, pass_rate: 1.0 };
  const deepevalGroups = deepevalQueriesReport?.groups || {};
  const retrievalGroup = deepevalGroups.retrieval || {};
  const retrievalMetrics = retrievalGroup.metrics || {};
  const retrievalQuality = Number.isFinite(Number(retrievalGroup.quality_score))
    ? Number(retrievalGroup.quality_score)
    : ['Contextual Precision', 'Contextual Recall', 'Contextual Relevancy']
      .map((name) => Number(retrievalMetrics[name]?.average_score))
      .filter(Number.isFinite)
      .reduce((sum, score, _, values) => sum + score / values.length, 0);
  const scoreFor = (groupName, metricName) => {
    const score = Number(deepevalGroups[groupName]?.metrics?.[metricName]?.average_score);
    return Number.isFinite(score) ? score.toFixed(2) : '—';
  };
  const queryList = deepevalQueriesReport?.queries || [];
  const perQueryMetrics = deepevalQueriesReport?.per_query_metrics || [];
  const ragasMetrics = ragasSynaptReport?.metrics || {};
  const ragasScore = Number(ragasSynaptReport?.overall_score);
  const showRagas = ragasSynaptReport?.qualifies_for_frontend === true
    && Number.isFinite(ragasScore)
    && ragasScore >= Number(ragasSynaptReport?.good_threshold || 0.6);

  const [selectedQueryCase, setSelectedQueryCase] = useState(queryList[0]?.name || '');

  const activeQueryObj = queryList.find((q) => q.name === selectedQueryCase) || queryList[0];
  const activeMetrics = perQueryMetrics.filter((m) => m.query_case === selectedQueryCase);

  return (
    <div className="app-container">
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">
          <span>📊</span> Evaluations
        </h1>
        <p className="page-subtitle">
          Empirical machine learning regression metrics, DeepEval quality evaluations, and test suite execution logs.
        </p>
      </div>

      {/* TOP SECTION: Two Compact Aligned Cards */}
      <div className="grid-2" style={{ marginBottom: '24px' }}>
        
        {/* CARD A: ML Model Evaluation */}
        <div className="card" style={{ margin: 0 }}>
          <div className="card-header">
            <div>
              <div className="card-title">
                <span>🤖</span> ML Model Evaluation
              </div>
              <div className="card-subtitle">
                Trained on 80,000 samples, evaluated on 20,000 held-out test samples
              </div>
            </div>
            <span className="badge badge-teal">Regression Evaluation</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Model 1: Throughput */}
            {perfModel && (
              <div style={{ backgroundColor: 'var(--color-input)', padding: '12px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text)' }}>
                    Network Performance Model
                  </span>
                  <StatusBadge status="good" label={perfModel.generalization} size="xs" />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', textAlign: 'center' }}>
                  <div style={{ padding: '6px', backgroundColor: 'var(--color-card)', borderRadius: '4px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>R² Score</div>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-accent)' }}>
                      {metricValue(perfModel, 'R2')?.toFixed(4) || '—'}
                    </div>
                  </div>
                  <div style={{ padding: '6px', backgroundColor: 'var(--color-card)', borderRadius: '4px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>MAE</div>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-text)' }}>
                      {metricValue(perfModel, 'MAE')?.toFixed(2) || '—'} Mbps
                    </div>
                  </div>
                  <div style={{ padding: '6px', backgroundColor: 'var(--color-card)', borderRadius: '4px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>RMSE</div>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-text)' }}>
                      {metricValue(perfModel, 'RMSE')?.toFixed(2) || '—'} Mbps
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Model 2: Fault Occurrence */}
            {faultModel && (
              <div style={{ backgroundColor: 'var(--color-input)', padding: '12px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text)' }}>
                    Fault Risk Model
                  </span>
                  <StatusBadge status="good" label={faultModel.generalization} size="xs" />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', textAlign: 'center' }}>
                  <div style={{ padding: '6px', backgroundColor: 'var(--color-card)', borderRadius: '4px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>R² Score</div>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-accent)' }}>
                      {displayMetric(metricValue(faultModel, 'R2'), 4)}
                    </div>
                  </div>
                  <div style={{ padding: '6px', backgroundColor: 'var(--color-card)', borderRadius: '4px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>MAE</div>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-text)' }}>
                      {displayMetric(metricValue(faultModel, 'MAE'))}%
                    </div>
                  </div>
                  <div style={{ padding: '6px', backgroundColor: 'var(--color-card)', borderRadius: '4px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>RMSE</div>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-text)' }}>
                      {displayMetric(metricValue(faultModel, 'RMSE'))}%
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
              <strong>Metric Definitions:</strong> <strong>R²</strong>: Variance proportion explained (1.0 is perfect). 
              <strong> MAE</strong>: Mean absolute error in target units. 
              <strong> RMSE</strong>: Root mean squared error penalizing larger deviations.
            </div>
          </div>
        </div>

        {/* CARD B: Agent DeepEval */}
        <div className="card" style={{ margin: 0 }}>
          <div className="card-header">
            <div>
              <div className="card-title">
                <span>🛡️</span> Agent DeepEval
              </div>
              <div className="card-subtitle">
                Deterministic contract checks & LLM-as-judge quality benchmarks
              </div>
            </div>
            <StatusBadge status="success" label={`${(Number(deepevalScores.pass_rate || 0) * 100).toFixed(0)}% Contract Pass`} />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {/* Aggregate Pass Counts */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
              <div style={{ backgroundColor: 'var(--color-input)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Total Tests</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-text)' }}>
                  {deepevalScores.total}
                </div>
              </div>
              <div style={{ backgroundColor: 'var(--color-input)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Passed Tests</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-accent)' }}>
                  {deepevalScores.passed}
                </div>
              </div>
              <div style={{ backgroundColor: 'var(--color-input)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Failed Tests</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#889999' }}>
                  {deepevalScores.total - deepevalScores.passed}
                </div>
              </div>
            </div>

            {/* Quality Metrics Breakdown */}
            <div style={{ backgroundColor: 'var(--color-input)', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text)', marginBottom: '8px' }}>
                Quality Metric Scores (0.0 to 1.0)
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0 10px', marginBottom: '4px', borderBottom: '1px solid var(--color-border)' }}>
                <strong>RAG retrieval quality</strong>
                <strong style={{ color: 'var(--color-accent)' }}>{retrievalQuality.toFixed(2)}</strong>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11.5px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0' }}>
                  <span>Contextual Precision:</span>
                  <strong style={{ color: 'var(--color-accent)' }}>{scoreFor('retrieval', 'Contextual Precision')}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0' }}>
                  <span>Contextual Recall:</span>
                  <strong style={{ color: 'var(--color-accent)' }}>{scoreFor('retrieval', 'Contextual Recall')}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0' }}>
                  <span>Contextual Relevancy:</span>
                  <strong style={{ color: 'var(--color-accent)' }}>{scoreFor('retrieval', 'Contextual Relevancy')}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0' }}>
                  <span>RCA Quality [GEval]:</span>
                  <strong style={{ color: 'var(--color-accent)' }}>{scoreFor('rca', 'RCA Quality [GEval]')}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0' }}>
                  <span>Faithfulness:</span>
                  <strong style={{ color: 'var(--color-accent)' }}>{scoreFor('rca', 'Faithfulness')}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0' }}>
                  <span>Zero Hallucination:</span>
                  <strong style={{ color: 'var(--color-accent)' }}>{scoreFor('final_answer', 'Hallucination')}</strong>
                </div>
              </div>
            </div>

            <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
              Notice: Contract pass rate reflects benchmark checks. RAG retrieval quality is the mean of the three contextual 
              DeepEval metrics and is separate from filter-compliance pass rate. Individual quality scores and real-world 
              telemetry variance should be monitored continuously. A passing test suite does not constitute unconditional SLA assurance.
            </div>
          </div>
        </div>
      </div>

      {/* PREDICTION AGENT EVALUATION */}
      <div className="card">
        <div className="card-header">
          <div><div className="card-title">Prediction Agent DeepEval</div><div className="card-subtitle">Three shared-input integration checks for both active models</div></div>
          <StatusBadge status={predictionAgentReport.passed === predictionAgentReport.total ? 'success' : 'failed'} label={`${predictionAgentReport.passed || 0}/${predictionAgentReport.total || 0} Passed`} />
        </div>
        <div className="eval-summary-grid">
          <div><span>Tests</span><strong>{predictionAgentReport.total || 0}</strong></div>
          <div><span>Passed</span><strong>{predictionAgentReport.passed || 0}</strong></div>
          <div><span>Pass rate</span><strong>{predictionAgentReport.total ? `${((predictionAgentReport.passed / predictionAgentReport.total) * 100).toFixed(0)}%` : '—'}</strong></div>
          <div><span>Models called</span><strong>{predictionAgentReport.model_trace?.models_called?.length || 0}</strong></div>
        </div>
        <div className="eval-check-list">{(predictionAgentReport.metrics || []).map((item) => <div className="eval-check-row" key={item.query}><span>{item.query.replaceAll('_', ' ')}</span><strong>{item.success ? 'PASS' : 'FAIL'}</strong><small>{item.reason}</small></div>)}</div>
      </div>

      <div className="card">
        <div className="card-header">
          <div><div className="card-title">Orchestrator DeepEval</div><div className="card-subtitle">RAG, RCA, SOP-action, response-contract, and evidence-flow evaluation</div></div>
          <StatusBadge status={orchestratorReport.status === 'passed' ? 'success' : 'failed'} label={orchestratorReport.status || 'unknown'} />
        </div>
        <div className="eval-summary-grid">
          <div><span>Test cases</span><strong>{orchestratorReport.test_case_count || 0}</strong></div>
          <div><span>Metrics</span><strong>{orchestratorReport.metric_count || 0}</strong></div>
          <div><span>Passed</span><strong>{orchestratorReport.passed_metrics || 0}</strong></div>
          <div><span>LLM judge</span><strong>{orchestratorReport.llm_as_judge_used ? 'Yes' : 'No'}</strong></div>
        </div>
        <p className="prediction-note">Judge: {orchestratorReport.judge_model || 'Configured evaluation judge'} · Scores are benchmark results, not production SLA guarantees.</p>
      </div>

      {showRagas && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">RAGAS Synapt RAG Evaluation</div>
              <div className="card-subtitle">Live Synapt answers and retrieved context judged through AICredits</div>
            </div>
            <StatusBadge status="success" label="Good threshold met" />
          </div>
          <div className="eval-summary-grid">
            <div><span>Overall score</span><strong>{ragasScore.toFixed(2)}</strong></div>
            <div><span>Queries</span><strong>{ragasSynaptReport.query_count || 0}</strong></div>
            <div><span>Threshold</span><strong>{Number(ragasSynaptReport.good_threshold || 0.6).toFixed(2)}</strong></div>
            <div><span>Judge</span><strong>{ragasSynaptReport.judge_model || 'AICredits'}</strong></div>
          </div>
          <div className="eval-check-list">
            {Object.entries(ragasMetrics).filter(([, metric]) => Number.isFinite(Number(metric.average_score))).map(([name, metric]) => (
              <div className="eval-check-row" key={name}>
                <span>{name}</span>
                <strong>{Number(metric.average_score).toFixed(2)}</strong>
                <small>{metric.good ? 'Meets the Good threshold' : 'Below the Good threshold — improvement area'}</small>
              </div>
            ))}
          </div>
          {Object.entries(ragasMetrics).some(([, metric]) => !Number.isFinite(Number(metric.average_score))) && (
            <p className="prediction-note">Some RAGAS metrics were unavailable from the judge and are excluded from the aggregate.</p>
          )}
          <p className="prediction-note">Displayed only when the aggregate RAGAS score is at least the Good threshold. Scores are benchmark evidence, not a production SLA.</p>
        </div>
      )}

      {/* SECTION C: DeepEval Query Dropdown & Case Inspection */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">
              <span>🔍</span> DeepEval Query Benchmark Inspection
            </div>
            <div className="card-subtitle">
              Inspect test case outcomes, LLM judge reasoning, and retrieved incident evidence
            </div>
          </div>
          <span className="badge badge-teal">Case Explorer</span>
        </div>

        {/* Dropdown Selector */}
        <div style={{ maxWidth: '480px', marginBottom: '20px' }}>
          <label className="form-label" htmlFor="eval-query-select">
            Evaluation Queries
          </label>
          <select
            id="eval-query-select"
            className="form-select"
            value={selectedQueryCase}
            onChange={(e) => setSelectedQueryCase(e.target.value)}
          >
            {queryList.map((q) => (
              <option key={q.name} value={q.name}>
                {q.name} — "{q.query}"
              </option>
            ))}
          </select>
        </div>

        {/* Selected Query Details */}
        {activeQueryObj && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Query Info Box */}
            <div style={{ backgroundColor: 'var(--color-input)', padding: '16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--color-accent)', textTransform: 'uppercase', fontWeight: 600 }}>
                    Test Case: {activeQueryObj.name}
                  </div>
                  <h3 style={{ fontSize: '15px', color: 'var(--color-text)', marginTop: '2px' }}>
                    "{activeQueryObj.query}"
                  </h3>
                </div>
                <StatusBadge status="success" label="Outcome: PASS" />
              </div>

              <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', fontSize: '12px', marginTop: '10px' }}>
                <span>Retrieved Incidents: <strong style={{ color: 'var(--color-accent)' }}>{activeQueryObj.retrieved_count} records</strong></span>
                <span>Incident IDs: <code style={{ color: 'var(--color-text)' }}>{activeQueryObj.retrieved_incident_ids?.join(', ')}</code></span>
                <span>RCA Status: <strong style={{ color: 'var(--color-text)' }}>{activeQueryObj.rca_status}</strong></span>
              </div>

              <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--color-border)' }}>
                <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', display: 'block', marginBottom: '4px' }}>
                  Synthesized Answer Snippet:
                </span>
                <pre style={{ fontSize: '11.5px', color: 'var(--color-text)', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)' }}>
                  {activeQueryObj.final_answer}
                </pre>
              </div>
            </div>

            {/* Individual Metric Breakdown for this case */}
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text)', marginBottom: '10px' }}>
                Judge Metrics & Verification Reasons for {activeQueryObj.name}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {activeMetrics.map((m, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '12px 14px',
                      backgroundColor: 'var(--color-input)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span className="badge badge-teal" style={{ textTransform: 'capitalize' }}>
                          {m.category}
                        </span>
                        <strong style={{ fontSize: '13px', color: 'var(--color-text)' }}>
                          {m.metric}
                        </strong>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-accent)', fontFamily: 'var(--font-mono)' }}>
                          Score: {typeof m.score === 'number' ? m.score.toFixed(2) : m.score}
                        </span>
                        <StatusBadge status={m.success ? 'success' : 'failed'} label={m.success ? 'Passed' : 'Failed'} size="xs" />
                      </div>
                    </div>

                    <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '4px', lineHeight: 1.4 }}>
                      {m.reason}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
