import React from 'react';
import { MetricPoint } from '../types';

interface Props {
  name: string;
  metrics: MetricPoint[];
}

const LocationDetails: React.FC<Props> = ({ name, metrics }) => {
  const recent = metrics.slice(-24);
  return (
    <div className="details">
      <h2>{name}</h2>
      <h3>Last {recent.length} Points</h3>
      <div className="chart" style={{ display: 'flex', gap: 4, alignItems: 'end', height: 100 }}>
        {recent.map((m) => {
          const total = m.count;
          const heightPct = Math.min(100, (total / 30) * 100);
          const label = new Date(m.timestamp).toISOString().slice(11, 16);
          return (
            <div key={m.timestamp} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div className="bar" title={`${m.timestamp}\nCount: ${m.count}`} style={{ width: 8, height: `${heightPct}%`, background: '#3388ff', borderRadius: 3 }} />
              <div style={{ fontSize: 10, marginTop: 4 }}>{label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default LocationDetails;
