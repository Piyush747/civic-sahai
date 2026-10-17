import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

type LocationPickerProps = {
  latitude: number;
  longitude: number;
  mapLabel: string;
  onPositionChange: (latitude: number, longitude: number) => void;
};

export function LocationPicker({ latitude, longitude, mapLabel, onPositionChange }: LocationPickerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const pinRef = useRef<L.CircleMarker | null>(null);
  const onPositionRef = useRef(onPositionChange);
  const startRef = useRef<[number, number]>([latitude, longitude]);
  const [geoError, setGeoError] = useState('');
  onPositionRef.current = onPositionChange;

  useEffect(() => {
    const node = containerRef.current;
    if (!node || mapRef.current) return;
    const map = L.map(node, { zoomControl: true }).setView(startRef.current, 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 19,
    }).addTo(map);
    pinRef.current = L.circleMarker(startRef.current, {
      radius: 9,
      color: '#0a7a6b',
      weight: 3,
      fillColor: '#0a7a6b',
      fillOpacity: 1,
    }).addTo(map);
    map.on('click', (event: L.LeafletMouseEvent) => {
      onPositionRef.current(event.latlng.lat, event.latlng.lng);
    });
    mapRef.current = map;
    const frame = window.requestAnimationFrame(() => map.invalidateSize());
    return () => {
      window.cancelAnimationFrame(frame);
      map.remove();
      mapRef.current = null;
      pinRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const pin = pinRef.current;
    if (!map || !pin || !Number.isFinite(latitude) || !Number.isFinite(longitude)) return;
    pin.setLatLng([latitude, longitude]);
    map.panTo([latitude, longitude]);
  }, [latitude, longitude]);

  function useMyLocation() {
    if (!navigator.geolocation) {
      setGeoError('This browser cannot share your location. Drop a pin on the map.');
      return;
    }
    setGeoError('');
    navigator.geolocation.getCurrentPosition(
      (position) => onPositionRef.current(position.coords.latitude, position.coords.longitude),
      () => setGeoError('Location permission was blocked. Drop a pin on the map.'),
      { enableHighAccuracy: true, timeout: 8000 },
    );
  }

  return (
    <section className="location-picker">
      <div ref={containerRef} className="complaint-map" role="application" aria-label={mapLabel} />
      <div className="location-picker-bar">
        <button type="button" className="button-secondary location-pin" onClick={useMyLocation}>
          Use my location
        </button>
        <span className="field-hint">
          {Number.isFinite(latitude) ? latitude.toFixed(5) : '—'}, {Number.isFinite(longitude) ? longitude.toFixed(5) : '—'}
        </span>
      </div>
      {geoError && <p className="error">{geoError}</p>}
    </section>
  );
}
