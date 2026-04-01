'use client';

import { useState, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import SearchBar from '@/components/SearchBar';
import FilterChips from '@/components/FilterChips';
import DetailSheet from '@/components/DetailSheet';
import Legend from '@/components/Legend';
import BottomNav, { type Tab } from '@/components/BottomNav';
import HotBites from '@/components/HotBites';
import ExplorePage from '@/components/ExplorePage';
import MapControls from '@/components/MapControls';
import ProfilePage from '@/components/ProfilePage';
import { supabase } from '@/lib/supabase';
import type { MapStyle } from '@/components/Map';

const FishMap = dynamic(() => import('@/components/Map'), { ssr: false });

type WaterBodyRow = {
  id: string;
  name: string;
  state: string;
  county: string;
  type: string;
  has_stocking: boolean;
  has_flow_data: boolean;
  elevation_ft: number | null;
  surface_acres: number | null;
  latitude: number;
  longitude: number;
  latest_stocking_date: string | null;
};

function getStockingRecency(dateStr: string | null): 'week' | 'month' | 'older' | 'none' {
  if (!dateStr) return 'none';
  const d = new Date(dateStr + 'T00:00:00');
  const now = new Date();
  const diff = (now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24);
  if (diff <= 7) return 'week';
  if (diff <= 30) return 'month';
  return 'older';
}

export default function Home() {
  const [waterBodies, setWaterBodies] = useState<WaterBodyRow[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'map' | 'hotbites' | 'search' | 'profile'>('map');
  const [mapStyle, setMapStyle] = useState<MapStyle>('outdoors');
  const [user, setUser] = useState<any>(null);

  // Auth listener
  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setUser(data.user));
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user || null);
    });
    return () => subscription.unsubscribe();
  }, []);
  const [filters, setFilters] = useState([
    { id: 'stocked', label: 'Recently Stocked', active: false },
    { id: 'lakes', label: 'Lakes', active: false },
    { id: 'rivers', label: 'Rivers', active: false },
    { id: 'flow', label: 'Live Flow', active: false },
    { id: 'trout', label: 'Trout', active: false },
    { id: 'bass', label: 'Bass', active: false },
    { id: 'walleye', label: 'Walleye', active: false },
  ]);
  const [speciesWaterIds, setSpeciesWaterIds] = useState<Record<string, Set<string>>>({});

  // Load species filter data
  useEffect(() => {
    async function loadSpeciesFilters() {
      const { data } = await supabase
        .from('water_body_species')
        .select('water_body_id, species(common_name, species_group)')
        .limit(10000);

      if (!data) return;

      const groups: Record<string, Set<string>> = { trout: new Set(), bass: new Set(), walleye: new Set() };
      data.forEach((d: any) => {
        const group = d.species?.species_group;
        const wbId = d.water_body_id;
        if (group === 'trout' || group === 'salmon') groups.trout.add(wbId);
        if (group === 'bass') groups.bass.add(wbId);
        if (group === 'walleye') groups.walleye.add(wbId);
      });
      setSpeciesWaterIds(groups);
    }
    loadSpeciesFilters();
  }, []);

  useEffect(() => {
    async function load() {
      // Fetch ALL water bodies in pages of 1000 (Supabase default limit)
      let allWbs: any[] = [];
      let page = 0;
      const pageSize = 1000;
      while (true) {
        const { data: batch } = await supabase
          .from('water_bodies')
          .select('id, name, state, county, type, has_stocking, has_flow_data, elevation_ft, surface_acres')
          .is('parent_id', null)
          .neq('status', 'merged')
          .range(page * pageSize, (page + 1) * pageSize - 1);
        if (!batch || batch.length === 0) break;
        allWbs = allWbs.concat(batch);
        if (batch.length < pageSize) break;
        page++;
      }
      const wbs = allWbs;

      if (!wbs.length) { setLoading(false); return; }

      // Get latest stocking dates
      const { data: stockingDates } = await supabase
        .from('stocking_events')
        .select('water_body_id, date')
        .order('date', { ascending: false });

      const latestStocking: Record<string, string> = {};
      stockingDates?.forEach(s => {
        if (!latestStocking[s.water_body_id]) {
          latestStocking[s.water_body_id] = s.date;
        }
      });

      // Get coordinates — paginate RPC results too
      let coordMap: Record<string, { lat: number; lon: number }> = {};
      const states = Array.from(new Set(wbs.map(w => w.state)));
      for (const state of states) {
        try {
          // RPC may be limited to 1000, paginate
          let offset = 0;
          while (true) {
            const { data: coords } = await supabase
              .rpc('get_water_body_coords', { p_state: state })
              .range(offset, offset + pageSize - 1);
            if (!coords || coords.length === 0) break;
            coords.forEach((c: any) => { coordMap[c.id] = { lat: c.lat, lon: c.lon }; });
            if (coords.length < pageSize) break;
            offset += pageSize;
          }
        } catch {}
      }

      // Fallback: NOAA links for any waters still missing coords
      const missingCoordIds = wbs.filter(w => !coordMap[w.id]).map(w => w.id);
      if (missingCoordIds.length > 0) {
        let noaaOffset = 0;
        while (noaaOffset < missingCoordIds.length) {
          const batch = missingCoordIds.slice(noaaOffset, noaaOffset + 50);
          const { data: noaaLinks } = await supabase
            .from('data_source_links')
            .select('water_body_id, external_id')
            .eq('source_type', 'noaa_station')
            .in('water_body_id', batch);

          noaaLinks?.forEach(link => {
            const parts = link.external_id?.split(',');
            if (parts && parts.length === 2) {
              coordMap[link.water_body_id] = {
                lat: parseFloat(parts[0]),
                lon: parseFloat(parts[1]),
              };
            }
          });
          noaaOffset += 50;
        }
      }

      const enriched: WaterBodyRow[] = wbs
        .map(wb => ({
          ...wb,
          latitude: coordMap[wb.id]?.lat || 0,
          longitude: coordMap[wb.id]?.lon || 0,
          latest_stocking_date: latestStocking[wb.id] || null,
        }))
        .filter(wb => wb.latitude !== 0);
      setWaterBodies(enriched);
      setLoading(false);
    }

    load();
  }, []);

  const filteredPins = useMemo(() => {
    const activeFilters = filters.filter(f => f.active);
    if (activeFilters.length === 0) return waterBodies;

    return waterBodies.filter(wb => {
      for (const f of activeFilters) {
        if (f.id === 'stocked' && getStockingRecency(wb.latest_stocking_date) === 'none') return false;
        if (f.id === 'lakes' && !['lake', 'reservoir'].includes(wb.type)) return false;
        if (f.id === 'rivers' && !['river', 'creek', 'stream'].includes(wb.type)) return false;
        if (f.id === 'flow' && !wb.has_flow_data) return false;
        if (f.id === 'trout' && !speciesWaterIds.trout?.has(wb.id)) return false;
        if (f.id === 'bass' && !speciesWaterIds.bass?.has(wb.id)) return false;
        if (f.id === 'walleye' && !speciesWaterIds.walleye?.has(wb.id)) return false;
      }
      return true;
    });
  }, [waterBodies, filters, speciesWaterIds]);

  const pins = useMemo(() =>
    filteredPins.map(wb => ({
      id: wb.id,
      name: wb.name,
      type: wb.type,
      latitude: wb.latitude,
      longitude: wb.longitude,
      has_stocking: wb.has_stocking,
      stocking_recency: getStockingRecency(wb.latest_stocking_date),
      has_flow_data: wb.has_flow_data,
    })),
    [filteredPins]
  );

  const handleTabChange = (tab: 'map' | 'hotbites' | 'search' | 'profile') => {
    if (tab === 'profile' && !user) {
      window.location.href = '/auth';
      return;
    }
    setActiveTab(tab);
    if (tab === 'map') setSelectedId(null);
  };

  return (
    <main className="relative w-full h-screen overflow-hidden bg-[var(--bg-primary)]">
      {/* Map — always mounted */}
      <FishMap
        pins={pins}
        onPinClick={(id) => {
          setSelectedId(id === '' ? null : id);
          setActiveTab('map');
        }}
        selectedId={selectedId}
        mapStyle={mapStyle}
      />

      {/* Map UI overlay — only when on map tab */}
      {activeTab === 'map' && (
        <>
          <SearchBar onSelect={(id) => setSelectedId(id)} />

          <FilterChips
            filters={filters}
            onToggle={(id) =>
              setFilters(prev => prev.map(f => f.id === id ? { ...f, active: !f.active } : f))
            }
          />

          <MapControls activeStyle={mapStyle} onStyleChange={setMapStyle} />

          {!selectedId && <Legend />}

          <DetailSheet
            waterBodyId={selectedId}
            onClose={() => setSelectedId(null)}
          />
        </>
      )}

      {/* Hot Bites */}
      <HotBites
        visible={activeTab === 'hotbites'}
        onSelect={(id) => { setSelectedId(id); setActiveTab('map'); }}
        onClose={() => setActiveTab('map')}
      />

      {/* Explore Page */}
      <ExplorePage
        visible={activeTab === 'search'}
        onSelect={(id) => { setSelectedId(id); setActiveTab('map'); }}
        onClose={() => setActiveTab('map')}
      />

      {/* Profile Page */}
      <ProfilePage
        visible={activeTab === 'profile'}
        user={user}
        onClose={() => setActiveTab('map')}
        onSelectWater={(id) => { setSelectedId(id); setActiveTab('map'); }}
      />

      {/* Bottom Navigation */}
      <BottomNav active={activeTab} onChange={handleTabChange} isLoggedIn={!!user} />

      {/* Brand watermark */}
      {activeTab === 'map' && !selectedId && (
        <div className="absolute top-28 right-4 z-10 pointer-events-none">
          <div
            className="text-[10px] font-bold tracking-[0.25em] text-white/10 uppercase"
            style={{ writingMode: 'vertical-rl' }}
          >
            FishOn
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-[var(--bg-primary)]">
          <div className="text-center">
            <div className="text-2xl font-bold tracking-tight text-white mb-2">FishOn</div>
            <div className="text-xs text-[var(--text-muted)]">Loading waters...</div>
          </div>
        </div>
      )}
    </main>
  );
}
