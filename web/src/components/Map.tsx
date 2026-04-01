'use client';

import { useRef, useEffect } from 'react';
import mapboxgl from 'mapbox-gl';

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!;

export type WaterPin = {
  id: string;
  name: string;
  type: string;
  latitude: number;
  longitude: number;
  has_stocking: boolean;
  stocking_recency: 'week' | 'month' | 'older' | 'none';
  has_flow_data: boolean;
};

export type MapStyle = 'outdoors' | 'satellite' | 'topo';

const STYLE_URLS: Record<MapStyle, string> = {
  outdoors: 'mapbox://styles/mapbox/outdoors-v12',
  satellite: 'mapbox://styles/mapbox/satellite-streets-v12',
  topo: 'mapbox://styles/mapbox/navigation-day-v1',
};

type Props = {
  pins: WaterPin[];
  onPinClick: (id: string) => void;
  selectedId: string | null;
  mapStyle?: MapStyle;
};

function getPinColor(pin: WaterPin): string {
  if (pin.stocking_recency === 'week') return '#22c55e';
  if (pin.stocking_recency === 'month') return '#eab308';
  if (pin.has_flow_data) return '#3b82f6';
  return '#94a3b8';
}

export default function FishMap({ pins, onPinClick, selectedId, mapStyle = 'outdoors' }: Props) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const onPinClickRef = useRef(onPinClick);
  const selectedIdRef = useRef(selectedId);
  const prevSelectedIdx = useRef(-1);

  useEffect(() => { onPinClickRef.current = onPinClick; }, [onPinClick]);
  useEffect(() => { selectedIdRef.current = selectedId; }, [selectedId]);

  // Initialize map
  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    const m = new mapboxgl.Map({
      container: mapContainer.current,
      style: STYLE_URLS[mapStyle],
      center: [-112.0, 43.0], // Center on ID/UT/MT/WY region
      zoom: 5.5,
      attributionControl: false,
    });

    m.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'bottom-right');
    m.addControl(new mapboxgl.GeolocateControl({
      positionOptions: { enableHighAccuracy: true },
      trackUserLocation: false,
    }), 'bottom-right');

    m.on('load', () => {
      // Make water bodies more prominent
      const waterLayers = ['water', 'water-shadow'];
      waterLayers.forEach(layer => {
        if (m.getLayer(layer)) {
          m.setPaintProperty(layer, 'fill-color', '#1a4a6b');
        }
      });

      // Add empty source — will be populated when pins arrive
      m.addSource('water-pins', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      // Outer glow layer — scales with zoom
      m.addLayer({
        id: 'water-pins-glow',
        type: 'circle',
        source: 'water-pins',
        paint: {
          'circle-radius': [
            'interpolate', ['linear'], ['zoom'],
            6, ['case',
              ['boolean', ['feature-state', 'selected'], false], 14,
              ['boolean', ['feature-state', 'hover'], false], 12,
              8],
            10, ['case',
              ['boolean', ['feature-state', 'selected'], false], 24,
              ['boolean', ['feature-state', 'hover'], false], 20,
              14],
            14, ['case',
              ['boolean', ['feature-state', 'selected'], false], 32,
              ['boolean', ['feature-state', 'hover'], false], 26,
              18],
          ],
          'circle-color': ['get', 'color'],
          'circle-opacity': [
            'case',
            ['boolean', ['feature-state', 'selected'], false], 0.3,
            ['boolean', ['feature-state', 'hover'], false], 0.25,
            0.15
          ],
          'circle-blur': 0.8,
        },
      });

      // Core pin layer — scales with zoom, always clearly visible
      m.addLayer({
        id: 'water-pins-core',
        type: 'circle',
        source: 'water-pins',
        paint: {
          'circle-radius': [
            'interpolate', ['linear'], ['zoom'],
            6, ['case',
              ['boolean', ['feature-state', 'selected'], false], 5,
              ['boolean', ['feature-state', 'hover'], false], 4.5,
              3],
            10, ['case',
              ['boolean', ['feature-state', 'selected'], false], 9,
              ['boolean', ['feature-state', 'hover'], false], 8,
              6],
            14, ['case',
              ['boolean', ['feature-state', 'selected'], false], 12,
              ['boolean', ['feature-state', 'hover'], false], 10,
              8],
          ],
          'circle-color': ['get', 'color'],
          'circle-opacity': 0.95,
          'circle-stroke-width': [
            'case',
            ['boolean', ['feature-state', 'selected'], false], 3,
            2
          ],
          'circle-stroke-color': [
            'case',
            ['boolean', ['feature-state', 'selected'], false], '#ffffff',
            'rgba(255,255,255,0.5)'
          ],
        },
      });

      // Labels — show at higher zoom levels
      m.addLayer({
        id: 'water-pins-labels',
        type: 'symbol',
        source: 'water-pins',
        minzoom: 9,
        layout: {
          'text-field': ['get', 'name'],
          'text-size': [
            'interpolate', ['linear'], ['zoom'],
            9, 10,
            13, 13
          ],
          'text-offset': [0, 1.4],
          'text-anchor': 'top',
          'text-font': ['DIN Pro Medium', 'Arial Unicode MS Regular'],
          'text-max-width': 10,
        },
        paint: {
          'text-color': '#e2e8f0',
          'text-halo-color': 'rgba(0,0,0,0.8)',
          'text-halo-width': 1.5,
          'text-opacity': [
            'interpolate', ['linear'], ['zoom'],
            9, 0.6,
            12, 1
          ],
        },
      });

      // Hover interaction
      let hoveredId: string | null = null;

      m.on('mouseenter', 'water-pins-core', () => {
        m.getCanvas().style.cursor = 'pointer';
      });

      m.on('mouseleave', 'water-pins-core', () => {
        m.getCanvas().style.cursor = '';
        if (hoveredId) {
          m.setFeatureState({ source: 'water-pins', id: hoveredId }, { hover: false });
          hoveredId = null;
        }
      });

      m.on('mousemove', 'water-pins-core', (e) => {
        if (e.features && e.features.length > 0) {
          if (hoveredId) {
            m.setFeatureState({ source: 'water-pins', id: hoveredId }, { hover: false });
          }
          hoveredId = e.features[0].id as string;
          m.setFeatureState({ source: 'water-pins', id: hoveredId }, { hover: true });
        }
      });

      // Click interaction
      m.on('click', 'water-pins-core', (e) => {
        if (e.features && e.features.length > 0) {
          const id = e.features[0].properties?.water_body_id;
          if (id) onPinClickRef.current(id);
        }
      });

      // Click on empty map — close detail sheet
      m.on('click', (e) => {
        const features = m.queryRenderedFeatures(e.point, { layers: ['water-pins-core'] });
        if (features.length === 0) {
          onPinClickRef.current('');
        }
      });
    });

    map.current = m;

    return () => {
      m.remove();
      map.current = null;
    };
  }, []);

  // Update pins data
  useEffect(() => {
    if (!map.current) return;

    const updateSource = () => {
      const source = map.current?.getSource('water-pins') as mapboxgl.GeoJSONSource;
      if (!source) return;

      const features = pins.map((pin, i) => ({
        type: 'Feature' as const,
        id: i,  // numeric ID for feature-state
        properties: {
          water_body_id: pin.id,
          name: pin.name,
          wtype: pin.type,
          color: getPinColor(pin),
        },
        geometry: {
          type: 'Point' as const,
          coordinates: [pin.longitude, pin.latitude],
        },
      }));

      source.setData({ type: 'FeatureCollection', features });
    };

    if (map.current.loaded() && map.current.getSource('water-pins')) {
      updateSource();
    } else {
      map.current.on('load', updateSource);
    }
  }, [pins]);

  // Fly to selected
  useEffect(() => {
    if (!map.current || !selectedId) return;

    const pin = pins.find(p => p.id === selectedId);
    if (!pin) return;

    map.current.flyTo({
      center: [pin.longitude, pin.latitude],
      zoom: Math.max(map.current.getZoom(), 11),
      offset: [0, -100],
      duration: 800,
    });

    // Set selected feature state
    const source = map.current.getSource('water-pins');
    if (source) {
      // Clear previous selection only
      if (prevSelectedIdx.current >= 0) {
        map.current.setFeatureState({ source: 'water-pins', id: prevSelectedIdx.current }, { selected: false });
      }
      // Set new selection
      const idx = pins.findIndex(p => p.id === selectedId);
      if (idx >= 0) {
        map.current.setFeatureState({ source: 'water-pins', id: idx }, { selected: true });
      }
      prevSelectedIdx.current = idx;
    }
  }, [selectedId, pins]);

  // Style switching
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    try {
      const center = map.current.getCenter();
      const zoom = map.current.getZoom();
      map.current.setStyle(STYLE_URLS[mapStyle]);
      map.current.once('style.load', () => {
        if (!map.current!.getSource('water-pins')) {
          map.current!.addSource('water-pins', {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: [] },
          });
        }
        map.current!.setCenter(center);
        map.current!.setZoom(zoom);
      });
    } catch {
      // Style not ready yet — ignore
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapStyle]);

  return (
    <div ref={mapContainer} className="absolute inset-0 w-full h-full" />
  );
}
