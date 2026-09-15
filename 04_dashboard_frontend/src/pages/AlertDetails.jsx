import React, {useEffect, useState} from 'react';
import {ArrowLeft, CheckCircle2, RotateCcw, XCircle} from 'lucide-react';
import {api} from '../services/api';
import MapView from '../components/MapView';
import {EvidenceImage, eventLabel} from '../components/EvidenceGallery';
import {Badge, formatTime, ResourceState, shortId, useResource} from '../components/Common';

function EvidenceCard({report}) {
  const evidence = report.evidence;
  return <figure className="evidence-card">
    <EvidenceImage eventId={report.event_id} alt={`Saved ${eventLabel(report.event_type)} image from ${report.bus_id}`}/>
    <figcaption><strong>{report.bus_id} · {(report.confidence * 100).toFixed(1)}%</strong><span>{evidence.source_name} · Frame {evidence.frame_id} · {evidence.video_time.toFixed(2)} s</span><span>{formatTime(report.timestamp)} · {Math.ceil(evidence.byte_count / 1024)} KiB</span><a className="text-link" href={api.evidenceUrl(report.event_id)} target="_blank" rel="noreferrer">Open image</a></figcaption>
  </figure>;
}

export default function AlertDetails({issueId, onBack, onStatus, revision, authenticated, onLogin, onChanged, onSessionExpired}) {
  const resource = useResource(signal => api.getAlertDetails(issueId, signal), [issueId], {onStatus, revision});
  const [confirm, setConfirm] = useState(null), [saving, setSaving] = useState(false), [error, setError] = useState('');
  const [note, setNote] = useState('');
  useEffect(() => {setConfirm(null); setError(''); setNote('')}, [issueId]);
  const issue = resource.data;
  const actionNames = {resolved: 'Mark resolved', dismissed: 'Mark false detection', open: 'Reopen issue'};
  function choose(status) {
    if (!authenticated) {onLogin(); return}
    setConfirm({status, expected: issue.status}); setNote(''); setError('');
  }
  async function save() {
    if (confirm.status === 'dismissed' && !note.trim()) {setError('Enter a reason for marking this a false detection.'); return}
    setSaving(true); setError('');
    try {await api.updateAlertStatus(issueId, confirm.status, note.trim(), confirm.expected); setConfirm(null); setNote(''); onChanged()}
    catch (error) {setError(error.message); if (error.status === 401) {setConfirm(null); onSessionExpired()}}
    finally {setSaving(false)}
  }
  const evidence = issue?.observations.filter(report => report.evidence) || [];
  return <>
    <button className="subtle back-link" onClick={onBack}><ArrowLeft size={16}/> Back to issues</button>
    <ResourceState resource={resource}/>
    {issue && <>
      <section className="panel detail-header"><div><span className="eyebrow">{issue.issue_id}</span><h2>Pothole · {shortId(issue.issue_id)}</h2><div className="badge-row"><Badge value={issue.status}/><Badge value={issue.priority}/><Badge value={issue.severity}/></div></div>
        <div className="review-actions">{issue.status === 'open' ? <>
          <button className="primary-button" disabled={saving} onClick={() => choose('resolved')}><CheckCircle2 size={17}/>{authenticated ? 'Mark resolved' : 'Sign in to resolve'}</button>
          <button className="subtle" disabled={saving} onClick={() => choose('dismissed')}><XCircle size={16}/> False detection</button>
        </> : <button className="subtle" disabled={saving} onClick={() => choose('open')}><RotateCcw size={16}/> Reopen issue</button>}</div>
      </section>
      {confirm && <div className="confirm-box" role="alertdialog" aria-label="Confirm review decision"><strong>{actionNames[confirm.status]}?</strong><p>{confirm.status === 'dismissed' ? 'This records an incorrect detection separately from resolved issues. Give a reason so the decision can be reviewed.' : 'Observations and saved evidence will be preserved. Both dashboards will show the saved status.'}</p><label className="resolution-note">{confirm.status === 'dismissed' ? 'Reason (required)' : 'Review note (optional)'}<textarea value={note} onChange={event => setNote(event.target.value)} maxLength={500} rows={2} disabled={saving} placeholder="Record what was reviewed or done."/></label><button className="primary-button" disabled={saving || (confirm.status === 'dismissed' && !note.trim())} onClick={save}>{saving ? 'Saving…' : 'Confirm decision'}</button><button className="subtle" disabled={saving} onClick={() => setConfirm(null)}>Cancel</button></div>}
      {error && <div className="error-banner" role="alert">{error}</div>}
      <section className="panel"><div className="panel-heading"><div><span className="eyebrow">DETECTION EVIDENCE</span><h2>Saved detection images</h2></div><span className="muted">{evidence.length} saved images</span></div>{evidence.length ? <div className="evidence-grid">{evidence.map(report => <EvidenceCard key={report.event_id} report={report}/>)}</div> : <div className="empty-state">No image was saved with these observations. Earlier metadata-only alerts retain their original reports.</div>}</section>
      <div className="detail-grid"><section className="panel"><MapView issues={[issue]} focus={[issue.latitude, issue.longitude]}/></section><section className="panel detail-facts"><h2>Issue record</h2><dl><dt>Coordinates</dt><dd>{issue.latitude.toFixed(6)}, {issue.longitude.toFixed(6)}</dd><dt>Location source</dt><dd>{issue.location_source} · approximate bus position</dd><dt>First seen</dt><dd>{formatTime(issue.first_seen)}</dd><dt>Last seen</dt><dd>{formatTime(issue.last_seen)}</dd><dt>Reports</dt><dd>{issue.report_count} observations · {issue.distinct_bus_count} distinct buses</dd><dt>Priority explanation</dt><dd>{issue.priority_reason}</dd><dt>Severity</dt><dd>Unknown — no physical damage assessment</dd></dl></section></div>
      <section className="panel"><div className="panel-heading"><h2>Individual observations</h2><span className="muted">Confidence belongs to each report</span></div><div className="table-scroll"><table><thead><tr><th>Event ID</th><th>Bus</th><th>Confidence</th><th>Detection time (IST)</th><th>Source</th></tr></thead><tbody>{issue.observations.map(report => <tr key={report.event_id}><td title={report.event_id}>{report.event_id.slice(0, 12)}</td><td>{report.bus_id}</td><td>{(report.confidence * 100).toFixed(1)}%</td><td>{formatTime(report.timestamp)}</td><td>{report.location_source}</td></tr>)}</tbody></table></div></section>
      <section className="panel"><div className="panel-heading"><h2>Status history</h2><span className="muted">Saved operator actions</span></div>{issue.activity?.length ? <div className="table-scroll"><table><thead><tr><th>When (IST)</th><th>Change</th><th>Operator</th><th>Note</th></tr></thead><tbody>{issue.activity.map(activity => <tr key={activity.activity_id}><td>{formatTime(activity.timestamp)}</td><td>{activity.previous_status} → {activity.status}</td><td>{activity.actor.replaceAll('_', ' ')}</td><td className="activity-note">{activity.note || 'No note supplied'}</td></tr>)}</tbody></table></div> : <div className="empty-state">No status changes have been recorded for this issue.</div>}</section>
    </>}
  </>;
}
