import React, { useEffect, useState } from 'react';
import { fetchLocations, fetchMetrics, fetchLocation, fetchLocationTypes } from './api';
import { LocationWithIntensity, MetricPoint, Location } from './types';
import LocationDetails from './components/LocationDetails';
import MapView from './components/MapView';

const App: React.FC = () => {
  const [locations, setLocations] = useState<LocationWithIntensity[]>([]);
  const [selectedId, setSelectedId] = useState<number | undefined>();
  const [metrics, setMetrics] = useState<MetricPoint[]>([]);
  const [visibleIds, setVisibleIds] = useState<number[]>([]);
  const [availableTypes, setAvailableTypes] = useState<string[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [perLocationMetrics, setPerLocationMetrics] = useState<Record<number, MetricPoint[]>>({});
  const [selectedName, setSelectedName] = useState<string>('');
  const [snapshot, setSnapshot] = useState<string>('');
  const [snapshotOffset, setSnapshotOffset] = useState<number>(0); // hours ago

  // compute a Date for the current snapshot (or now) and a friendly UTC label
  const snapshotDate = snapshot ? new Date(snapshot) : new Date();
  const snapshotLabelHours = String(snapshotDate.getUTCHours()).padStart(2, '0');
  const snapshotLabelDate = snapshotDate.toISOString().slice(0, 10);
  const hAgo = snapshotOffset;
  const days = Math.floor(hAgo / 24);
  const hours = hAgo % 24;
  const agoLabel = hAgo === 0 ? 'now' : (days > 0 ? `${days}d ${hours}h ago` : `${hours}h ago`);
  const snapshotLabel = `${snapshotLabelHours}:00 UTC — ${snapshotLabelDate} (${agoLabel})`;

  // Load locations
  useEffect(() => {
    fetchLocations(snapshot).then(setLocations).catch(console.error);
    const interval = setInterval(() => fetchLocations(snapshot).then(setLocations).catch(console.error), 15000);
    return () => clearInterval(interval);
  }, [snapshot]);

  // Load available types once
  useEffect(() => {
    import('./api').then(mod => mod.fetchLocationTypes()).then(setAvailableTypes).catch(console.error);
  }, []);

  // Load metrics for selected; re-run when selectedId OR visibleIds changes so we fetch
  // metrics when a selected location becomes visible after a pan/zoom.
  useEffect(() => {
    if (selectedId != null) {
      fetchLocation(selectedId).then(l => setSelectedName(l.name));
      // Only show/fetch metrics if the selected location is visible AND its type is selected
      const selLoc = locations.find(l => l.id === selectedId);
      if (selLoc && visibleIds.includes(selectedId) && selectedTypes.includes(selLoc.type)) {
        // Prefer cached per-location metrics if available
        const cached = perLocationMetrics[selectedId];
        if (cached) setMetrics(cached);
        else fetchMetrics(selectedId, 24).then(setMetrics).catch(console.error);
      } else {
        // Clear metrics when selection is not visible or its type not selected
        setMetrics([]);
      }
    }
  }, [selectedId, visibleIds]);

  // Whenever visibleIds or selectedTypes change, fetch metrics for each visible location that matches selected types.
  useEffect(() => {
    // If no types selected, nothing to fetch and clear cache
    if (selectedTypes.length === 0) {
      setPerLocationMetrics({});
      setMetrics([]);
      return;
    }

    // compute visible locations that match the selected types
    const visibleLocations = locations.filter(l => visibleIds.includes(l.id) && selectedTypes.includes(l.type));

    // Build a set for quick lookup
    const wantedIds = new Set(visibleLocations.map(l => l.id));

    // Remove cached metrics for locations that are no longer wanted
    setPerLocationMetrics(prev => {
      const copy: Record<number, MetricPoint[]> = { ...prev };
      for (const idStr of Object.keys(copy)) {
        const id = Number(idStr);
        if (!wantedIds.has(id)) {
          delete copy[id];
        }
      }
      return copy;
    });

    // Fetch metrics for each wanted location (if not already cached)
    visibleLocations.forEach(loc => {
      // Use functional state read to avoid stale closure over perLocationMetrics
      setPerLocationMetrics(prev => {
        if (prev[loc.id]) return prev; // already have it
        // Kick off async fetch and optimistically return prev; fetched result will update state
        fetchMetrics(loc.id, 24).then(data => {
          setPerLocationMetrics(p => ({ ...p, [loc.id]: data }));
        }).catch(err => {
          console.error('failed to fetch metrics for location', loc.id, err);
        });
        return prev;
      });
    });
  }, [visibleIds, selectedTypes, locations]);

  return (
    <div className="layout">
      <div className="sidebar">
        <h1>Sydney Live Map</h1>
        <label>Time (UTC Hour Offset)</label>
        <div className="time-row">
          <input type="range" min={0} max={168} value={snapshotOffset} onChange={e => {
            const offset = parseInt(e.target.value);
            setSnapshotOffset(offset);
            const now = Date.now();
            const snap = new Date(now - offset * 60 * 60 * 1000);
            setSnapshot(snap.toISOString());
          }} />
          <div className="time-display">{snapshotLabel}</div>
        </div>
        {/* chart is rendered inside LocationDetails when a location is selected */}

        <div className="list">
          <div style={{ marginBottom: 8 }}>
            <strong>Filter types</strong>
            <div>
              {availableTypes.map(t => (
                <label key={t} style={{ display: 'inline-block', marginRight: 8 }}>
                  <input
                    type="checkbox"
                    checked={selectedTypes.includes(t)}
                    onChange={e => {
                      if (e.target.checked) setSelectedTypes(prev => [...prev, t]);
                      else setSelectedTypes(prev => prev.filter(x => x !== t));
                    }}
                  /> {t}
                </label>
              ))}
            </div>
          </div>
          {locations.map(l => (
            <div key={l.id} className={`list-item ${l.id === selectedId ? 'active' : ''}`} onClick={() => setSelectedId(l.id)}>
              <span>{l.name}</span>
              <span className="pill">{(l.intensity * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
        {selectedId && <LocationDetails name={selectedName} metrics={metrics} />}
      </div>
      <div className="map-container">
        {/* Only pass locations that match selected types. If none selected, pass empty array so no markers render. */}
        { /* compute filtered list here to keep MapView simple */ }
        <MapView
          locations={selectedTypes.length === 0 ? [] : locations.filter(l => selectedTypes.includes(l.type))}
          onSelect={(id) => setSelectedId(id)}
          selectedId={selectedId}
          onVisibleChange={setVisibleIds}
        />
      </div>
    </div>
  );
};

export default App;
