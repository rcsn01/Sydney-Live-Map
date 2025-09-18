export interface Location {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  type: string;
}

export interface LocationWithIntensity extends Location {
  intensity: number; // 0-1 scale
}

export interface MetricPoint {
  timestamp: string;
  count: number;
}
