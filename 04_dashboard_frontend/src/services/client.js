export function createApiClient(baseUrl = '/api', fetcher = (...args) => fetch(...args)) {
  async function request(path, {signal, responseType = 'json', ...options} = {}) {
    const controller = new AbortController();
    const abort = () => controller.abort();
    if (signal?.aborted) controller.abort();
    signal?.addEventListener('abort', abort, {once: true});
    const timeout = setTimeout(abort, 10000);
    try {
      const response = await fetcher(`${baseUrl.replace(/\/$/, '')}${path}`, {
        credentials: 'include', ...options, signal: controller.signal,
        headers: {'Content-Type': 'application/json', ...options.headers},
      });
      if (response.ok && responseType === 'text') return await response.text();
      const data = await response.json().catch(() => {if (response.ok) throw new Error('The backend returned an invalid JSON response. Check the API address.'); return {}});
      if (!response.ok) {
        const detail = typeof data.detail === 'string' ? data.detail : 'The request could not be completed.';
        const error = new Error(detail);
        error.status = response.status;
        throw error;
      }
      return data;
    } catch (error) {
      if (error.name === 'AbortError' && !signal?.aborted) throw new Error('The backend took too long to respond. Please retry.');
      if (error instanceof TypeError) throw new Error('Cannot reach the backend. Check that it is running, then retry.');
      throw error;
    } finally {
      clearTimeout(timeout);
      signal?.removeEventListener('abort', abort);
    }
  }
  const query = filters => {
    const params = new URLSearchParams();
    Object.entries(filters || {}).forEach(([key, value]) => {if (value !== '' && value != null) params.set(key, value)});
    return params.size ? `?${params}` : '';
  };
  return {
    getStatistics: signal => request('/statistics', {signal}),
    getAlerts: (filters, signal) => request(`/alerts${query(filters)}`, {signal}),
    getEvidence: (filters, signal) => request(`/evidence${query(filters)}`, {signal}),
    getAlertDetails: (id, signal) => request(`/alerts/${encodeURIComponent(id)}`, {signal}),
    updateAlertStatus: (id, status, note = '', expectedStatus) => request(`/alerts/${encodeURIComponent(id)}/status`, {method: 'PATCH', body: JSON.stringify({status, ...(note ? {note} : {}), ...(expectedStatus ? {expected_status: expectedStatus} : {})})}),
    evidenceUrl: eventId => `${baseUrl.replace(/\/$/, '')}/observations/${encodeURIComponent(eventId)}/evidence`,
    exportIssues: (filters, signal) => request(`/reports/issues.csv${query(filters)}`, {signal, responseType: 'text'}),
    getBuses: signal => request('/buses', {signal}),
    getAnalytics: (filters, signal) => request(`/analytics${query(filters)}`, {signal}),
    getSession: () => request('/auth/session'),
    login: password => request('/auth/login', {method: 'POST', body: JSON.stringify({password})}),
    logout: () => request('/auth/logout', {method: 'POST'}),
  };
}
