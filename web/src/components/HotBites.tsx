'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

type HotBite = {
  water_body_id: string;
  water_body_name: string;
  county: string;
  type: string;
  species: string;
  quantity: number;
  date: string;
  days_ago: number;
};

type Props = {
  onSelect: (id: string) => void;
  visible: boolean;
  onClose: () => void;
};

function daysAgoLabel(days: number) {
  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  return `${days}d ago`;
}

function stockingColor(days: number) {
  if (days <= 3) return 'text-green-400';
  if (days <= 7) return 'text-green-300';
  if (days <= 14) return 'text-yellow-400';
  return 'text-[var(--text-muted)]';
}

export default function HotBites({ onSelect, visible, onClose }: Props) {
  const [bites, setBites] = useState<HotBite[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!visible) return;
    setLoading(true);

    async function load() {
      // Get recent stocking events with water body info
      const { data } = await supabase
        .from('stocking_events')
        .select('water_body_id, species_raw, quantity, date, water_bodies!inner(name, county, type)')
        .order('date', { ascending: false })
        .limit(30);

      if (!data) { setLoading(false); return; }

      const now = new Date();
      const enriched: HotBite[] = data.map((d: any) => {
        const eventDate = new Date(d.date + 'T00:00:00');
        const days = Math.floor((now.getTime() - eventDate.getTime()) / (1000 * 60 * 60 * 24));
        return {
          water_body_id: d.water_body_id,
          water_body_name: d.water_bodies.name,
          county: d.water_bodies.county,
          type: d.water_bodies.type,
          species: d.species_raw,
          quantity: d.quantity,
          date: d.date,
          days_ago: days,
        };
      });

      // Deduplicate by water body + species + date
      const seen = new Set<string>();
      const unique = enriched.filter(b => {
        const key = `${b.water_body_id}-${b.species}-${b.date}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });

      setBites(unique);
      setLoading(false);
    }

    load();
  }, [visible]);

  if (!visible) return null;

  return (
    <div className="absolute inset-0 z-40 flex flex-col bg-[var(--bg-primary)]">
      {/* Header */}
      <div className="flex items-center justify-between px-5 pt-5 pb-3">
        <div>
          <h1 className="text-lg font-bold text-white tracking-tight">Hot Bites</h1>
          <p className="text-xs text-[var(--text-muted)]">Recent stocking & activity across Utah</p>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-white/10 transition-colors text-[var(--text-muted)]"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M5 5L15 15M15 5L5 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </button>
      </div>

      {/* Feed */}
      <div className="flex-1 overflow-y-auto px-4 pb-20">
        {loading ? (
          <div className="space-y-3 mt-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-white/5 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="space-y-2 mt-2">
            {bites.map((bite, i) => (
              <button
                key={`${bite.water_body_id}-${bite.species}-${bite.date}-${i}`}
                onClick={() => { onSelect(bite.water_body_id); onClose(); }}
                className="w-full text-left glass rounded-xl px-4 py-3 hover:bg-white/10 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-white">{bite.water_body_name}</div>
                    <div className="text-xs text-[var(--text-muted)] mt-0.5">
                      {bite.county} County · {bite.type}
                    </div>
                  </div>
                  <span className={`text-xs font-medium ${stockingColor(bite.days_ago)}`}>
                    {daysAgoLabel(bite.days_ago)}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
                  <span className="text-xs text-green-400">{bite.species}</span>
                  {bite.quantity > 0 && (
                    <span className="text-xs text-[var(--text-muted)]">
                      · {bite.quantity.toLocaleString()} fish
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
