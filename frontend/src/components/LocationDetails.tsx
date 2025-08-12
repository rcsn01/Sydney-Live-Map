import React from 'react';
import { MetricPoint } from '../types';

interface Props {
  name: string;
  metrics: MetricPoint[];
}

const LocationDetails: React.FC<Props> = ({ name, metrics }) => {
  return (
    <div className="details">
      <h2>{name}</h2>
      <h3>Last {metrics.length} Points</h3>
      <div className="chart">
        {metrics.slice(-24).map(m => {
          const total = m.pedestrian_count + m.traffic_count;
            return (
              <div key={m.timestamp} className="bar" title={`${m.timestamp}\nPed: ${m.pedestrian_count} Traffic: ${m.traffic_count}`}
                style={{ height: Math.min(100, total / 30) + '%' }} />
            );
        })}
      </div>
    </div>
  );
};

export default LocationDetails;
