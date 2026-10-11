import React, { useState } from 'react';
import StatusBadge from './StatusBadge';

export default function AgentFlow({ isOpen, onClose, analysisResult }) {
  const [expandedStage, setExpandedStage] = useState(null);

  if (!isOpen) return null;

  const trace = analysisResult?.trace || {};
  const sections = analysisResult?.sections || [];
  const hasLiveExecution = Boolean(analysisResult);
  const agentOutputs = analysisResult?.trace?.agent_outputs || {};
  const outputKeyByStage = {
    query_understanding: 'query_retrieval',
    incident_search: 'query_retrieval',
    prediction: 'prediction',
    rca: 'root_cause_analysis',
    classification: 'classification',
    impact: 'network_impact',
    recommendations: 'recommendations',
    response_assembly: 'response_summary',
  };

  const formatOutput = (value) => {
    if (value === undefined || value === null) return '';
    if (typeof value === 'string') return value;
    return JSON.stringify(value, null, 2);
  };

  // Keep technical prompts and raw provider payloads out of the normal flow
  // view. The full API trace remains available to backend diagnostics.
  const displayStageOutput = (stageId, value) => {
    if (!value || typeof value !== 'object') return value;
    if (stageId === 'query_understanding' || stageId === 'incident_search') {
      return {
        status: value.status,
        query_plan: value.query_plan_public,
        filter_diagnostics: value.filter_diagnostics,
        retrieval: value.retrieval,
        answer: value.answer,
        fallbacks: value.fallbacks,
      };
    }
    if (stageId === 'recommendations') {
      return {
        status: value.status,
        procedure_retrieval_called: value.procedure_retrieval_called,
        procedures: value.procedures,
        recommendations: value.recommendations,
      };
    }
    return value;
  };

  // Helper to extract section by id
  const getSection = (id) => sections.find((s) => s.id === id);

  const histSection = getSection('historical_data');
  const predSection = getSection('prediction');
  const rcaSection = getSection('root_cause_analysis');
  const classSection = getSection('incident_prioritization');
  const impactSection = getSection('network_impact');
  const recSection = getSection('recommendations');

  // Define actual stages matching APPLICATION_FLOW.md and TelecomAnalysisOrchestrator
  const stages = [
    {
      id: 'guardrail',
      number: 1,
      title: 'Input Guardrail & Validation',
      component: 'InputGuardrail',
      purpose: 'Validates query length (1-4000), top_k range (1-50), and blocks off-topic or malformed queries before analysis.',
      origin: 'Rule-based / Deterministic',
      originType: 'deterministic',
      status: hasLiveExecution ? 'success' : 'reference',
      input: hasLiveExecution ? analysisResult.query : 'User query string, top_k, optional telemetry',
      output: hasLiveExecution ? 'Query passed validation checks' : 'Validated query payload or rejection',
      toolCall: 'None (Local deterministic validator)',
      isSkipped: false,
      details: 'Prevents adversarial or invalid payloads from executing downstream retrieval and LLM agents.',
    },
    {
      id: 'query_understanding',
      number: 2,
      title: 'Query Understanding & Synapt Context',
      component: trace.query_agent || 'QuerySynaptAgent',
      purpose: 'Fetches advisory telecom-domain context from Synapt (ask_synapt) and constructs structured retrieval filters.',
      origin: trace.llm_call_sources?.includes('QuerySynaptAgent.query_planning')
        ? 'LLM-generated'
        : 'Rule-based / Deterministic fallback',
      originType: trace.llm_call_sources?.includes('QuerySynaptAgent.query_planning') ? 'llm' : 'deterministic',
      status: hasLiveExecution
        ? (trace.retrieval_status === 'no_evidence' ? 'warning' : 'success')
        : 'reference',
      input: hasLiveExecution ? analysisResult.query : 'User query and advisory telecom taxonomy',
      output: hasLiveExecution
        ? `Synapt context: ${trace.synapt_domain_context_status || 'offline stub'}`
        : 'Retrieval plan with metadata & numeric thresholds',
      toolCall: 'Synapt MCP: ask_synapt (port 8000)',
      isSkipped: false,
      details: 'Synapt provides advisory guidance; local incident database remains the ground-truth evidence store.',
    },
    {
      id: 'incident_search',
      number: 3,
      title: 'Historical Incident Search (Hybrid RAG)',
      component: 'ChromaDB + BM25 Lexical Retriever',
      purpose: 'Executes hybrid retrieval: Chroma vector search (0.6) combined with BM25 keyword matching (0.4) on incident dataset.',
      origin: 'Retrieved Data / Tool',
      originType: 'tool',
      status: hasLiveExecution
        ? (histSection?.data?.incidents?.length > 0 ? 'success' : 'warning')
        : 'reference',
      input: hasLiveExecution ? 'Retrieval filters and semantic embedding query' : 'Dense vector embedding + lexical keywords',
      output: hasLiveExecution
        ? `${histSection?.data?.matching_count ?? 0} matching records found (${histSection?.data?.returned_count ?? 0} returned)`
        : 'Ranked historical incidents with telemetry features',
      toolCall: 'Chroma persistent collection: rag/chroma_db + RankBM25',
      isSkipped: false,
      details: 'Matches against data/telecom_network_incidents_with_id.csv containing 100,000 operational records.',
    },
    {
      id: 'prediction',
      number: 4,
      title: 'Network Prediction Agent',
      component: 'NetworkPredictionAgent',
      purpose: 'Runs XGBoost ML pipelines to forecast Throughput (Mbps) and Fault Occurrence Rate (%) when telemetry features are supplied.',
      origin: (trace.prediction_models_called?.length > 0) ? 'Rule-based / Deterministic' : 'Skipped or Not Applicable',
      originType: (trace.prediction_models_called?.length > 0) ? 'deterministic' : 'skipped',
      status: hasLiveExecution
        ? (predSection?.status === 'success' ? 'success' : predSection?.status === 'partial' ? 'warning' : 'not_applicable')
        : 'reference',
      input: hasLiveExecution
        ? (trace.prediction_models_called?.length > 0 ? 'Telemetry metrics payload' : 'None (Telemetry omitted)')
        : '24 Throughput features or 22 Fault Risk features',
      output: hasLiveExecution
        ? (predSection?.summary || 'Predictions skipped (no telemetry provided)')
        : 'Predicted Throughput (Mbps) and Fault Rate (%)',
      toolCall: 'ml_model/models/*.joblib pipelines',
      isSkipped: hasLiveExecution ? (trace.prediction_models_called?.length === 0) : false,
      details: 'Predictions are machine learning estimates; they are strictly distinguished from observed measurements.',
    },
    {
      id: 'rca',
      number: 5,
      title: 'Root-Cause Analysis (RCA) Agent',
      component: 'RCAAgent',
      purpose: 'Compares retrieved incident evidence with current symptoms to rank hypothesized failure modes.',
      origin: 'Rule-based / Deterministic',
      originType: 'deterministic',
      status: hasLiveExecution
        ? (rcaSection?.status === 'success' ? 'success' : 'not_applicable')
        : 'reference',
      input: hasLiveExecution ? 'Retrieved historical cases + metric differentials' : 'Retrieved incidents + prediction outputs',
      output: hasLiveExecution
        ? (rcaSection?.summary || 'RCA hypothesis evaluated')
        : 'Ranked failure hypotheses with evidence links',
      toolCall: 'agents.rca_agent: compare_and_rank_hypotheses',
      isSkipped: false,
      details: 'RCA outputs are framed strictly as investigative hypotheses, never confirmed physical causes.',
    },
    {
      id: 'classification',
      number: 6,
      title: 'Incident Classification & Triage',
      component: 'IncidentClassificationAgent',
      purpose: 'Assigns operational priority tiers (P1 to P4) based on telemetry severity cutoffs.',
      origin: 'Rule-based / Deterministic',
      originType: 'deterministic',
      status: hasLiveExecution ? 'success' : 'reference',
      input: hasLiveExecution ? 'Retrieved examples and active telemetry' : 'Incident records and telemetry metrics',
      output: hasLiveExecution
        ? (classSection?.summary || 'Severity and priority triage completed')
        : 'P1-P4 priority counts and classification tiers',
      toolCall: 'agents.incident_classifier: classify_scenario',
      isSkipped: false,
      details: 'Priority codes represent dataset-relative operational triage, not binding service level agreements.',
    },
    {
      id: 'impact',
      number: 7,
      title: 'Network Impact Assessment',
      component: 'NetworkImpactAnalyzer',
      purpose: 'Evaluates potential service degradation risks (voice quality, data throughput, handover drops).',
      origin: 'Rule-based / Deterministic',
      originType: 'deterministic',
      status: hasLiveExecution ? 'success' : 'reference',
      input: hasLiveExecution ? 'Telemetry thresholds and prediction outputs' : 'Observed and predicted metric values',
      output: hasLiveExecution
        ? (impactSection?.summary || 'Impact risk assessment completed')
        : 'Degradation severity indicators & potential effects',
      toolCall: 'agents.impact_analysis: analyze_network_impact',
      isSkipped: false,
      details: 'Describes potential service impacts; does not assert confirmed customer damage or legal SLA breach.',
    },
    {
      id: 'recommendations',
      number: 8,
      title: 'SOP & Recommended Actions Agent',
      component: 'RecommendationAgent',
      purpose: 'Retrieves relevant standard operating procedures from Synapt MCP only when actionable troubleshooting is requested.',
      origin: (recSection?.status === 'success')
        ? 'Retrieved Data / Tool'
        : (recSection?.status === 'unavailable' ? 'Fallback response' : 'Skipped or Not Applicable'),
      originType: (recSection?.status === 'success')
        ? 'tool'
        : (recSection?.status === 'unavailable' ? 'fallback' : 'skipped'),
      status: hasLiveExecution
        ? (recSection?.status === 'success' ? 'success' : recSection?.status === 'unavailable' ? 'error' : 'not_requested')
        : 'reference',
      input: hasLiveExecution
        ? `Procedure requested: ${trace.synapt_procedure_retrieval_called ? 'Yes' : 'No'}`
        : 'Troubleshooting intent + RCA leading hypothesis',
      output: hasLiveExecution
        ? (recSection?.summary || 'Procedure retrieval skipped (action intent not detected)')
        : 'Standard operating procedure steps with procedure IDs',
      toolCall: 'Synapt MCP: get_synapt_procedures (port 8000)',
      isSkipped: hasLiveExecution ? !trace.synapt_procedure_retrieval_called : false,
      details: 'SOP actions are retrieved on-demand; synthetic procedures are prototype guidance, not production work orders.',
    },
    {
      id: 'response_assembly',
      number: 9,
      title: 'Response Assembly & Summarization',
      component: 'TelecomAnalysisOrchestrator',
      purpose: 'Packages structured sections and synthesizes the final comprehensive answer using LLM or deterministic fallback.',
      origin: analysisResult?.overall_summary_source === 'llm'
        ? 'LLM-generated'
        : (analysisResult?.overall_summary_source === 'deterministic_fallback' ? 'Fallback response' : 'Rule-based / Deterministic'),
      originType: analysisResult?.overall_summary_source === 'llm' ? 'llm' : 'deterministic',
      status: hasLiveExecution ? (analysisResult.status === 'success' ? 'success' : 'warning') : 'reference',
      input: hasLiveExecution ? 'All upstream component outputs' : 'Aggregated results from all active agents',
      output: hasLiveExecution ? 'final_answer and structured response sections' : 'Integrated final response payload',
      toolCall: trace.summary_llm_call_invoked ? 'Claude / LLM generate()' : 'Deterministic section serializer',
      isSkipped: false,
      details: 'Preserves exact evidence and data boundaries; handles LLM fallback seamlessly if the provider is offline.',
    },
    {
      id: 'trace_eval',
      number: 10,
      title: 'DeepEval Contract & Evidence Checks',
      component: 'DeepEval Orchestrator Validator',
      purpose: 'Executes deterministic checks ensuring response contract completeness and evidence grounding.',
      origin: 'Rule-based / Deterministic',
      originType: 'deterministic',
      status: hasLiveExecution ? 'success' : 'reference',
      input: hasLiveExecution ? 'Generated final response JSON' : 'Output JSON schema and evidence linkages',
      output: hasLiveExecution ? 'Schema contract validated' : 'Contract validation pass/fail trace',
      toolCall: 'evaluations.orchestrator_deepeval: response_contract_metric',
      isSkipped: false,
      details: 'Normal production runtime uses deterministic contract tests; offline test suites run GEval LLM-as-judge.',
    },
  ];

  // Overlay observed runtime states without changing the documented stage flow.
  const runtimeStatuses = trace.execution_statuses || {};
  const liveStages = stages.map((stage) => ({
    ...stage,
    status: hasLiveExecution && runtimeStatuses[stage.id]
      ? runtimeStatuses[stage.id]
      : stage.status,
    isSkipped: hasLiveExecution && runtimeStatuses[stage.id] === 'skipped',
  }));

  const getOriginBadge = (originType) => {
    switch (originType) {
      case 'llm':
        return <span className="badge badge-teal">⚡ LLM-generated</span>;
      case 'deterministic':
        return <span className="badge badge-muted">⚙️ Rule-based / Deterministic</span>;
      case 'tool':
        return <span className="badge badge-success">📦 Retrieved Data / Tool</span>;
      case 'fallback':
        return <span className="badge badge-warning">⚠️ Fallback Response</span>;
      case 'skipped':
        return <span className="badge badge-muted">⏭️ Skipped / Inactive</span>;
      default:
        return <span className="badge badge-muted">ℹ️ Documented Spec</span>;
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        style={{ maxWidth: '960px', maxHeight: '92vh' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="modal-header">
          <div>
            <div className="card-title" style={{ fontSize: '18px' }}>
              <span>🔀</span> Telecom Agent Orchestration Workflow
            </div>
            <div className="card-subtitle">
              {hasLiveExecution
                ? 'Observed execution flow for current query analysis'
                : 'Documented LangGraph architecture & component pipeline (Reference Mode)'}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="btn btn-secondary btn-xs"
            style={{ fontSize: '14px', padding: '4px 8px' }}
          >
            ✕ Close
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Origin Legend */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '10px',
              backgroundColor: 'var(--color-input)',
              padding: '12px 16px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              marginBottom: '20px',
            }}
          >
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text)' }}>
              Response Origin Legend:
            </span>
            <span className="badge badge-teal">⚡ LLM-generated</span>
            <span className="badge badge-muted">⚙️ Rule-based / Deterministic</span>
            <span className="badge badge-success">📦 Retrieved Data / Tool</span>
            <span className="badge badge-warning">⚠️ Fallback Response</span>
            <span className="badge badge-muted">⏭️ Skipped / Inactive</span>
          </div>

          {hasLiveExecution && trace.fallback_report?.fallback_used && (
            <div className="alert alert-warning" style={{ marginBottom: '20px' }}>
              <div>
                <strong>Fallbacks used during this run</strong>
                <div style={{ marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {(trace.fallback_report.fallbacks || []).map((item, index) => (
                    <div key={index}>
                      {item.stage}: {item.method}. Reason: {item.reason}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {!hasLiveExecution && (
            <div className="alert alert-info" style={{ marginBottom: '20px' }}>
              <span>ℹ️</span>
              <div>
                <strong>Reference View:</strong> Showing the documented architecture pipeline from 
                <code>APPLICATION_FLOW.md</code>. Run a query in the AI Assistant to observe live agent execution traces.
              </div>
            </div>
          )}

          {/* Workflow Stages Stack */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {liveStages.map((stage, idx) => {
              const isExpanded = expandedStage === stage.id;
              const isLast = idx === stages.length - 1;
              const stageResult = agentOutputs[outputKeyByStage[stage.id]];

              return (
                <div key={stage.id} style={{ position: 'relative' }}>
                  <div
                    className="card"
                    style={{
                      margin: 0,
                      backgroundColor: stage.isSkipped ? '#0c0f0f' : 'var(--color-card)',
                      borderColor: isExpanded ? 'var(--color-accent)' : 'var(--color-border)',
                      opacity: stage.isSkipped ? 0.65 : 1,
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        cursor: 'pointer',
                        gap: '12px',
                      }}
                      onClick={() => setExpandedStage(isExpanded ? null : stage.id)}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
                        <div
                          style={{
                            width: '28px',
                            height: '28px',
                            borderRadius: '50%',
                            backgroundColor: stage.isSkipped ? '#1c2727' : 'var(--color-primary)',
                            color: 'var(--color-text)',
                            fontSize: '12px',
                            fontWeight: 700,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                          }}
                        >
                          {stage.number}
                        </div>

                        <div>
                          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text)' }}>
                            {stage.title}
                          </div>
                          <div style={{ fontSize: '11.5px', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                            {stage.component}
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        {getOriginBadge(stage.originType)}
                        <StatusBadge
                          status={stage.isSkipped ? 'skipped' : stage.status}
                          label={stage.isSkipped ? 'Skipped' : (hasLiveExecution ? undefined : 'Active Pipeline')}
                          size="xs"
                        />
                        <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                          {isExpanded ? '▲' : '▼'}
                        </span>
                      </div>
                    </div>

                    {/* Quick summary line when collapsed */}
                    {!isExpanded && (
                      <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '8px', paddingLeft: '40px' }}>
                        {stage.purpose}
                      </div>
                    )}

                    {/* Expandable details panel */}
                    {isExpanded && (
                      <div
                        style={{
                          marginTop: '14px',
                          paddingTop: '12px',
                          borderTop: '1px solid var(--color-border)',
                          fontSize: '12.5px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '8px',
                        }}
                      >
                        <div>
                          <strong style={{ color: 'var(--color-accent)' }}>Component Purpose: </strong>
                          <span>{stage.purpose}</span>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                          <div style={{ backgroundColor: 'var(--color-input)', padding: '8px 10px', borderRadius: '4px' }}>
                            <strong style={{ color: 'var(--color-text)', fontSize: '11.5px', display: 'block' }}>
                              Input Received:
                            </strong>
                            <code style={{ fontSize: '11.5px', color: 'var(--color-text-muted)' }}>
                              {stage.input}
                            </code>
                          </div>

                          <div style={{ backgroundColor: 'var(--color-input)', padding: '8px 10px', borderRadius: '4px' }}>
                            <strong style={{ color: 'var(--color-text)', fontSize: '11.5px', display: 'block' }}>
                              Output / Result:
                            </strong>
                            <code style={{ fontSize: '11.5px', color: 'var(--color-text-muted)' }}>
                              {stage.output}
                            </code>
                          </div>
                        </div>

                        <div style={{ fontSize: '11.5px', color: '#889999' }}>
                          <strong>Tool/Agent Call: </strong>
                          <code>{stage.toolCall}</code>
                        </div>

                        <div style={{ fontSize: '11.5px', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                          Note: {stage.details}
                        </div>
                        {stageResult !== undefined && (
                          <div style={{ backgroundColor: 'var(--color-input)', padding: '8px 10px', borderRadius: '4px' }}>
                            <strong style={{ color: 'var(--color-accent)', fontSize: '11.5px', display: 'block' }}>
                              Result passed to downstream agents:
                            </strong>
                            <pre style={{ marginTop: '6px', whiteSpace: 'pre-wrap', color: 'var(--color-text-muted)', fontSize: '11px', maxHeight: '260px', overflow: 'auto' }}>
                              {formatOutput(displayStageOutput(stage.id, stageResult))}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Flow arrow connector */}
                  {!isLast && (
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'center',
                        padding: '4px 0',
                        color: 'var(--color-primary)',
                        fontSize: '12px',
                      }}
                    >
                      ↓
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
