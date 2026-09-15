import React from 'react';
import {api} from '../services/api';
import {Badge, Empty, formatTime, ResourceState, useResource} from '../components/Common';

export default function Buses({onStatus, revision}) {
  const resource = useResource(signal => api.getBuses(signal), [], {onStatus, revision});
  return <section className="panel"><div className="panel-heading"><div><h2>Bus telemetry</h2><p className="muted">Activity comes from heartbeats, including when no potholes are detected.</p></div></div><ResourceState resource={resource}/>{resource.data && (resource.data.items.length ? <div className="table-scroll"><table><thead><tr><th>Bus</th><th>Status</th><th>Last heartbeat (IST)</th><th>Location</th><th>Camera</th><th>AI</th></tr></thead><tbody>{resource.data.items.map(bus => <tr key={bus.bus_id}><td><strong>{bus.bus_id}</strong></td><td><Badge value={bus.online ? 'online' : 'offline'}/></td><td>{formatTime(bus.last_seen)}</td><td>{bus.latitude != null && bus.longitude != null ? <>{bus.latitude.toFixed(5)}, {bus.longitude.toFixed(5)}<small>{bus.location_source}</small></> : 'Location unavailable'}</td><td><Badge value={bus.camera_status}/></td><td><Badge value={bus.ai_status}/></td></tr>)}</tbody></table></div> : <Empty>No buses have sent a heartbeat yet. Start the edge runner or event simulator.</Empty>)}</section>;
}
