import React from 'react';
import { Ambulance, CheckCircle2, CircleDot } from 'lucide-react';
import { api } from '../services/api';
import { ResourceState, useResource } from '../components/Common';
export default function Emergency({
  onStatus,
  revision
}) {
  const resource = useResource(signal => api.getStatistics(signal), [], {
    onStatus,
    revision
  });
  return <><ResourceState resource={resource} /><section className="panel module-panel emergency-panel"><Ambulance size={34} /><span className="eyebrow">EMERGENCY RESPONSE · PROTOTYPE MODULE</span><h2>Ambulance checkpoint received</h2><p>The latest pull includes ambulance.pt with a named ambulance class. Its detection accuracy and connection to shared alerts still need verification. The older emergency.pt contains general objects.</p><div className="module-check"><CheckCircle2 size={18} /><div><strong>Assets preserved</strong><p>All five model files and both recordings are kept with their original names.</p></div></div><div className="module-check"><CircleDot size={18} /><div><strong>Emergency recognition pending</strong><p>The ambulance class is verified. Evaluation on representative footage and integration with the shared alert pipeline are still pending; no accident detector is configured.</p></div></div><div className="info-card"><strong>Signal priority is a future demonstration</strong><p>No traffic signals or emergency services are connected. A corridor drawn from simulated coordinates would be an illustration.</p></div></section></>;
}
