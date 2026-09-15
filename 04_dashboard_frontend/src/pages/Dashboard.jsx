import React, { useState } from 'react';
import { AlertTriangle, Ambulance, ArrowUpRight, BusFront, CheckCircle2, CircleDot, Zap } from 'lucide-react';
import { api } from '../services/api';
import MapView from '../components/MapView';
import { Badge, ResourceState, useResource } from '../components/Common';
import EvidenceGallery, {DetectionCard} from '../components/EvidenceGallery';
export default function Dashboard({
  onSelect,
  onStatus,
  revision,
  onNavigate
}) {
  const [showBuses, setShowBuses] = useState(true);
  const resource = useResource(async signal => {
    const [statistics, issues, buses, evidence] = await Promise.all([api.getStatistics(signal), api.getAlerts({
      page_size: 8
    }, signal), api.getBuses(signal), api.getEvidence({page_size: 8}, signal)]);
    return {
      statistics,
      issues,
      buses,
      evidence
    };
  }, [], {
    onStatus,
    revision
  });
  const stats = resource.data?.statistics,
    fleet = resource.data?.buses.items || [];
  const cards = [['Open issues', stats ? (stats.open_issues ?? (stats.total_issues - stats.resolved_issues - (stats.dismissed_issues || 0))) : null, AlertTriangle, 'Awaiting operator review', 'pink'], ['Sensing fleet', stats?.active_buses, BusFront, 'Online from recent heartbeats', 'cyan'], ['High review priority', stats?.open_high_priority_issues, CircleDot, 'Confirmed by distinct buses', 'amber'], ['Resolved issues', stats?.resolved_issues, CheckCircle2, 'Reports and history preserved', 'green']];
  return <><ResourceState resource={resource} />
    <div className="stats-grid">{cards.map(([label, value, Icon, detail, tone]) => <div className={'stat-card ' + tone} key={label}><div className="stat-icon"><Icon size={18} /></div><div className="stat-copy"><span>{label}</span><strong>{value ?? '—'}</strong><small>{detail}</small></div><ArrowUpRight size={16} className="stat-arrow" /></div>)}</div>
    <div className="workspace"><section className="map-card"><div className="panel-heading"><div><span className="eyebrow">CITY PULSE</span><h2>Recent issue locations</h2></div><span className="muted">Latest {resource.data?.issues.items.length ?? 0} issues</span></div><MapView issues={resource.data?.issues.items} buses={showBuses ? fleet : []} onSelect={onSelect} /><div className="map-footer"><div className="map-metric"><span>New issues today</span><strong>{stats?.new_issues_today ?? '—'}</strong></div><div className="map-metric"><span>Total saved issues</span><strong>{stats?.total_issues ?? '—'}</strong></div><button className={'toggle ' + (showBuses ? 'on' : '')} aria-pressed={showBuses} onClick={() => setShowBuses(!showBuses)}><span />Show fleet</button></div></section>
      <aside className="right-rail"><section className="panel latest-capture"><div className="panel-heading"><div><span className="eyebrow">LATEST CAPTURE</span><h3>Detection from the road</h3></div><Badge value="pothole"/></div>{resource.data?.evidence.items[0] ? <DetectionCard compact report={resource.data.evidence.items[0]} onSelect={onSelect}/> : <p className="module-note">Waiting for a confirmed detection with a saved image.</p>}</section>
        <section className="panel fleet-panel"><div className="panel-head"><div><span className="eyebrow">FLEET STATUS</span><h3>Mobile sensors</h3></div><Badge value={(stats?.active_buses ?? '—') + ' online'} /></div><div className="fleet-list">{fleet.length ? fleet.slice(0, 4).map(bus => <button className="fleet-row" key={bus.bus_id} onClick={() => onNavigate('buses')}><div className="bus-icon"><BusFront size={16} /></div><div className="fleet-main"><strong>{bus.bus_id}</strong><span>{bus.location_source || 'Location unavailable'}</span></div><Badge value={bus.online ? 'online' : 'offline'} /></button>) : <p className="module-note">No buses have sent a heartbeat yet.</p>}</div></section>
        <section className="panel insight-panel"><div className="insight-icon"><Zap size={17} /></div><div><span className="eyebrow">REVIEW PRIORITY</span><p>One bus: low. Two: medium. Three or more: high. <strong>Physical severity remains unassessed.</strong></p></div></section>
      </aside>
    </div>
    <section className="panel events-panel"><div className="panel-heading"><div><span className="eyebrow">INCIDENT PHOTO STREAM</span><h2>See what the fleet detected</h2></div><button className="subtle" onClick={() => onNavigate('alerts')}>All {resource.data?.evidence.total ?? 0} images<ArrowUpRight size={14} /></button></div><p className="gallery-note">Saved images update every two seconds. Select a report to inspect its map location, evidence and resolution history.</p>{resource.data && <EvidenceGallery items={resource.data.evidence.items} onSelect={onSelect}/>}</section>
    <section className="panel detector-status"><Ambulance size={22}/><div><strong>More incident types</strong><p>Accident and emergency detection need labeled examples and validated weights. The current detector reports potholes.</p></div><button className="subtle" onClick={() => onNavigate('emergency')}>Model status<ArrowUpRight size={14}/></button></section>
  </>;
}
