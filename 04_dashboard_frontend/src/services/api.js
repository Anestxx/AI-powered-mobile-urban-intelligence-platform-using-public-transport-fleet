import {createApiClient} from './client';
import {mockApi} from '../mocks/mockData';

export const isMock = import.meta.env.VITE_USE_MOCKS === 'true';
export const api = isMock ? mockApi : createApiClient(import.meta.env.VITE_API_BASE_URL || '/api');

export async function getMapIssues(filters, signal) {
  const first = await api.getAlerts({...filters, page: 1, page_size: 100}, signal);
  const items = [...first.items];
  // Keep the map responsive and state the displayed coverage explicitly.
  const pages = Math.min(5, Math.ceil(first.total / 100));
  for (let page = 2; page <= pages; page++) {
    const result = await api.getAlerts({...filters, page, page_size: 100}, signal);
    items.push(...result.items);
  }
  return {items: [...new Map(items.map(item => [item.issue_id, item])).values()], total: first.total};
}
