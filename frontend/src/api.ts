import axios from 'axios';
import { LocationWithIntensity, MetricPoint, Location } from './types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export async function fetchLocations(at?: string): Promise<LocationWithIntensity[]> {
  const params: Record<string, string> = {};
  if (at) params.at = at;
  const res = await axios.get(`${API_BASE}/locations`, { params });
  return res.data;
}

export async function fetchLocation(id: number): Promise<Location> {
  const res = await axios.get(`${API_BASE}/locations/${id}`);
  return res.data;
}

export async function fetchMetrics(id: number, hours = 24): Promise<MetricPoint[]> {
  const res = await axios.get(`${API_BASE}/locations/${id}/metrics`, { params: { hours } });
  return res.data;
}

export async function fetchLocationTypes(): Promise<string[]> {
  const res = await axios.get(`${API_BASE}/location-types`);
  return res.data;
}

export async function fetchMetricsByType(type: string, hours = 24): Promise<MetricPoint[]> {
  const res = await axios.get(`${API_BASE}/metrics`, { params: { type, hours } });
  return res.data;
}
