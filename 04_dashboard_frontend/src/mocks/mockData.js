import fixture from '../../../contracts/fixtures/demo.json';

const state = structuredClone(fixture);
let signedIn = false;
const copy = value => structuredClone(value);
const matches = (issue, filters = {}) => Object.entries(filters).every(([key, value]) => {
  if (!value || ['page', 'page_size'].includes(key)) return true;
  const date = new Date(issue.last_seen).toLocaleDateString('en-CA', {timeZone: 'Asia/Kolkata'});
  if (key === 'date_from') return date >= value;
  if (key === 'date_to') return date <= value;
  return issue[key] === value;
});
const priorities = () => Object.fromEntries(['low', 'medium', 'high'].map(priority => [priority, state.issues.items.filter(issue => issue.status === 'open' && issue.priority === priority).length]));

export const mockApi = {
  async getEvidence(filters = {}) {return {items: [], total: 0, page: Number(filters.page || 1), page_size: Number(filters.page_size || 12)}},
  async getAlerts(filters = {}) {const items = state.issues.items.filter(issue => matches(issue, filters)); const page = Number(filters.page || 1), size = Number(filters.page_size || 20); return copy({items: items.slice((page - 1) * size, page * size), total: items.length, page, page_size: size})},
  async getAlertDetails(id) {const issue = state.issues.items.find(value => value.issue_id === id); if (!issue) throw new Error('Issue not found'); return copy({...issue, observations: state.observations.filter((_, index) => id === 'ISSUE_DEMO_NEARBY' ? index < 2 : index === 2).map(observation => ({...observation, issue_id: id, received_at: observation.timestamp}))})},
  async getStatistics() {return {open_issues: state.issues.items.filter(value => value.status === 'open').length, dismissed_issues: state.issues.items.filter(value => value.status === 'dismissed').length, total_issues: state.issues.total, new_issues_today: state.issues.items.filter(value => new Date(value.first_seen).toLocaleDateString('en-CA', {timeZone: 'Asia/Kolkata'}) === new Date().toLocaleDateString('en-CA', {timeZone: 'Asia/Kolkata'})).length, open_high_priority_issues: priorities().high, resolved_issues: state.issues.items.filter(value => value.status === 'resolved').length, active_buses: state.buses.items.filter(value => value.online).length, open_by_priority: priorities()}},
  evidenceUrl: id => '/api/observations/' + encodeURIComponent(id) + '/evidence',
  async exportIssues(filters = {}) {
    const fields = ['issue_id', 'event_type', 'status', 'priority', 'severity', 'latitude', 'longitude', 'location_source', 'report_count', 'distinct_bus_count', 'first_seen', 'last_seen'];
    const cell = value => '"' + String(value ?? '').replaceAll('"', '""') + '"';
    return [fields.map(cell).join(','), ...state.issues.items.filter(issue => matches(issue, filters)).map(issue => fields.map(key => cell(issue[key])).join(','))].join('\r\n');
  },
  async getBuses() {return copy(state.buses)},
  async updateAlertStatus(id, status, note = '', expectedStatus) {if (!signedIn) throw new Error('Operator sign-in required'); const issue = state.issues.items.find(value => value.issue_id === id); if (!issue) throw new Error('Issue not found'); if (!['open','resolved','dismissed'].includes(status)) throw new Error('Invalid status'); if (status === 'dismissed' && !note.trim()) throw new Error('A reason is required'); if (expectedStatus && issue.status !== expectedStatus && issue.status !== status) throw new Error('Issue changed. Refresh before updating.'); if (issue.status !== status) {issue.activity = [{activity_id: crypto.randomUUID(), issue_id: id, previous_status: issue.status, status, note: note.trim(), actor: 'demo_operator', timestamp: new Date().toISOString()}, ...(issue.activity || [])]; issue.status = status} return copy(issue)},
  async getAnalytics() {return {date_from: '2026-09-13', date_to: '2026-09-13', timezone: 'Asia/Kolkata', new_issues_by_day: [{date: '2026-09-13', count: 2}], open_by_priority: priorities(), observations_by_bus: state.observations.map(value => ({bus_id: value.bus_id, count: 1}))}},
  async getSession() {return {authenticated: signedIn}},
  async login() {signedIn = true; return {authenticated: true}},
  async logout() {signedIn = false; return {authenticated: false}},
};
