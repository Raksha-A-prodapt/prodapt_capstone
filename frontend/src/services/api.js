/**
 * Telecom Network Operations Assistant API Client
 * Compatible with backend Starlette API on port 8001
 */

export const API_BASE_URL = 'http://127.0.0.1:8001';

/**
 * Check backend API liveness and orchestrator initialization state.
 * @returns {Promise<{status: string, orchestrator_initialized: boolean}>}
 */
export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Health check returned HTTP ${response.status}`);
  }
  return response.json();
}

/**
 * Execute telecom incident analysis query flow.
 * @param {Object} params
 * @param {string} params.query
 * @param {Object|null} params.network_metrics
 * @returns {Promise<Object>}
 */
export async function analyzeQuery({ query, network_metrics = null, prediction_mode = 'network_performance' }) {
  const payload = {
    query: query.trim(),
    top_k: 15,
    network_metrics: network_metrics && Object.keys(network_metrics).length > 0 ? network_metrics : null,
    prediction_mode,
  };

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 120000);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new Error('Analysis timed out after 120 seconds. Check that Synapt and the backend are responding.');
    }
    throw new Error(`Could not reach the analysis API at ${API_BASE_URL}: ${error.message}`);
  } finally {
    window.clearTimeout(timeoutId);
  }

  const data = await response.json().catch(() => ({ detail: 'Invalid JSON response from server' }));

  if (!response.ok) {
    const errorDetail = data.detail 
      ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))
      : `Analysis failed with HTTP ${response.status}`;
    throw new Error(errorDetail);
  }

  return data;
}

/**
 * Classify and triage a current metric scenario.
 * @param {Object} networkMetrics
 * @returns {Promise<Object>}
 */
export async function classifyScenario(networkMetrics) {
  const response = await fetch(`${API_BASE_URL}/api/classify`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ network_metrics: networkMetrics }),
  });

  const data = await response.json().catch(() => ({ detail: 'Invalid JSON response from server' }));

  if (!response.ok) {
    const errorDetail = data.detail || `Classification failed with HTTP ${response.status}`;
    throw new Error(errorDetail);
  }

  return data;
}

/**
 * Run the ML prediction agent directly, without the assistant/RAG workflow.
 */
export async function predictNetwork(networkMetrics, predictionMode = 'network_performance') {
  const response = await fetch(`${API_BASE_URL}/api/predict`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ network_metrics: networkMetrics, prediction_mode: predictionMode }),
  });

  const data = await response.json().catch(() => ({ detail: 'Invalid JSON response from server' }));
  if (!response.ok) {
    const detail = data.detail || data.error || `Prediction failed with HTTP ${response.status}`;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return data;
}

/** Save a user rating for an already displayed assistant response. */
export async function submitFeedback({ response_id, query, final_response, rating, comment, context }) {
  const response = await fetch(`${API_BASE_URL}/api/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ response_id, query, final_response, rating, comment: comment || null, context }),
  });
  const data = await response.json().catch(() => ({ detail: 'Invalid feedback response from server' }));
  if (!response.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail || data));
  }
  return data;
}
