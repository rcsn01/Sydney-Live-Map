import React, { useEffect } from 'react';
import L from 'leaflet';
import { LocationWithIntensity } from '../types';

interface Props {
  locations: LocationWithIntensity[];
  onSelect: (id: number) => void;
  selectedId?: number;
}

const MapView: React.FC<Props> = ({ locations, onSelect, selectedId }) => {
  useEffect(() => {
    const map = L.map('map').setView([-33.8688, 151.2093], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    const markers: L.CircleMarker[] = [];

    // Determine dynamic scaling across current snapshot to accentuate differences
    const intensities = locations.map(l => l.intensity);
    const minI = Math.min(...intensities, 0);
    const maxI = Math.max(...intensities, 1);

    locations.forEach(loc => {
      // Normalize intensity to 0..1 then scale radius
      const norm = (loc.intensity - minI) / (maxI - minI || 1);
      const radius = 4 + norm * 60; // smaller base, larger max to emphasize busy spots
      /*const radius = 4 + Math.sqrt(norm) * 20;
      const radius = 4 + (norm ** 2) * 20;
      const radius = 4 + (Math.log1p(norm * 9) / Math.log(10)) * 20;*/
      const marker = L.circleMarker([loc.latitude, loc.longitude], {
        radius,
        color: loc.id === selectedId ? '#ff8800' : '#3388ff',
        weight: 1.5,
        fillOpacity: 0.85,
        fillColor: loc.id === selectedId ? '#ff8800' : '#3388ff'
      }).addTo(map);
      marker.bindTooltip(`${loc.name}<br/>Intensity: ${(loc.intensity * 100).toFixed(0)}%`);
      marker.on('click', () => onSelect(loc.id));
      const el = (marker as any)._path as SVGElement;
      el.classList.add('pulse');
      // Keep animation duration tied to intensity if desired (faster for busy)
      el.style.animationDuration = `${(1.8 - norm * 1.2).toFixed(2)}s`;
      markers.push(marker);
    });

    return () => {
      markers.forEach(m => m.remove());
      map.remove();
    };
  }, [locations, onSelect, selectedId]);

  return <div id="map" style={{ height: '100%', width: '100%' }} />;
};

export default MapView;
