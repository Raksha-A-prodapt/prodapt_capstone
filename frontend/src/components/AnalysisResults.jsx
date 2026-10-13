import React, { useState } from 'react';
import StatusBadge from './StatusBadge';
import ModelAgreementCard from './ModelAgreementCard';

const value = (v, fallback = 'Not available') => {
  if (v === null || v === undefined || v === '') return fallback;
  if (typeof v === 'object') return JSON.stringify(v);
  return String(v);
};
const number = (v, digits = 2) => (typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: digits }) : value(v));

function cleanSummary(text) {
  return String(text || 'No final summary was returned.')
    .replace(/^\s*Answer\s*:?\s*/i, '')
    .replace(/\n?\s*(?:Recommendations|Recommended Actions)\s*:?\s*(?:\n\s*)?No recommendations (?:are )?available\.?\s*/gi, '\n')
    .trim();
}

const ANSWER_SECTION_HEADINGS = [
  'Answer',
  'RCA',
  'Recommended Actions',
  'Filtered Historical Evaluation',
  'Network Predictions',
  'Root-Cause Analysis',
  'Historical Incident Matches',
  'Recommendations',
  'Incident Classification and Prioritization',
  'Network Impact Assessment',
];

function splitAnswerSections(text) {
  const source = String(text || '').replace(/\r/g, '').trim();
  if (!source) return [];
  const headingPattern = ANSWER_SECTION_HEADINGS
    .map((heading) => heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .join('|');
  const matcher = new RegExp(`(?:^|\\n)(${headingPattern})\\s*\\n`, 'g');
  const matches = [...source.matchAll(matcher)];
  if (!matches.length) return [{ title: 'Answer', body: source }];
  return matches.map((match, index) => ({
    title: match[1] === 'Root-Cause Analysis' || match[1] === 'RCA' ? 'RCA' : match[1] === 'Recommendations' || match[1] === 'Recommended Actions' ? 'Recommended Actions' : match[1],
    body: source.slice(match.index + match[0].length, matches[index + 1]?.index || source.length).trim(),
  })).filter((section) => section.body);
}

function SummaryText({ text }) {
  const paragraphs = cleanSummary(text).split(/\n\s*\n|\n(?=[A-Za-z][A-Za-z /&-]{2,40}:)/).filter(Boolean);
  return <div className="summary-copy">{paragraphs.map((paragraph, index) => {
    const lines = paragraph.split('\n').map((line) => line.trim()).filter(Boolean);
    const isList = lines.length > 1 && lines.every((line) => /^[-*•]\s+/.test(line));
    if (isList) return <ul key={index}>{lines.map((line) => <li key={line}>{line.replace(/^[-*•]\s+/, '')}</li>)}</ul>;
    const highlightedHeading = paragraph.match(/^(Answer|RCA|Recommended Actions)\s*:?[ \t]*(.*)$/is);
    if (highlightedHeading) return <p key={index}><strong>{highlightedHeading[1]}</strong>{highlightedHeading[2] ? <>: {highlightedHeading[2]}</> : null}</p>;
    const match = paragraph.match(/^([^:\n]{2,60}):\s*([\s\S]*)$/);
    return <p key={index}>{match ? <><strong>{match[1]}:</strong> {match[2]}</> : paragraph}</p>;
  })}</div>;
}

function Metric({ label, value: metricValue, unit }) {
  return <div className="analysis-metric"><span>{label}</span><strong>{number(metricValue)}{metricValue !== undefined && metricValue !== null ? ` ${unit || ''}` : ''}</strong></div>;
}

function Bar({ score }) {
  const width = Math.max(0, Math.min(100, Number(score || 0) * 100));
  return <div style={{ height: 7, background: 'var(--color-border)', borderRadius: 4, overflow: 'hidden', marginTop: 7 }}><div style={{ width: `${width}%`, height: '100%', background: 'var(--color-primary)' }} /></div>;
}

function PredictionSummary({ prediction, mode }) {
  const performance = prediction?.network_performance;
  const fault = prediction?.fault_risk;
  const classification = performance?.classification;
  const faultOnly = mode === 'fault_tolerance';
  if (prediction?.status === 'historical_baseline') {
    const metrics = prediction.baseline_metrics || performance?.average_metrics || {};
    const labels = [
      ['throughput_mbps', 'Average throughput', 'Mbps'],
      ['latency_ms', 'Average latency', 'ms'],
      ['packet_loss_rate', 'Average packet loss', '%'],
      ['call_drop_rate', 'Average call-drop rate', '%'],
      ['handover_success_rate', 'Average handover success', '%'],
      ['fault_occurrence_rate', 'Average fault occurrence', '%'],
    ];
    return <>
      <div className="answer-prediction-grid">{labels.filter(([key]) => metrics[key] !== undefined && metrics[key] !== null).map(([key, label, unit]) => <div className="answer-prediction-tile" key={key}><span>{label}</span><strong>{number(metrics[key])} {unit}</strong></div>)}</div>
      <p className="muted">Historical baseline from {prediction.record_count || 0} filtered incident(s). No live telemetry was supplied, so prediction models were not run. Validate these averages against current measurements.</p>
    </>;
  }
  return <div className="answer-prediction-grid">
    {!faultOnly && <div className="answer-prediction-tile"><span>Network status</span><strong>{classification?.overall_risk || 'Unavailable'}</strong>{classification?.performance_score !== null && classification?.performance_score !== undefined && <small>Score {classification.performance_score}/100</small>}</div>}
    <div className="answer-prediction-tile"><span>Fault risk</span><strong>{fault?.fault_risk || 'Unavailable'}</strong>{fault?.predicted_fault_occurrence_rate_percent !== undefined && <small>{fault.predicted_fault_occurrence_rate_percent}% predicted rate</small>}{fault?.missing_features?.length > 0 && <small>Missing: {fault.missing_features.join(', ')}</small>}</div>
    {!faultOnly && <div className="answer-kpi-strip"><span>KPI classification</span><strong>{classification?.overall_risk || 'Unavailable'}</strong></div>}
  </div>;
}

export default function AnalysisResults({ result }) {
  const [expanded, setExpanded] = useState({});
  const sections = Array.isArray(result?.sections) ? result.sections : [];
  const section = (id) => sections.find((item) => item?.id === id);
  const historical = section('historical_data');
  const rca = section('root_cause_analysis');
  const recommendations = section('recommendations');
  const classification = section('incident_prioritization');
  const impact = section('network_impact');
  const historicalEvaluation = section('historical_evaluation');
  const prediction = section('prediction');
  const incidents = Array.isArray(historical?.data?.incidents) ? historical.data.incidents.slice(0, 15) : [];
  const [showAllIncidents, setShowAllIncidents] = useState(false);
  const hypotheses = Array.isArray(rca?.data?.hypotheses) ? rca.data.hypotheses : [];
  const actions = Array.isArray(recommendations?.data?.recommendations) ? recommendations.data.recommendations : [];
  const procedures = Array.isArray(recommendations?.data?.procedures) ? recommendations.data.procedures : [];
  const diagnosticChecks = [...new Set(procedures.flatMap((procedure) => Array.isArray(procedure?.diagnostic_checks) ? procedure.diagnostic_checks : []))]
    .filter((check) => typeof check === 'string' && check.trim())
    .map((check) => check.trim())
    .slice(0, 7);
  const top = hypotheses[0];
  const toggle = (key) => setExpanded((old) => ({ ...old, [key]: !old[key] }));
  const predictionData = prediction?.data || {};
  const predictionPayload = predictionData.prediction || predictionData;
  const predictionAvailable = Boolean(predictionData?.status === 'historical_baseline' || (predictionPayload && Object.values(predictionPayload).some((item) => item?.status === 'success' || item?.predictions || item?.predicted_fault_occurrence_rate_percent !== undefined)));
  const finding = top
    ? `Historical analysis of ${incidents.length} similar incident${incidents.length === 1 ? '' : 's'} points to ${value(top.hypothesis || top.name, 'the leading hypothesis').toLowerCase()} as the main investigation focus. ${predictionData.status === 'historical_baseline' ? 'Current telemetry was not provided; historical averages are shown as a baseline, not a live prediction.' : predictionAvailable ? 'Current telemetry was available for model prediction.' : 'No current metrics were provided, so live validation and predictions were not available.'}`
    : (incidents.length ? `Historical analysis returned ${incidents.length} similar incident${incidents.length === 1 ? '' : 's'}. Validate the observed pattern with live network measurements.` : 'No historical evidence was returned for this query.');
  const counts = classification?.data?.historical_examples?.priority_counts || classification?.data?.priority_counts || {};
  const maxCount = Math.max(1, ...['P1', 'P2', 'P3', 'P4'].map((key) => Number(counts[key] || 0)));
  const totalPrioritized = ['P1', 'P2', 'P3', 'P4'].reduce((sum, key) => sum + Number(counts[key] || 0), 0);
  const currentScenario = classification?.data?.current_scenario || classification?.data?.scenario_classification;
  const priorityGroups = classification?.data?.historical_examples?.incidents || [];
  const priorityIds = ['P1', 'P2', 'P3', 'P4'].reduce((groups, priority) => {
    groups[priority] = priorityGroups.filter((item) => item?.priority === priority && item?.incident_id).map((item) => item.incident_id);
    return groups;
  }, {});
  const execution = result?.trace?.execution_statuses || {};
  const fallbackReport = result?.trace?.fallback_report || {};
  const summarySource = result?.overall_summary_source || (result?.overall_summary_status === 'success' ? 'LLM' : 'Deterministic fallback');
  const historicalBaseline = predictionData.status === 'historical_baseline';
  const summaryText = result?.overall_summary || result?.user_answer || result?.final_answer;
  const answerSections = splitAnswerSections(result?.final_answer);
  const answerBody = answerSections.find((section) => section.title === 'Answer')?.body || summaryText;

  return <div className="analysis-results">
    <section className="card analysis-card llm-summary-card">
      <div className="card-header"><div><div className="card-title">LLM Analysis Summary</div><div className="card-subtitle">Final answer synthesized from retrieved evidence and agent outputs</div></div><span className={`badge ${result?.overall_summary_status === 'success' ? 'badge-success' : 'badge-warning'}`}>{summarySource}</span></div>
      <div className="llm-summary-text"><div className="summary-answer"><div className="summary-section-title">Answer</div><SummaryText text={answerBody} /></div>
        {(answerSections.filter((section) => section.title !== 'Answer' && section.title !== 'RCA' && section.title !== 'Recommendations' && section.title !== 'Recommended Actions').length > 0 || procedures.length > 0) && <div className="summary-section-lines">
          {answerSections.filter((section) => section.title !== 'Answer' && section.title !== 'RCA' && section.title !== 'Recommendations' && section.title !== 'Recommended Actions').map((section) => <div className="summary-section-line" key={section.title}><div className="summary-section-title">{section.title}</div><SummaryText text={section.body} /></div>)}
          {procedures.length > 0 && <div className="summary-section-line"><div className="summary-section-title">Recommended Actions</div><SummaryText text={`Follow the relevant Synapt SOP procedures: ${procedures.map((procedure) => value(procedure.name || procedure.title || procedure.sop_id || procedure.procedure_id, 'network investigation')).join(', ')}.`} /></div>}
        </div>}
      </div>
      <div className="analysis-tags" aria-label="Analysis stages">
        <StatusBadge status="success" label="Answer" />
        <StatusBadge status={rca?.status || 'not_applicable'} label="RCA" />
        <StatusBadge status={historicalEvaluation?.status || 'not_applicable'} label="Filtered Historical Evaluation" />
        <StatusBadge status={historicalBaseline ? 'fallback' : predictionAvailable ? 'success' : 'not_applicable'} label={historicalBaseline ? 'Network Predictions · Historical Baseline' : 'Network Predictions'} />
        <StatusBadge status={historical?.status || 'not_applicable'} label="Historical Incident Matches" />
        <StatusBadge status={classification?.status || 'not_applicable'} label="Incident Classification and Prioritization" />
        <StatusBadge status={impact?.status || 'not_applicable'} label="Network Impact Assessment" />
        <StatusBadge status={recommendations?.status || 'not_applicable'} label="Recommended Actions" />
      </div>
      <div className="execution-strip"><span>Query planning: <strong>{execution.query_understanding || 'unknown'}</strong></span><span>Final summary: <strong>{execution.response_assembly || result?.overall_summary_status || 'unknown'}</strong></span><span>SOP: <strong>{recommendations?.data?.procedure_retrieval_called ? 'called' : recommendations?.status === 'not_requested' ? 'not requested' : 'not called'}</strong></span></div>
      {fallbackReport?.fallback_used && <div className="alert alert-warning compact-alert">A fallback was used for one or more stages. Expand the execution details in the agent flow for the reason.</div>}
    </section>
    <section className="card analysis-card">
      <div className="card-header"><div><div className="card-title">Analysis Summary</div><div className="card-subtitle">Evidence-grounded conclusion and next investigation steps</div></div><StatusBadge status={result.status || 'success'} /></div>
      <div className="summary-sections">
        <div><h4>Overall Finding</h4><p className="analysis-text">{finding}</p></div>
        <div className="leading-hypothesis"><h4>Leading RCA Hypothesis</h4><div className="hypothesis-title"><strong>{value(top?.hypothesis || top?.name, 'No leading hypothesis returned')}</strong>{top?.score !== undefined && <span className="hypothesis-score">Score {number(top.score)}</span>}</div><p>{value(top?.evidence || rca?.summary, 'The available evidence did not produce a leading hypothesis.')}</p><p className="muted">This is an investigative hypothesis based on historical patterns, not a confirmed physical cause.</p></div>
        <div><h4>Key Historical Evidence</h4><p className="analysis-text">{incidents.length ? `${incidents.length} historical incident match${incidents.length === 1 ? '' : 'es'} were retrieved.` : 'No historical incidents were retrieved.'}</p><div className="evidence-inline">{incidents.slice(0, 6).map((item, index) => { const incident = item?.incident || item || {}; return <span key={item?.incident_id || index}>{item?.incident_id || incident.incident_id || `Incident ${index + 1}`}{incident.packet_loss_rate !== undefined ? ` · packet loss ${number(incident.packet_loss_rate)}%` : ''}{incident.latency_ms !== undefined ? ` · latency ${number(incident.latency_ms)} ms` : ''}</span>; })}</div></div>
      </div>
    </section>

    <section className="card"><div className="card-header"><div><div className="card-title">Historical Incident Matches and Evidence</div><div className="card-subtitle">Historical matches are evidence, not proof of the same physical cause.</div></div><StatusBadge status={historical?.status || 'not_available'} label={`${incidents.length} Incidents`} /></div>
      {incidents.length === 0 ? <p className="muted">No historical incident matches were returned.</p> : <>
        <button type="button" className="incident-dropdown-toggle" onClick={() => setShowAllIncidents((visible) => !visible)}>
          <span>{showAllIncidents ? 'Hide incident list' : `View ${incidents.length} retrieved incidents`}</span>
          <span aria-hidden="true">{showAllIncidents ? '▲' : '▼'}</span>
        </button>
        {showAllIncidents && <div className="incident-list">{incidents.slice(0, 4).map((item, index) => { const incident = item?.incident || item || {}; const id = item?.incident_id || incident.incident_id || `Incident ${index + 1}`; return <div className="incident-row" key={id}>
        <div className="incident-main"><strong>{id}</strong><Metric label="Latency" value={incident.latency_ms} unit="ms" /><Metric label="Packet loss" value={incident.packet_loss_rate} unit="%" /><Metric label="Throughput" value={incident.throughput_mbps} unit="Mbps" /><Metric label="Season" value={incident.season} /></div>
        <button className="link-button" onClick={() => toggle(`incident-${id}`)}>{expanded[`incident-${id}`] ? 'Hide Evidence' : 'View Evidence'}</button>
        {expanded[`incident-${id}`] && <div className="evidence-grid">{Object.entries(incident).map(([key, itemValue]) => <div key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{value(itemValue)}</strong></div>)}</div>}
        </div>; })}
          {incidents.length > 4 && <details className="incident-more-details"><summary>View remaining {incidents.length - 4} incidents</summary><div className="incident-list">{incidents.slice(4).map((item, index) => { const incident = item?.incident || item || {}; const id = item?.incident_id || incident.incident_id || `Incident ${index + 5}`; return <div className="incident-row" key={id}>
            <div className="incident-main"><strong>{id}</strong><Metric label="Latency" value={incident.latency_ms} unit="ms" /><Metric label="Packet loss" value={incident.packet_loss_rate} unit="%" /><Metric label="Throughput" value={incident.throughput_mbps} unit="Mbps" /><Metric label="Season" value={incident.season} /></div>
            <button className="link-button" onClick={() => toggle(`incident-${id}`)}>{expanded[`incident-${id}`] ? 'Hide Evidence' : 'View Evidence'}</button>
            {expanded[`incident-${id}`] && <div className="evidence-grid">{Object.entries(incident).map(([key, itemValue]) => <div key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{value(itemValue)}</strong></div>)}</div>}
          </div>; })}</div></details>}
        </div>}
      </>}
      <div className="chart-section"><h4>Historical Metric Comparison</h4><div className="metric-chart-grid">{['latency_ms', 'packet_loss_rate', 'throughput_mbps'].map((metric) => { const vals = incidents.map((item) => Number((item?.incident || item || {})[metric])).filter(Number.isFinite); const max = Math.max(1, ...vals); return <div className="mini-chart" key={metric}><span>{metric.replaceAll('_', ' ')}</span>{incidents.map((item, index) => { const current = Number((item?.incident || item || {})[metric]); return <div className="bar-line" key={index}><small>{index + 1}</small><div><i style={{ width: `${Number.isFinite(current) ? current / max * 100 : 0}%` }} /></div><em>{Number.isFinite(current) ? number(current) : '—'}</em></div>; })}</div>; })}</div></div>
    </section>

    {historicalEvaluation?.status === 'available' && <section className="card"><div className="card-header"><div><div className="card-title">Filtered Historical Evaluation</div><div className="card-subtitle">Metadata-filtered averages, not current-network predictions</div></div><StatusBadge status="success" label={`${historicalEvaluation.data.record_count || 0} Records`} /></div><div className="historical-average-grid">{Object.entries(historicalEvaluation.data.aggregate_metrics || {}).map(([metric, average]) => <div className="historical-average-item" key={metric}><span>{metric.replaceAll('_', ' ')}</span><strong>{number(average)}</strong></div>)}</div><p className="muted">Filters were applied before aggregation. Seasonal, weather, and city results therefore change with the query.</p></section>}

    <section className="card"><div className="card-header"><div><div className="card-title">Incident Classification and Prioritization</div><div className="card-subtitle">Historical priority distribution{currentScenario?.priority ? ' and current scenario' : ''}</div></div>{currentScenario?.priority && <span className="badge badge-warning">{currentScenario.priority}</span>}</div><div className="priority-tiles">{['P1', 'P2', 'P3', 'P4'].map((key) => { const count = Number(counts[key] || 0); const ids = priorityIds[key] || []; return <div className={`priority-tile ${key.toLowerCase()}`} key={key}><strong>{key} <small>({count})</small></strong><span>{totalPrioritized ? `${Math.round(count / totalPrioritized * 100)}%` : '0%'}</span>{ids.length > 0 ? <ul className="priority-incident-list">{ids.map((id) => <li key={id}>{id}</li>)}</ul> : <em>No assigned incidents</em>}</div>; })}</div>{currentScenario && <div className="scenario-priority"><span>Current scenario</span><strong>{currentScenario.priority || 'Not classified'}</strong><small>{value(currentScenario.priority_level || currentScenario.priority_reason, 'No current telemetry classification')}</small></div>}</section>

    <section className="card"><div className="card-header"><div><div className="card-title">Root-Cause Analysis</div><div className="card-subtitle">Ranked evidence-based hypotheses, not confirmed physical causes</div></div><StatusBadge status={rca?.status || 'not_available'} /></div><p className="analysis-text">{value(rca?.summary, 'Root-cause analysis was not available.')}</p><div className="hypothesis-list">{hypotheses.map((item, index) => <div className="hypothesis-row" key={`${item.hypothesis}-${index}`}><div className="hypothesis-heading"><strong>{item.rank || index + 1}. {value(item.hypothesis || item.name)}</strong><span>{item.score !== undefined ? number(item.score) : 'No score'}</span></div><Bar score={item.score} /><button className="link-button" onClick={() => toggle(`hypothesis-${index}`)}>{expanded[`hypothesis-${index}`] ? 'Hide Evidence' : 'View Evidence'}</button>{expanded[`hypothesis-${index}`] && <div className="evidence-grid">{item.matched_incident_id && <div><span>Matched incident</span><strong>{item.matched_incident_id}</strong></div>}<div><span>Supporting signals</span><strong>{value(item.supporting_signals || item.evidence)}</strong></div></div>}</div>)}</div></section>

    {impact && <section className="card"><div className="card-header"><div><div className="card-title">Network Impact Assessment</div><div className="card-subtitle">Potential effects based on supplied telemetry or filtered historical averages</div></div><StatusBadge status={impact?.status || 'not_available'} label={impact?.analysis_basis === 'historical_filtered_aggregate' ? 'Historical Baseline' : undefined} /></div>{Array.isArray(impact?.data?.findings) && impact.data.findings.length > 0 ? <div className="impact-list">{impact.data.findings.map((finding, index) => <div className="impact-row" key={`${finding.metric || 'impact'}-${index}`}><div className="impact-heading"><strong>{value(finding.metric, 'Network signal')}</strong>{finding.observed_value !== undefined && <span>{number(finding.observed_value)}</span>}</div><p>{value(finding.potential_impact, 'Potential service impact detected.')}</p>{finding.source && <small>Source: {finding.source}</small>}</div>)}</div> : <p className="muted">{value(impact?.summary, impact?.analysis_basis === 'historical_filtered_aggregate' ? 'The historical baseline did not cross configured impact indicators.' : 'No potential impact indicators were identified.')}</p>}<p className="muted">Potential effects are not confirmed customer outcomes and do not establish root cause. Historical-baseline findings are not current-network observations.</p></section>}

    {recommendations && <section className="card"><div className="card-header"><div><div className="card-title">Recommended Actions</div><div className="card-subtitle">Actions derived from retrieved SOP procedures</div></div><StatusBadge status={recommendations?.status || 'not_available'} /></div>{diagnosticChecks.length > 0 && <div className="diagnostic-checks"><div className="subsection-title">Diagnostic Checks</div><ol>{diagnosticChecks.map((check, index) => <li key={`${check}-${index}`}>{check}</li>)}</ol></div>}{procedures.length > 0 ? <div className="action-list">{procedures.map((procedure, index) => { const procedureActions = actions.filter((item) => (item.procedure_id && item.procedure_id === (procedure.sop_id || procedure.procedure_id)) || (item.procedure_name && item.procedure_name === (procedure.name || procedure.title))); return <div className="action-row" key={index}><strong>{index + 1}. {value(procedure.name || procedure.title || procedure.sop_id || procedure.procedure_id, 'Procedure')}</strong><span>{value(procedure.description || procedure.summary || procedureActions.slice(0, 2).map((item) => item.action).join(' '), 'Review the relevant network measurements, alarms, historical pattern, and escalation criteria.')}</span></div>; })}</div> : <p className="muted">{recommendations.status === 'not_requested' ? 'No troubleshooting request was detected, so SOP retrieval was skipped.' : recommendations.status === 'unavailable' ? 'SOP retrieval was requested but the Synapt procedure source was unavailable.' : 'SOP retrieval returned no procedures.'}</p>}<p className="muted">Verify prototype procedures against the authorized operational runbook before execution.</p></section>}

    {predictionAvailable && <section className="card"><div className="card-header"><div><div className="card-title">{historicalBaseline ? 'Historical Network Baseline' : 'Network Prediction Results'}</div><div className="card-subtitle">{historicalBaseline ? 'Descriptive averages used when current telemetry is absent; live predictions require telemetry' : 'Compact model outcomes; values are predictions'}</div></div><StatusBadge status={predictionData.status || prediction?.status || 'success'} label={historicalBaseline ? 'Historical Baseline' : undefined} /></div><PredictionSummary prediction={{ ...predictionPayload, ...predictionData }} mode={predictionData.prediction_mode} />{!historicalBaseline && predictionData.prediction_mode !== 'fault_tolerance' && <ModelAgreementCard prediction={predictionPayload} />}</section>}
  </div>;
}
