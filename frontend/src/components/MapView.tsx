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

    locations.forEach(loc => {
      const radius = 8 + loc.intensity * 12;
      const marker = L.circleMarker([loc.latitude, loc.longitude], {
        radius,
        color: loc.id === selectedId ? '#ff8800' : '#3388ff',
        weight: 2,
        fillOpacity: 0.6
      }).addTo(map);
      marker.bindTooltip(`${loc.name}<br/>Intensity: ${loc.intensity}`);
      marker.on('click', () => onSelect(loc.id));
      // Pulse animation via CSS class toggling
      const el = (marker as any)._path as SVGElement;
      el.classList.add('pulse');
      el.style.animationDuration = `${Math.max(0.5, 2 - loc.intensity * 1.5)}s`;
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
