import React, {useEffect} from 'react';
import {CircleMarker, MapContainer, Popup, TileLayer, useMap} from 'react-leaflet';
import {Badge, shortId} from './Common';
import {EvidenceImage, eventLabel} from './EvidenceGallery';

const center = [12.9716, 77.5946];
const colors = {high: '#ff6c83', medium: '#f5bd62', low: '#5cc9ff', resolved: '#8c98ae', dismissed: '#a18bbd'};
function Viewport({focus}) {const map = useMap(); const lat = focus?.[0], lng = focus?.[1]; useEffect(() => {if (lat != null && lng != null) map.setView([lat, lng], 15)}, [map, lat, lng]); return null}
export default function MapView({issues = [], buses = [], onSelect, focus, large = false}) {return <div className={`map-frame ${large ? 'large' : ''}`}>
  <MapContainer center={focus || center} zoom={12} scrollWheelZoom className="city-map"><TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
    {issues.filter(issue => Number.isFinite(issue.latitude) && Number.isFinite(issue.longitude)).slice().reverse().map(issue => <CircleMarker key={issue.issue_id} center={[issue.latitude, issue.longitude]} radius={9} pathOptions={{color: colors[issue.status === 'open' ? issue.priority : issue.status], fillOpacity: .65, weight: 2}}><Popup minWidth={230}><div className="map-popup"><strong>{eventLabel(issue.event_type)} · {shortId(issue.issue_id)}</strong><EvidenceImage eventId={issue.latest_evidence?.event_id} className="map-evidence" alt={`${eventLabel(issue.event_type)} at this location`}/>{issue.latest_evidence && <span>{Math.round(issue.latest_evidence.confidence * 100)}% confidence · {issue.latest_evidence.bus_id}</span>}<p>{issue.latitude.toFixed(5)}, {issue.longitude.toFixed(5)}<br/>Priority: {issue.priority}<br/>Reports: {issue.report_count} · {issue.evidence_count || 0} saved images<br/>Location: {issue.location_source}</p><Badge value={issue.status}/>{onSelect && <button onClick={() => onSelect(issue.issue_id)}>View images and review</button>}</div></Popup></CircleMarker>)}
    {buses.filter(bus => Number.isFinite(bus.latitude) && Number.isFinite(bus.longitude)).map(bus => <CircleMarker key={`bus-${bus.bus_id}`} center={[bus.latitude, bus.longitude]} radius={5} pathOptions={{color: bus.online ? '#72f1a8' : '#8c98ae', fillOpacity: 1, weight: 2}}><Popup><div className="map-popup"><strong>{bus.bus_id}</strong><p>{bus.online ? 'Online' : 'Offline'} · {bus.location_source}<br/>Camera: {bus.camera_status}<br/>AI: {bus.ai_status}</p></div></Popup></CircleMarker>)}
    <Viewport focus={focus}/>
  </MapContainer>
  <div className="map-legend">{Object.entries(colors).map(([name, color]) => <span key={name}><i style={{background: color}}/>{name}</span>)}</div>
</div>}
