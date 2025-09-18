import React, { useEffect } from 'react';
import L from 'leaflet';
import { LocationWithIntensity } from '../types';

interface Props {
  locations: LocationWithIntensity[];
  onSelect: (id: number) => void;
  selectedId?: number;
  selectedType?: string;
}
const MapView: React.FC<Props> = ({ locations, onSelect, selectedId, selectedType = 'all' }) => {
  useEffect(() => {
    const map = L.map('map').setView([-33.8688, 151.2093], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    const markerLayer = L.layerGroup().addTo(map);

    const renderMarkers = () => {
      markerLayer.clearLayers();
      if (!locations || locations.length === 0) return;
      // Determine dynamic scaling across current snapshot to accentuate differences
      const intensities = locations.map(l => l.intensity);
      const minI = Math.min(...intensities, 0);
      const maxI = Math.max(...intensities, 1);
      const bounds = map.getBounds();

      locations.forEach(loc => {
        // respect the selected type filter
        if (selectedType && selectedType !== 'all' && loc.type !== selectedType) return;
        // only render if inside current viewport
        const latlng = L.latLng(loc.latitude, loc.longitude);
        if (!bounds.contains(latlng)) return;

        // Normalize intensity to 0..1 then scale radius
        const norm = (loc.intensity - minI) / (maxI - minI || 1);
        const radius = 4 + norm * 60;
        const marker = L.circleMarker([loc.latitude, loc.longitude], {
          radius,
          color: loc.id === selectedId ? '#ff8800' : '#3388ff',
          weight: 1.5,
          fillOpacity: 0.5,
          fillColor: loc.id === selectedId ? '#ff8800' : '#3388ff'
        });
        marker.bindTooltip(`${loc.name}<br/>Intensity: ${(loc.intensity * 100).toFixed(0)}%`);
        marker.on('click', () => onSelect(loc.id));
        marker.addTo(markerLayer);
        // no pulsing animation: keep marker static for performance
        // const el = (marker as any)._path as SVGElement;
        // if (el) {
        //   el.classList.add('pulse');
        //   el.style.animationDuration = `${(1.8 - norm * 1.2).toFixed(2)}s`;
        // }
      });
    };

    // initial render
    renderMarkers();
    // refresh when map moves or zooms
    map.on('moveend zoomend', renderMarkers);

    return () => {
      map.off('moveend zoomend', renderMarkers);
      markerLayer.clearLayers();
      markerLayer.remove();
      map.remove();
    };
  }, [locations, onSelect, selectedId]);

  return <div id="map" style={{ height: '100%', width: '100%' }} />;
};

export default MapView;
