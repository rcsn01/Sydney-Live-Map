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
    </div>
  );
};

export default LocationDetails;
