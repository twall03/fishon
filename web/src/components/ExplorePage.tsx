'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

type WaterBodyResult = {
  id: string;
  name: string;
  type: string;
  county: string;
  state: string;
  has_stocking: boolean;
  elevation_ft: number | null;
  surface_acres: number | null;
};

type Props = {
  visible: boolean;
  onSelect: (id: string) => void;
  onClose: () => void;
};

function TypeIcon({ type }: { type: string }) {
  const icons: Record<string, string> = {
    lake: '🏔',
    reservoir: '🏞',
    river: '🌊',
    creek: '💧',
    pond: '🐟',
    stream: '💧',
  };
  return <span className="text-sm">{icons[type] || '📍'}</span>;
}

export default function ExplorePage({ visible, onSelect, onClose }: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<WaterBodyResult[]>([]);
  const [allWaters, setAllWaters] = useState<WaterBodyResult[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!visible) return;
    setLoading(true);

    async function load() {
      const { data } = await supabase
        .from('water_bodies')
        .select('id, name, type, county, state, has_stocking, elevation_ft, surface_acres')
        .is('parent_id', null)
        .order('name');

      setAllWaters(data || []);
      setResults(data || []);
      setLoading(false);
    }
    load();
  }, [visible]);

  useEffect(() => {
    let filtered = allWaters;

    if (query.length >= 2) {
      const q = query.toLowerCase();
      filtered = filtered.filter(w =>
        w.name.toLowerCase().includes(q) ||
        w.county?.toLowerCase().includes(q)
      );
    }

    if (filter !== 'all') {
      if (filter === 'lakes') filtered = filtered.filter(w => ['lake', 'reservoir'].includes(w.type));
      if (filter === 'rivers') filtered = filtered.filter(w => ['river', 'creek', 'stream'].includes(w.type));
      if (filter === 'stocked') filtered = filtered.filter(w => w.has_stocking);
    }

    setResults(filtered.slice(0, 100));
  }, [query, filter, allWaters]);

  if (!visible) return null;

  return (
    <div className="absolute inset-0 z-40 flex flex-col bg-[var(--bg-primary)]">
      {/* Header */}
      <div className="px-5 pt-5 pb-3">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-lg font-bold text-white tracking-tight">Explore</h1>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors text-[var(--text-muted)]"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M5 5L15 15M15 5L5 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        </div>

        {/* Search */}
        <div className="glass rounded-xl px-4 py-2.5 flex items-center gap-3 mb-3">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-[var(--text-muted)]">
            <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name, county..."
            className="flex-1 bg-transparent text-sm text-white placeholder:text-[var(--text-muted)] outline-none"
          />
        </div>

        {/* Filter tabs */}
        <div className="flex gap-2">
          {[
            { id: 'all', label: 'All' },
            { id: 'lakes', label: 'Lakes' },
            { id: 'rivers', label: 'Rivers' },
            { id: 'stocked', label: 'Stocked' },
          ].map(f => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`text-xs px-3 py-1.5 rounded-full transition-colors ${
                filter === f.id
                  ? 'bg-[var(--accent)] text-white'
                  : 'bg-white/5 text-[var(--text-muted)] hover:text-white'
              }`}
            >
              {f.label}
            </button>
          ))}
          <span className="text-xs text-[var(--text-muted)] self-center ml-auto">
            {results.length} waters
          </span>
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto px-4 pb-20">
        {loading ? (
          <div className="space-y-2 mt-2">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-14 bg-white/5 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="space-y-1.5 mt-2">
            {results.map(w => (
              <button
                key={w.id}
                onClick={() => { onSelect(w.id); onClose(); }}
                className="w-full text-left flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-colors"
              >
                <TypeIcon type={w.type} />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate">{w.name}</div>
                  <div className="text-[11px] text-[var(--text-muted)]">
                    {w.county} · {w.type} · {w.state}
                    {w.elevation_ft ? ` · ${w.elevation_ft.toLocaleString()}ft` : ''}
                  </div>
                </div>
                {w.has_stocking && (
                  <div className="w-2 h-2 rounded-full bg-green-400 flex-shrink-0" />
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
