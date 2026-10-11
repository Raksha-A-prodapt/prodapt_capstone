import React, { useState, useEffect } from 'react';
import KPICard from '../components/KPICard';
import StatusBadge from '../components/StatusBadge';
import { fetchHealth } from '../services/api';
import datasetSummaryData from '../data/dataset_summary.json';

export default function HomeDashboard({ onNavigate }) {
  const [healthStatus, setHealthStatus] = useState({ online: false, initialized: false, checking: true });
  const [datasetSummary, setDatasetSummary] = useState(datasetSummaryData);

  // Poll API health
  useEffect(() => {
    let isMounted = true;
    async function checkHealth() {
      try {
        const data = await fetchHealth();
        if (isMounted) {
          setHealthStatus({
            online: true,
            initialized: Boolean(data.orchestrator_initialized),
            checking: false,
          });
        }
      } catch (err) {
        if (isMounted) {
          setHealthStatus({ online: false, initialized: false, checking: false });
        }
      }
    }

    checkHealth();
    const interval = setInterval(checkHealth, 8000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const kpis = datasetSummary?.kpis || [];
  const charts = datasetSummary?.charts || {};
  const seasonsData = charts.incidents_by_season || [];
  const weatherData = charts.incidents_by_weather || [];
  const issueData = charts.issue_reported_distribution || [];
  const seasonalMetrics = charts.seasonal_metric_averages || [];

  return (
    <div className="app-container">
      {/* Welcome & System Status Bar */}
      <div
        className="card"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          padding: '16px 20px',
          marginBottom: '20px',
        }}
      >
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-text)' }}>
            Network Operations Overview
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
            5G NetOps historical telemetry dataset analysis, predictive machine learning, and semantic troubleshooting.
          </p>
        </div>

        {/* API Health Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              backgroundColor: 'var(--color-input)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: healthStatus.online ? 'var(--color-accent)' : 'var(--color-error)',
                display: 'inline-block',
              }}
            />
            <span style={{ color: 'var(--color-text)' }}>
              {healthStatus.checking
                ? 'Connecting to API...'
                : healthStatus.online
                ? (healthStatus.initialized ? 'API Online • Orchestrator Ready' : 'API Online • Ready')
                : 'API Disconnected (127.0.0.1:8001)'}
            </span>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Dataset Summary KPIs
        </div>
        <div className="grid-6">
          {kpis.map((kpi) => (
            <KPICard
              key={kpi.id}
              label={kpi.label}
              value={kpi.value}
              unit={kpi.unit}
              subtitle={kpi.percent ? `${kpi.percent}% of total` : undefined}
              highlight={kpi.id === 'total_incidents'}
            />
          ))}
        </div>
      </div>

      {/* Visualizations Section: 4 Compact Charts */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Precomputed Dataset Distributions
        </div>
        <div className="grid-2">
          {/* Chart 1: Incidents by Season */}
          <div className="card" style={{ margin: 0 }}>
            <div className="card-header">
              <div>
                <div className="card-title">Incidents by Season</div>
                <div className="card-subtitle">Distribution across 100,000 historical records</div>
              </div>
              <span className="badge badge-teal">Seasonal</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {seasonsData.map((item) => {
                const max = 26000;
                const pct = ((item.count / max) * 100).toFixed(1);
                return (
                  <div key={item.category}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--color-text)' }}>{item.category}</span>
                      <span style={{ color: 'var(--color-accent)', fontFamily: 'var(--font-mono)' }}>
                        {item.count.toLocaleString()} records
                      </span>
                    </div>
                    <div style={{ height: '8px', backgroundColor: 'var(--color-input)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${pct}%`,
                          height: '100%',
                          backgroundColor: 'var(--color-primary)',
                          borderRadius: '4px',
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Chart 2: Incidents by Weather */}
          <div className="card" style={{ margin: 0 }}>
            <div className="card-header">
              <div>
                <div className="card-title">Incidents by Weather Condition</div>
                <div className="card-subtitle">Environmental conditions during incident logging</div>
              </div>
              <span className="badge badge-teal">Weather</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {weatherData.map((item) => {
                const max = 35000;
                const pct = ((item.count / max) * 100).toFixed(1);
                return (
                  <div key={item.category}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--color-text)' }}>{item.category}</span>
                      <span style={{ color: 'var(--color-accent)', fontFamily: 'var(--font-mono)' }}>
                        {item.count.toLocaleString()} records
                      </span>
                    </div>
                    <div style={{ height: '8px', backgroundColor: 'var(--color-input)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${pct}%`,
                          height: '100%',
                          backgroundColor: 'var(--color-accent)',
                          borderRadius: '4px',
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Chart 3: Issue Reported vs Normal */}
          <div className="card" style={{ margin: 0 }}>
            <div className="card-header">
              <div>
                <div className="card-title">Issue Reported Ratio</div>
                <div className="card-subtitle">Verified incident flag proportion</div>
              </div>
              <span className="badge badge-teal">Ground Truth</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {issueData.map((item) => {
                const isReported = item.category === 'Yes';
                return (
                  <div key={item.category}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--color-text)' }}>
                        {isReported ? 'Issue Reported (Degraded)' : 'No Issue Reported (Baseline)'}
                      </span>
                      <span style={{ color: isReported ? 'var(--color-warning)' : 'var(--color-accent)', fontFamily: 'var(--font-mono)' }}>
                        {item.count.toLocaleString()} ({item.percent}%)
                      </span>
                    </div>
                    <div style={{ height: '10px', backgroundColor: 'var(--color-input)', borderRadius: '5px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${item.percent}%`,
                          height: '100%',
                          backgroundColor: isReported ? 'var(--color-warning)' : 'var(--color-primary)',
                          borderRadius: '5px',
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Chart 4: Seasonal Metric Averages */}
          <div className="card" style={{ margin: 0 }}>
            <div className="card-header">
              <div>
                <div className="card-title">Seasonal Metric Averages</div>
                <div className="card-subtitle">Throughput (Mbps) and Latency (ms) across seasons</div>
              </div>
              <span className="badge badge-teal">Averages</span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)', textAlign: 'left' }}>
                    <th style={{ padding: '6px 8px' }}>Season</th>
                    <th style={{ padding: '6px 8px' }}>Latency</th>
                    <th style={{ padding: '6px 8px' }}>Throughput</th>
                    <th style={{ padding: '6px 8px' }}>Pkt Loss</th>
                    <th style={{ padding: '6px 8px' }}>Fault Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {seasonalMetrics.map((row) => (
                    <tr key={row.season} style={{ borderBottom: '1px solid var(--color-border)' }}>
                      <td style={{ padding: '8px', color: 'var(--color-text)', fontWeight: 600 }}>{row.season}</td>
                      <td style={{ padding: '8px', color: 'var(--color-accent)' }}>{row.latency_ms} ms</td>
                      <td style={{ padding: '8px', color: 'var(--color-text)' }}>{row.throughput_mbps} Mbps</td>
                      <td style={{ padding: '8px', color: 'var(--color-text-muted)' }}>{row.packet_loss_percent}%</td>
                      <td style={{ padding: '8px', color: 'var(--color-warning)' }}>{row.fault_occurrence_percent}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Navigation Shortcuts */}
      <div>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Workspace Modules
        </div>
        <div className="grid-3">
          <div
            className="card"
            style={{
              margin: 0,
              cursor: 'pointer',
              borderColor: 'var(--color-border)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
            onClick={() => onNavigate('assistant')}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '20px' }}>🤖</span>
                <span style={{ fontSize: '15px', fontWeight: 600, color: 'var(--color-text)' }}>
                  AI Assistant
                </span>
              </div>
              <p style={{ fontSize: '12.5px', color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
                Natural-language telecom incident search, hybrid Chroma+BM25 retrieval, telemetry gating, root-cause analysis, and SOP-derived recommended actions.
              </p>
            </div>
            <div style={{ marginTop: '16px' }}>
              <span className="btn btn-secondary btn-sm" style={{ width: '100%' }}>
                Launch Assistant →
              </span>
            </div>
          </div>

          <div
            className="card"
            style={{
              margin: 0,
              cursor: 'pointer',
              borderColor: 'var(--color-border)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
            onClick={() => onNavigate('prediction')}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '20px' }}>⚡</span>
                <span style={{ fontSize: '15px', fontWeight: 600, color: 'var(--color-text)' }}>
                  Network Performance & Fault Prediction
                </span>
              </div>
              <p style={{ fontSize: '12.5px', color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
                Run Model 1 (Throughput regressor, 24 features) and Model 2 (Fault Occurrence regressor, 22 features) independently with full feature validation.
              </p>
            </div>
            <div style={{ marginTop: '16px' }}>
              <span className="btn btn-secondary btn-sm" style={{ width: '100%' }}>
                Open ML Predictors →
              </span>
            </div>
          </div>

          <div
            className="card"
            style={{
              margin: 0,
              cursor: 'pointer',
              borderColor: 'var(--color-border)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
            onClick={() => onNavigate('evaluations')}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '20px' }}>📊</span>
                <span style={{ fontSize: '15px', fontWeight: 600, color: 'var(--color-text)' }}>
                  Evaluations
                </span>
              </div>
              <p style={{ fontSize: '12.5px', color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
                Review real ML model metrics (R² 0.9997, MAE 0.17%) and DeepEval test suite results (40/40 tests passed, GEval quality scores, hallucination rates).
              </p>
            </div>
            <div style={{ marginTop: '16px' }}>
              <span className="btn btn-secondary btn-sm" style={{ width: '100%' }}>
                View Evaluations →
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
