import React, {useEffect, useRef, useState} from 'react';
import {AlertCircle, ArrowRight, RefreshCw} from 'lucide-react';

export const shortId = value => value?.replace('ISSUE_', '').slice(0, 10).toUpperCase();
export const formatTime = value => value ? new Intl.DateTimeFormat('en-IN', {dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Kolkata'}).format(new Date(value)) : 'Unavailable';
export function Badge({value}) {return <span className={`badge ${value}`}>{value === 'unknown' ? 'Unknown' : value === 'dismissed' ? 'False detection' : value?.replaceAll('_', ' ')}</span>}
export function Empty({children = 'No issues match these filters.'}) {return <div className="empty-state">{children}</div>}
export function Filters({value, onChange, dates = true}) {return <div className="filters">
  <label>Status<select value={value.status || ''} onChange={event => onChange({...value, status: event.target.value})}><option value="">All statuses</option><option value="open">Open</option><option value="resolved">Resolved</option><option value="dismissed">False detection</option></select></label>
  <label>Priority<select value={value.priority || ''} onChange={event => onChange({...value, priority: event.target.value})}><option value="">All priorities</option>{['low', 'medium', 'high'].map(item => <option key={item} value={item}>{item}</option>)}</select></label>
  <label>Event<select value={value.event_type || ''} onChange={event => onChange({...value, event_type: event.target.value})}><option value="">All events</option><option value="pothole">Pothole</option></select></label>
  {dates && <><label>From<input aria-label="From date" type="date" value={value.date_from || ''} onChange={event => onChange({...value, date_from: event.target.value})}/></label><label>To<input aria-label="To date" type="date" value={value.date_to || ''} onChange={event => onChange({...value, date_to: event.target.value})}/></label></>}
  <button className="subtle" onClick={() => onChange({})}>Clear filters</button>
</div>}
export function IssueTable({issues, onSelect}) {if (!issues.length) return <Empty/>; return <div className="table-scroll"><table><thead><tr>{['Issue', 'Priority', 'Severity', 'Reports', 'Status', 'Last seen (IST)', ''].map((title, index) => <th key={index}>{title}</th>)}</tr></thead><tbody>{issues.map(issue => <tr key={issue.issue_id}><td><button className="text-link" onClick={() => onSelect(issue.issue_id)}>{shortId(issue.issue_id)}</button><small>Pothole · {issue.location_source}</small></td><td><Badge value={issue.priority}/></td><td><Badge value={issue.severity}/></td><td>{issue.report_count}<small>{issue.distinct_bus_count} distinct buses</small></td><td><Badge value={issue.status}/></td><td>{formatTime(issue.last_seen)}</td><td><button className="icon-button" aria-label={`View issue ${shortId(issue.issue_id)}`} onClick={() => onSelect(issue.issue_id)}><ArrowRight size={17}/></button></td></tr>)}</tbody></table></div>}

export function useResource(loader, dependencies, {onStatus, revision, interval = 2000} = {}) {
  const [state, setState] = useState({data: null, loading: true, error: '', updated: null});
  const [retry, setRetry] = useState(0);
  const statusRef = useRef(onStatus);
  statusRef.current = onStatus;
  useEffect(() => {
    let stopped = false, busy = false;
    const controller = new AbortController();
    setState({data: null, loading: true, error: '', updated: null});
    async function load() {
      if (busy) return;
      busy = true;
      try {
        const data = await loader(controller.signal);
        if (!stopped) {const updated = new Date(); setState({data, loading: false, error: '', updated}); statusRef.current?.({updated, error: ''})}
      } catch (error) {
        if (!stopped && error.name !== 'AbortError') {setState(previous => ({...previous, loading: false, error: error.message})); statusRef.current?.({error: error.message})}
      } finally {busy = false}
    }
    load();
    const timer = setInterval(load, interval);
    return () => {stopped = true; controller.abort(); clearInterval(timer)};
  }, [...dependencies, revision, retry]);
  return {...state, retry: () => setRetry(value => value + 1)};
}
export function ResourceState({resource}) {return <>
  {resource.error && <div className="error-banner" role="alert"><AlertCircle size={18}/><div><strong>{resource.data ? 'Updates interrupted — showing last received data.' : 'Unable to load data.'}</strong><span>{resource.error}</span></div><button className="subtle" onClick={resource.retry}><RefreshCw size={15}/> Retry</button></div>}
  {resource.loading && <div className="loading-state" role="status">Loading city intelligence…</div>}
</>}
