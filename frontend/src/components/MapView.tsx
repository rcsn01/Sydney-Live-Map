import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { LocationWithIntensity } from '../types';

interface Props {
  locations: LocationWithIntensity[];
  onSelect: (id: number) => void;
  selectedId?: number;
  // Called when the set of visible location ids changes (after moveend and on data updates)
  onVisibleChange?: (visibleIds: number[]) => void;
}

const MapView: React.FC<Props> = ({ locations, onSelect, selectedId, onVisibleChange }) => {
  const mapRef = useRef<L.Map | null>(null);
  // Keep markers keyed by location id so we can add/remove/update efficiently
  const markersRef = useRef<Record<number, L.CircleMarker>>({});

  useEffect(() => {
    if (mapRef.current) return; // init only once
    const map = L.map('map').setView([-33.8688, 151.2093], 14);
    mapRef.current = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    return () => {
      // cleanup on unmount
      (Object.values(markersRef.current) as L.CircleMarker[]).forEach(m => m.remove());
      map.remove();
      mapRef.current = null;
      markersRef.current = {};
    };
  }, []);

  // Helper to compute styling & radius based on intensity and selection
  const computeMarkerOptions = (loc: LocationWithIntensity, minI: number, maxI: number) => {
    const norm = (loc.intensity - minI) / (maxI - minI || 1);
    const radius = 4 + norm * 60;
    const isSelected = loc.id === selectedId;
    return {
      radius,
      color: isSelected ? '#ff8800' : '#3388ff',
      weight: 1.5,
      fillOpacity: 0.85,
      fillColor: isSelected ? '#ff8800' : '#3388ff',
      _animDuration: `${(1.8 - norm * 1.2).toFixed(2)}s`,
      _norm: norm
    } as const;
  };

  // Effect: synchronize visible markers whenever locations, selectedId, or map bounds change
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Keep markers in sync when the map stops moving or when locations prop changes
    const updateVisibleMarkers = () => {
      const bounds = map.getBounds();

      // compute intensity scaling across provided locations so circle sizes are consistent
      const intensities = locations.map((l: LocationWithIntensity) => l.intensity);
      const minI = Math.min(...intensities, 0);
      const maxI = Math.max(...intensities, 1);

      const visible = locations.filter((l: LocationWithIntensity) => bounds.contains([l.latitude, l.longitude] as L.LatLngExpression));
      const visibleIds = new Set<number>(visible.map((v: LocationWithIntensity) => v.id));

      // Remove markers that are no longer visible
      for (const idStr of Object.keys(markersRef.current)) {
        const id = Number(idStr);
        if (!visibleIds.has(id)) {
          markersRef.current[id].remove();
          delete markersRef.current[id];
        }
      }

      // Add or update visible markers
      visible.forEach((loc: LocationWithIntensity) => {
        const opts = computeMarkerOptions(loc, minI, maxI);
        const existing = markersRef.current[loc.id];
        if (existing) {
          // update style if changed (selection or intensity changed)
          existing.setStyle({ radius: opts.radius, color: opts.color, fillColor: opts.fillColor });
          existing.unbindTooltip();
          existing.bindTooltip(`${loc.name}<br/>Intensity: ${(loc.intensity * 100).toFixed(0)}%`);
        } else {
          const marker = L.circleMarker([loc.latitude, loc.longitude], {
            radius: opts.radius,
            color: opts.color,
            weight: opts.weight,
            fillOpacity: opts.fillOpacity,
            fillColor: opts.fillColor
          }).addTo(map);
          marker.bindTooltip(`${loc.name}<br/>Intensity: ${(loc.intensity * 100).toFixed(0)}%`);
          marker.on('click', () => onSelect(loc.id));
          // no pulsing animation: keep marker static
          // const el = (marker as any)._path as SVGElement | undefined;
          // if (el) {
          //   el.classList.add('pulse');
          //   el.style.animationDuration = opts._animDuration;
          // }
          markersRef.current[loc.id] = marker;
        }
      });

      // Call optional callback with array of visible ids
      if (onVisibleChange) {
        onVisibleChange(Array.from(visibleIds));
      }
    };

    // initial update
    updateVisibleMarkers();

    // update on map move end
    map.on('moveend', updateVisibleMarkers);

    // also update if user resizes window or locations change quickly
    window.addEventListener('resize', updateVisibleMarkers);

    return () => {
      map.off('moveend', updateVisibleMarkers);
      window.removeEventListener('resize', updateVisibleMarkers);
    };
  }, [locations, selectedId, onSelect]);

  return <div id="map" style={{ height: '100%', width: '100%' }} />;
};

export default MapView;
