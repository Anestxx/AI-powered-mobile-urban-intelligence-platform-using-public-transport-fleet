import React, {useState} from 'react';
import {api} from '../services/api';
import {Filters, IssueTable, ResourceState, useResource} from '../components/Common';
import EvidenceGallery from '../components/EvidenceGallery';

export default function Alerts({onSelect, onStatus, revision}) {
  const [filters, setFilters] = useState({}), [page, setPage] = useState(1);
  const [view, setView] = useState('images');
  const pageSize = 12;
  const [exporting, setExporting] = useState(false), [exportError, setExportError] = useState('');
  const resource = useResource(signal => (view === 'images' ? api.getEvidence : api.getAlerts)({...filters, page, page_size: pageSize}, signal), [JSON.stringify(filters), page, view], {onStatus, revision});
  async function exportCsv() {
    setExporting(true); setExportError('');
    try {
      const csv = await api.exportIssues(filters);
      const url = URL.createObjectURL(new Blob([csv], {type: 'text/csv;charset=utf-8'}));
      const link = document.createElement('a');
      link.href = url; link.download = 'codyssey-issues.csv';
      document.body.appendChild(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {setExportError(error.message)} finally {setExporting(false)}
  }
  return <section className="panel">
    <div className="panel-heading"><div><span className="eyebrow">INCIDENTS</span><h2>Detection evidence</h2></div><div className="view-switch" aria-label="Incident view">{[['images', 'Photo gallery'], ['issues', 'Issue list']].map(([key, label]) => <button key={key} className={view === key ? 'active' : ''} aria-pressed={view === key} onClick={() => {setView(key); setPage(1)}}>{label}</button>)}</div><button className="subtle" disabled={exporting} onClick={exportCsv}>{exporting ? 'Exporting…' : 'Download issues CSV'}</button></div>
    <p className="gallery-note">Pothole detection is enabled. Accident and emergency detection await labeled data and validated models. Each image is an observation; nearby reports may share one issue.</p>
    <Filters value={filters} onChange={value => {setFilters(value); setPage(1)}}/>
    {exportError && <div className="error-banner" role="alert">{exportError}</div>}
    <ResourceState resource={resource}/>
    {resource.data && <>{view === 'images' ? <EvidenceGallery items={resource.data.items} onSelect={onSelect}/> : <IssueTable issues={resource.data.items} onSelect={onSelect}/>}<div className="pagination"><span>{resource.data.total} {view === 'images' ? 'saved images' : 'issues'} · Page {page} of {Math.max(1, Math.ceil(resource.data.total / pageSize))}</span><div><button className="subtle" disabled={page === 1} onClick={() => setPage(value => value - 1)}>Previous</button><button className="subtle" disabled={page * pageSize >= resource.data.total} onClick={() => setPage(value => value + 1)}>Next</button></div></div></>}
  </section>;
}
