import React, {useEffect, useState} from 'react';
import {ArrowUpRight, Camera, MapPin} from 'lucide-react';
import {api} from '../services/api';
import {Badge, Empty, formatTime, shortId} from './Common';

export const eventLabel = value => ({pothole: 'Pothole', accident: 'Accident', ambulance: 'Ambulance'}[value] || value || 'Incident');

export function EvidenceImage({eventId, alt, className = ''}) {
  const [failed, setFailed] = useState(false), [attempt, setAttempt] = useState(0);
  useEffect(() => {setFailed(false); setAttempt(0)}, [eventId]);
  if (!eventId) return <div className={'photo-placeholder ' + className}><Camera size={24}/><span>No image saved</span></div>;
  if (failed) return <div className={'photo-placeholder ' + className}><Camera size={24}/><span>Image unavailable</span><button className="subtle" onClick={() => {setFailed(false); setAttempt(value => value + 1)}}>Retry image</button></div>;
  return <img className={className} src={api.evidenceUrl(eventId) + (attempt ? `?retry=${attempt}` : '')} alt={alt} loading="lazy" onError={() => setFailed(true)}/>;
}

export function DetectionCard({report, onSelect, compact = false}) {
  const image = report.evidence;
  return <article className={'detection-card ' + (compact ? 'compact' : '')}>
    <div className="detection-photo"><EvidenceImage eventId={report.event_id} alt={`${eventLabel(report.event_type)} detected by ${report.bus_id}`}/><span className="photo-tag">{eventLabel(report.event_type)}</span><span className="photo-confidence">{Math.round(report.confidence * 100)}% confidence</span></div>
    <div className="detection-copy"><div className="detection-title"><strong>{report.bus_id}</strong><Badge value={report.status}/></div>
      <span className="photo-location"><MapPin size={12}/>{report.latitude.toFixed(5)}, {report.longitude.toFixed(5)} · {report.location_source}</span>
      <span>{image.source_name} · {image.video_time.toFixed(2)} s · Frame {image.frame_id}</span>
      <span>{formatTime(report.timestamp)}</span>
      <div className="detection-actions"><button className="text-link" onClick={() => onSelect(report.issue_id)}>Review {shortId(report.issue_id)}<ArrowUpRight size={14}/></button><a href={api.evidenceUrl(report.event_id)} target="_blank" rel="noreferrer">Open image</a></div>
    </div>
  </article>;
}

export default function EvidenceGallery({items = [], onSelect}) {
  if (!items.length) return <Empty>No saved images match this view. New confirmed pothole detections save an image automatically. Older alerts without images remain in the issue list.</Empty>;
  return <div className="detection-grid">{items.map(report => <DetectionCard key={report.event_id} report={report} onSelect={onSelect}/>)}</div>;
}
