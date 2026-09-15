import React, {useState} from 'react';
import {api, isMock} from '../services/api';
import {Empty, ResourceState, useResource} from '../components/Common';

function Bars({items, labelKey}) {const max = Math.max(1, ...items.map(item => item.count)); return items.length ? <div className="bar-chart">{items.map(item => <div className="bar-row" key={item[labelKey]}><span>{item[labelKey]}</span><div className="bar-track"><i style={{width: `${item.count / max * 100}%`}}/></div><strong>{item.count}</strong></div>)}</div> : <Empty>No records for this period.</Empty>}
export default function Analytics({onStatus, revision}) {
  const [dates, setDates] = useState({});
  const resource = useResource(signal => api.getAnalytics(dates, signal), [JSON.stringify(dates)], {onStatus, revision});
  const data = resource.data;
  return <><section className="panel filters"><label>From<input type="date" aria-label="Analytics from date" value={dates.date_from || ''} disabled={isMock} onChange={event => setDates({...dates, date_from: event.target.value})}/></label><label>To<input type="date" aria-label="Analytics to date" value={dates.date_to || ''} disabled={isMock} onChange={event => setDates({...dates, date_to: event.target.value})}/></label><button className="subtle" onClick={() => setDates({})}>Last 7 days</button><span className="muted">{isMock ? 'Historical fixture analytics' : 'Calendar dates in Asia/Kolkata'}</span></section><ResourceState resource={resource}/>{data && <><section className="panel chart-panel"><h2>New issues by day</h2><p className="muted">{data.date_from} to {data.date_to}</p><Bars items={data.new_issues_by_day} labelKey="date"/></section><div className="detail-grid"><section className="panel chart-panel"><h2>Current open issues by priority</h2><Bars items={Object.entries(data.open_by_priority).map(([priority, count]) => ({priority, count}))} labelKey="priority"/></section><section className="panel chart-panel"><h2>Observations by bus</h2><Bars items={data.observations_by_bus} labelKey="bus_id"/></section></div></>}</>;
}
