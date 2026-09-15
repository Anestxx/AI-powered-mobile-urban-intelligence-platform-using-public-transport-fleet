import React, {useState} from 'react';
import {getMapIssues} from '../services/api';
import MapView from '../components/MapView';
import {Filters, ResourceState, useResource} from '../components/Common';

export default function CityMap({onSelect, onStatus, revision}) {
  const [filters, setFilters] = useState({status: 'open'});
  const resource = useResource(signal => getMapIssues(filters, signal), [JSON.stringify(filters)], {onStatus, revision});
  return <section className="panel"><Filters value={filters} onChange={setFilters}/><ResourceState resource={resource}/><MapView large issues={resource.data?.items} onSelect={onSelect}/><p className="map-caption">Showing {resource.data?.items.length ?? 0} of {resource.data?.total ?? 0} matching issues{resource.data?.total > 500 ? ' (latest 500; narrow filters to inspect more)' : ''}. Locations are approximate bus observation positions. Source is labeled in each popup.</p></section>;
}
