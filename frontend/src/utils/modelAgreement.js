export function getModelAgreement(prediction) {
  const performance = prediction?.network_performance;
  const fault = prediction?.fault_risk;
  const performanceStatus = String(performance?.classification?.overall_risk || '').toUpperCase();
  const faultRisk = String(fault?.fault_risk || '').toUpperCase();
  const performanceReady = performance?.status === 'success' && performanceStatus;
  const faultReady = fault?.status === 'success' && faultRisk;

  if (!performanceReady && !faultReady) return { label: 'Unavailable', tone: 'neutral', detail: 'No model result' };
  if (!performanceReady || !faultReady) return { label: 'Incomplete', tone: 'neutral', detail: 'One model result missing' };
  if (performanceStatus === 'CRITICAL' && faultRisk === 'CRITICAL') return { label: 'Critical agreement', tone: 'critical', detail: 'Both models show critical risk' };
  if (performanceStatus === 'CRITICAL') return { label: 'Performance critical', tone: 'critical', detail: 'Performance model shows critical risk' };
  if (faultRisk === 'CRITICAL') return { label: 'Fault critical', tone: 'critical', detail: 'Fault model shows critical risk' };
  if (performanceStatus === 'HIGH' && ['HIGH', 'CRITICAL'].includes(faultRisk)) return { label: 'High-risk agreement', tone: 'critical', detail: 'Both models show elevated risk' };
  if (performanceStatus === 'HIGH') return { label: 'Performance warning', tone: 'warning', detail: 'Performance degradation detected' };
  if (['HIGH', 'MEDIUM'].includes(faultRisk)) return { label: 'Fault warning', tone: 'warning', detail: 'Fault model shows elevated risk' };
  if (performanceStatus === 'MEDIUM' && faultRisk === 'LOW') return { label: 'Moderate degradation', tone: 'warning', detail: 'Performance needs attention' };
  if (performanceStatus === 'LOW' && faultRisk === 'MEDIUM') return { label: 'Emerging fault risk', tone: 'warning', detail: 'Fault risk is above healthy range' };
  if (performanceStatus === 'LOW' && faultRisk === 'LOW') return { label: 'Healthy agreement', tone: 'healthy', detail: 'Both models show low risk' };
  return { label: 'Mixed result', tone: 'neutral', detail: 'Models identify different risk levels' };
}
