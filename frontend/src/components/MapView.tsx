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
  const canvasRendererRef = useRef<L.Renderer | null>(null);
  // Keep markers keyed by location id so we can add/remove/update efficiently
  const markersRef = useRef<Record<number, L.CircleMarker>>({});

  useEffect(() => {
    if (mapRef.current) return; // init only once
  // preferCanvas reduces SVG/DOM pressure when many markers are present
  const map = L.map('map', { preferCanvas: true }).setView([-33.8688, 151.2093], 14);
    mapRef.current = map;

  // create a single shared canvas renderer for performant circleMarker rendering
  canvasRendererRef.current = L.canvas();

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
      // reduce opacity for non-selected markers to improve visual density
      fillOpacity: isSelected ? 0.9 : 0.25,
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

  // compute visible locations and scale marker sizes relative to the visible set
  const visible = locations.filter((l: LocationWithIntensity) => bounds.contains([l.latitude, l.longitude] as L.LatLngExpression));

  // determine min/max intensity among visible locations (fall back to global range if none visible)
  const visibleIntensities = visible.map(v => v.intensity);
  const minI = visibleIntensities.length ? Math.min(...visibleIntensities) : Math.min(...locations.map(l => l.intensity), 0);
  const maxI = visibleIntensities.length ? Math.max(...visibleIntensities) : Math.max(...locations.map(l => l.intensity), 1);

  // Constants for min/max radius (px) and piecewise scaling params.
  const MIN_RADIUS = 4;
  const MAX_RADIUS = 30;
  // Piecewise scaling parameters:
  // - LOW_EXP compresses low/mid values so they grow slowly.
  // - HIGH_EXP emphasizes values above THRESHOLD so the very top remains sensitive.
  // - THRESHOLD is the normalized point (0..1) where we switch behavior.
  const LOW_EXP = 0.6;   // <1 compresses lower values
  const HIGH_EXP = 3.0;  // >1 accentuates the top-end
  const THRESHOLD = 0.75;

  // Map a normalized value in [0,1] to a scaled value in [0,1] using a
  // piecewise function that keeps the mapping continuous at THRESHOLD.
  const piecewiseScale = (n: number) => {
    if (n <= 0) return 0;
    if (n >= 1) return 1;
    if (n <= THRESHOLD) {
      return Math.pow(n, LOW_EXP);
    }
    const lowVal = Math.pow(THRESHOLD, LOW_EXP);
    const t = (n - THRESHOLD) / (1 - THRESHOLD); // 0..1 over the upper segment
    return lowVal + Math.pow(t, HIGH_EXP) * (1 - lowVal);
  };
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
  // compute normalized radius for this visible location so smallest visible -> MIN_RADIUS, largest visible -> MAX_RADIUS
  const range = (maxI - minI);
  // If all visible intensities are equal, render medium size (0.5) rather than always max.
  const rawNorm = range === 0 ? 0.5 : (loc.intensity - minI) / range;
  const norm = Math.max(0, Math.min(1, rawNorm));
  const scaled = piecewiseScale(norm);
  const radius = MIN_RADIUS + scaled * (MAX_RADIUS - MIN_RADIUS);
        const opts = computeMarkerOptions(loc, minI, maxI);
        // override radius computed from computeMarkerOptions with visible-relative radius
        const finalRadius = radius;
        const existing = markersRef.current[loc.id];
        if (existing) {
          // update style if changed (selection or intensity changed)
          // setRadius must be used to change marker size on CircleMarker
          try {
            (existing as any).setRadius(finalRadius);
          } catch (err) {
            // fallback: some Leaflet builds may not expose setRadius; attempt via setStyle
            existing.setStyle({ radius: finalRadius });
          }
          existing.setStyle({ color: opts.color, fillColor: opts.fillColor });
          existing.unbindTooltip();
          existing.bindTooltip(`${loc.name}<br/>Intensity: ${(loc.intensity * 100).toFixed(0)}%`);
        } else {
          const marker = L.circleMarker([loc.latitude, loc.longitude], {
            radius: finalRadius,
            color: opts.color,
            weight: opts.weight,
            fillOpacity: opts.fillOpacity,
            fillColor: opts.fillColor,
            renderer: canvasRendererRef.current || undefined
          }).addTo(map);
          marker.bindTooltip(`${loc.name}<br/>Intensity: ${(loc.intensity * 100).toFixed(0)}%`);
          // click selection disabled: do not register marker.on('click')
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
