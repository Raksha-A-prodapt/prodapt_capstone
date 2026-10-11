import React from 'react';
import { getModelAgreement } from '../utils/modelAgreement';

export default function ModelAgreementCard({ prediction }) {
  const agreement = getModelAgreement(prediction);
  const performanceRisk = prediction?.network_performance?.classification?.overall_risk || '—';
  const faultRisk = prediction?.fault_risk?.fault_risk || '—';

  return <div className="card model-agreement-card">
    <div className="card-header"><div><div className="card-title">Model Agreement</div><div className="card-subtitle">Performance + fault risk</div></div><span className={`agreement-badge agreement-${agreement.tone}`}>{agreement.label}</span></div>
    <div className="agreement-row"><span>Performance</span><strong>{performanceRisk}</strong><span>Fault risk</span><strong>{faultRisk}</strong></div>
    <div className="agreement-detail">{agreement.detail}</div>
  </div>;
}
