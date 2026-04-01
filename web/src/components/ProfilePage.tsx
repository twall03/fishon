'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

type Props = {
  visible: boolean;
  user: any;
  onClose: () => void;
  onSelectWater: (id: string) => void;
};

type Waypoint = {
  id: string;
  name: string;
  description: string | null;
  icon: string;
  color: string;
  water_body_id: string | null;
  created_at: string;
};

type CatchLog = {
  id: string;
  species_text: string | null;
  length_inches: number | null;
  weight_lbs: number | null;
  method: string | null;
  lure_or_fly: string | null;
  notes: string | null;
  caught_at: string;
  water_body_id: string | null;
  species: { common_name: string } | null;
  water_bodies: { name: string } | null;
};

type Note = {
  id: string;
  title: string | null;
  body: string;
  created_at: string;
  water_bodies: { name: string } | null;
};

export default function ProfilePage({ visible, user, onClose, onSelectWater }: Props) {
  const [tab, setTab] = useState<'waypoints' | 'catches' | 'notes'>('waypoints');
  const [waypoints, setWaypoints] = useState<Waypoint[]>([]);
  const [catches, setCatches] = useState<CatchLog[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!visible || !user) return;
    setLoading(true);

    async function load() {
      const [wp, cl, nt] = await Promise.all([
        supabase.from('waypoints').select('*').eq('user_id', user.id).order('created_at', { ascending: false }),
        supabase.from('catch_logs').select('*, species(common_name), water_bodies(name)').eq('user_id', user.id).order('caught_at', { ascending: false }).limit(20),
        supabase.from('notes').select('*, water_bodies(name)').eq('user_id', user.id).order('created_at', { ascending: false }).limit(20),
      ]);

      setWaypoints(wp.data || []);
      setCatches(cl.data || []);
      setNotes(nt.data || []);
      setLoading(false);
    }
    load();
  }, [visible, user]);

  if (!visible) return null;

  return (
    <div className="absolute inset-0 z-40 flex flex-col bg-[var(--bg-primary)]">
      {/* Header */}
      <div className="px-5 pt-5 pb-3">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">My Fishing</h1>
            <p className="text-xs text-[var(--text-muted)]">{user?.email}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={async () => { await supabase.auth.signOut(); onClose(); }}
              className="text-xs text-[var(--text-muted)] hover:text-white px-3 py-1.5 rounded-lg hover:bg-white/5 transition-colors"
            >
              Sign Out
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors text-[var(--text-muted)]"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M5 5L15 15M15 5L5 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-white/5 rounded-xl p-1">
          {[
            { id: 'waypoints' as const, label: 'Waypoints', count: waypoints.length },
            { id: 'catches' as const, label: 'Catches', count: catches.length },
            { id: 'notes' as const, label: 'Notes', count: notes.length },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex-1 text-xs font-medium py-2 rounded-lg transition-colors ${
                tab === t.id
                  ? 'bg-[var(--accent)] text-white'
                  : 'text-[var(--text-muted)] hover:text-white'
              }`}
            >
              {t.label} {t.count > 0 && `(${t.count})`}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 pb-20">
        {loading ? (
          <div className="space-y-3 mt-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-white/5 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : (
          <>
            {/* Waypoints tab */}
            {tab === 'waypoints' && (
              <div className="mt-4">
                {waypoints.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-3xl mb-3">📍</div>
                    <div className="text-sm text-[var(--text-muted)]">No waypoints yet</div>
                    <div className="text-xs text-[var(--text-muted)] mt-1">Long press on the map to drop a pin</div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {waypoints.map(wp => (
                      <div key={wp.id} className="glass rounded-xl px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm" style={{ backgroundColor: wp.color + '20', color: wp.color }}>
                            📍
                          </div>
                          <div className="flex-1">
                            <div className="text-sm font-medium text-white">{wp.name}</div>
                            {wp.description && <div className="text-xs text-[var(--text-muted)]">{wp.description}</div>}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Catches tab */}
            {tab === 'catches' && (
              <div className="mt-4">
                {catches.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-3xl mb-3">🐟</div>
                    <div className="text-sm text-[var(--text-muted)]">No catches logged yet</div>
                    <div className="text-xs text-[var(--text-muted)] mt-1">Log your first catch from a water body detail card</div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {catches.map(c => (
                      <button
                        key={c.id}
                        onClick={() => c.water_body_id && onSelectWater(c.water_body_id)}
                        className="w-full text-left glass rounded-xl px-4 py-3"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-sm font-medium text-white">
                              {c.species?.common_name || c.species_text || 'Unknown species'}
                            </div>
                            <div className="text-xs text-[var(--text-muted)]">
                              {c.water_bodies?.name || 'Unknown water'}
                              {c.length_inches ? ` · ${c.length_inches}"` : ''}
                              {c.weight_lbs ? ` · ${c.weight_lbs} lbs` : ''}
                            </div>
                          </div>
                          <div className="text-xs text-[var(--text-muted)]">
                            {new Date(c.caught_at).toLocaleDateString()}
                          </div>
                        </div>
                        {c.method && (
                          <div className="text-xs text-[var(--accent)] mt-1">{c.method}{c.lure_or_fly ? ` — ${c.lure_or_fly}` : ''}</div>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Notes tab */}
            {tab === 'notes' && (
              <div className="mt-4">
                {notes.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-3xl mb-3">📝</div>
                    <div className="text-sm text-[var(--text-muted)]">No notes yet</div>
                    <div className="text-xs text-[var(--text-muted)] mt-1">Add notes from any water body detail card</div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {notes.map(n => (
                      <div key={n.id} className="glass rounded-xl px-4 py-3">
                        {n.title && <div className="text-sm font-medium text-white">{n.title}</div>}
                        <div className="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2">{n.body}</div>
                        <div className="text-[10px] text-[var(--text-muted)] mt-2">
                          {n.water_bodies?.name || 'General'}
                          {' · '}
                          {new Date(n.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
