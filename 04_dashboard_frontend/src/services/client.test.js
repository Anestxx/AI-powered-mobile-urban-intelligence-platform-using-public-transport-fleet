import test from 'node:test';
import assert from 'node:assert/strict';
import {createApiClient} from './client.js';

test('photo gallery preserves filters, pagination and cancellation', async () => {
  let called;
  const controller = new AbortController();
  const client = createApiClient('/api', async (url, options) => {called = {url, options}; return {ok: true, json: async () => ({items: [{event_id: 'photo-1'}], total: 25})}});
  const result = await client.getEvidence({status: 'resolved', event_type: 'pothole', page: 2, page_size: 12}, controller.signal);
  assert.equal(called.url, '/api/evidence?status=resolved&event_type=pothole&page=2&page_size=12');
  assert.equal(result.items[0].event_id, 'photo-1');
  assert.ok(called.options.signal instanceof AbortSignal);
});

test('review decision includes the expected prior status', async () => {
  let body;
  const client = createApiClient('/api', async (_, options) => {body = JSON.parse(options.body); return {ok: true, json: async () => ({status: 'dismissed'})}});
  await client.updateAlertStatus('ISSUE_1', 'dismissed', 'Shadow', 'open');
  assert.deepEqual(body, {status: 'dismissed', note: 'Shadow', expected_status: 'open'});
});

test('CSV export uses the active filters and handles non-JSON responses', async () => {
  let url;
  const client = createApiClient('/api', async value => {url = value; return {ok: true, text: async () => 'issue_id,status\r\nISSUE_1,open\r\n'}});
  assert.match(await client.exportIssues({status: 'open', date_from: '2026-09-14'}), /ISSUE_1,open/);
  assert.equal(url, '/api/reports/issues.csv?status=open&date_from=2026-09-14');
});

test('CSV export surfaces server limits instead of downloading error JSON', async () => {
  const client = createApiClient('/api', async () => ({ok: false, status: 422, json: async () => ({detail: 'Narrow the date filters'})}));
  await assert.rejects(client.exportIssues({}), /Narrow the date filters/);
});

test('evidence follows a configured backend address', () => {
  assert.equal(createApiClient('http://127.0.0.1:8000/api/').evidenceUrl('event/1'), 'http://127.0.0.1:8000/api/observations/event%2F1/evidence');
});

test('filters and pagination are sent to the backend', async () => {
  let called;
  const client = createApiClient('/api', async (url, options) => {called = {url, options}; return {ok: true, json: async () => ({items: [], total: 0, page: 2, page_size: 10})}});
  const response = await client.getAlerts({status: 'open', priority: '', page: 2, page_size: 10});
  assert.equal(called.url, '/api/alerts?status=open&page=2&page_size=10');
  assert.equal(called.options.credentials, 'include');
  assert.deepEqual(response.items, []);
});

test('failed resolution propagates a backend error', async () => {
  const client = createApiClient('/api', async () => ({ok: false, status: 401, json: async () => ({detail: 'Operator sign-in required'})}));
  await assert.rejects(client.updateAlertStatus('ISSUE_1', 'resolved'), error => error.status === 401 && /sign-in/.test(error.message));
});

test('resolution sends the expected status without changing client records', async () => {
  let body;
  const client = createApiClient('/api', async (_, options) => {body = JSON.parse(options.body); return {ok: true, json: async () => ({status: 'resolved'})}});
  assert.deepEqual(await client.updateAlertStatus('ISSUE_1', 'resolved'), {status: 'resolved'});
  assert.deepEqual(body, {status: 'resolved'});
});

test('network failure gives a useful retry message', async () => {
  const client = createApiClient('/api', async () => {throw new TypeError('Failed to fetch')});
  await assert.rejects(client.getStatistics(), /Cannot reach the backend/);
});

test('resolution notes are sent with the saved status', async () => {
  let body;
  const client = createApiClient('/api', async (_, options) => {body = JSON.parse(options.body); return {ok: true, json: async () => ({status: 'resolved'})}});
  await client.updateAlertStatus('ISSUE_1', 'resolved', 'Reviewer demonstration');
  assert.deepEqual(body, {status: 'resolved', note: 'Reviewer demonstration'});
});

test('an HTML response from a wrong API address is reported clearly', async () => {
  const client = createApiClient('/wrong-address', async () => ({ok: true, json: async () => {throw new SyntaxError('Not JSON')}}));
  await assert.rejects(client.getAlerts(), /invalid JSON response/);
});
