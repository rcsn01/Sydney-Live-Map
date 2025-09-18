import React, { useEffect, useState } from 'react';
import { fetchLocations, fetchMetrics, fetchLocation } from './api';
import { LocationWithIntensity, MetricPoint, Location } from './types';
import MapView from './components/MapView';
import LocationDetails from './components/LocationDetails';

const App: React.FC = () => {
  const [locations, setLocations] = useState<LocationWithIntensity[]>([]);
  const [selectedId, setSelectedId] = useState<number | undefined>();
  const [metrics, setMetrics] = useState<MetricPoint[]>([]);
  const [selectedName, setSelectedName] = useState<string>('');
  const [snapshot, setSnapshot] = useState<string>('');
  const [snapshotOffset, setSnapshotOffset] = useState<number>(0); // hours ago
  const nowUtc = new Date();
  const MIN_YEAR = 2015;
  const MAX_YEAR = nowUtc.getUTCFullYear();
  const [year, setYear] = useState<number>(nowUtc.getUTCFullYear());
  const dayOfYearFromDate = (d: Date) => {
    const start = Date.UTC(d.getUTCFullYear(), 0, 1);
    return Math.floor((d.getTime() - start) / (24 * 60 * 60 * 1000)) + 1;
  };
  const dateFromYearDay = (y: number, day: number) => new Date(Date.UTC(y, 0, 1) + (day - 1) * 24 * 60 * 60 * 1000);
  const [dayOfYear, setDayOfYear] = useState<number>(dayOfYearFromDate(nowUtc));

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

  // derive unique types from locations for the type filter
  const types = Array.from(new Set(locations.map(l => l.type).filter(Boolean)));
  const [selectedType, setSelectedType] = useState<string>('all');

  // Load metrics for selected
  useEffect(() => {
    if (selectedId != null) {
      fetchLocation(selectedId).then(l => setSelectedName(l.name));
      fetchMetrics(selectedId, 24).then(setMetrics);
    }
  }, [selectedId]);

  // keep year/day and snapshotOffset in sync
  useEffect(() => {
    // when year/dayOfYear change, compute a snapshot at UTC midnight of that day
    const d = dateFromYearDay(year, dayOfYear);
    const now = Date.now();
    const offset = Math.round((now - d.getTime()) / (60 * 60 * 1000));
    setSnapshot(d.toISOString());
    setSnapshotOffset(offset);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year, dayOfYear]);

  // when snapshotOffset changes (via the hours slider), update year/day to match
  useEffect(() => {
    const now = Date.now();
    const d = new Date(now - snapshotOffset * 60 * 60 * 1000);
    setYear(d.getUTCFullYear());
    setDayOfYear(dayOfYearFromDate(d));
    // also update snapshot ISO
    setSnapshot(d.toISOString());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [snapshotOffset]);

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
            // snapshot and year/dayOfYear are kept in sync by effects
            setSnapshot(snap.toISOString());
          }} />
          <div className="time-display">{snapshotLabel}</div>
        </div>
        <div style={{ marginTop: 8 }}>
          <label>Year: {year}</label>
          <input type="range" min={MIN_YEAR} max={MAX_YEAR} value={year} onChange={e => setYear(parseInt(e.target.value))} />
        </div>
        <div style={{ marginTop: 4 }}>
          <label>Day of year: {dayOfYear}</label>
          <input type="range" min={1} max={365} value={dayOfYear} onChange={e => setDayOfYear(parseInt(e.target.value))} />
        </div>
        {/* moved chart: show recent metrics as bars under the UTC slider when a location is selected */}
        {selectedId != null && metrics.length > 0 && (
          <div className="chart" style={{ marginTop: 12 }}>
            {metrics.slice(-24).map(m => {
              const total = m.count;
              return (
                <div key={m.timestamp} className="bar" title={`${m.timestamp}\nCount: ${m.count}`} 
                  style={{ height: Math.min(100, total / 30) + '%' }} />
              );
            })}
          </div>
        )}
        <div style={{ marginTop: 8 }}>
          <label>Type filter</label>
          <select value={selectedType} onChange={e => setSelectedType(e.target.value)}>
            <option value="all">All</option>
            {types.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>

        <div className="list">
          {locations.map(l => (
            // only show items matching selected type (or all)
            selectedType !== 'all' && l.type !== selectedType ? null : (
            <div key={l.id} className={`list-item ${l.id === selectedId ? 'active' : ''}`} onClick={() => setSelectedId(l.id)}>
              <span>{l.name}</span>
              <span className="pill">{(l.intensity * 100).toFixed(0)}%</span>
            </div>
            )
          ))}
        </div>
        {selectedId && <LocationDetails name={selectedName} metrics={metrics} />}
      </div>
      <div className="map-container">
        <MapView locations={locations} onSelect={setSelectedId} selectedId={selectedId} selectedType={selectedType} />
      </div>
    </div>
  );
};

export default App;
