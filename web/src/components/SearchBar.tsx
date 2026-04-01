'use client';

import { useState, useRef, useEffect } from 'react';
import { searchWaterBodies } from '@/lib/supabase';

type Props = {
  onSelect: (id: string) => void;
};

export default function SearchBar({ onSelect }: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (!query || query.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }

    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(async () => {
      const data = await searchWaterBodies(query);
      // Deduplicate by water_body_id
      const seen = new Set();
      const unique = data.filter((d: any) => {
        const id = d.water_body_id || d.water_bodies?.id;
        if (seen.has(id)) return false;
        seen.add(id);
        return true;
      });
      setResults(unique.slice(0, 8));
      setOpen(unique.length > 0);
    }, 250);

    return () => clearTimeout(timeoutRef.current);
  }, [query]);

  return (
    <div className="absolute top-4 left-4 right-4 z-20 max-w-lg mx-auto">
      {/* Search Input */}
      <div className="glass rounded-2xl overflow-hidden shadow-2xl shadow-black/40">
        <div className="flex items-center px-4 py-3 gap-3">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" className="text-[var(--text-muted)] flex-shrink-0">
            <circle cx="7.5" cy="7.5" r="5.5" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M11.5 11.5L16 16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search waters..."
            className="flex-1 bg-transparent text-sm text-white placeholder:text-[var(--text-muted)] outline-none"
          />
          {query && (
            <button
              onClick={() => { setQuery(''); setOpen(false); }}
              className="text-[var(--text-muted)] hover:text-white transition-colors"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M3 3L11 11M11 3L3 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </button>
          )}
        </div>

        {/* Results Dropdown */}
        {open && (
          <div className="border-t border-white/5">
            {results.map((r) => {
              const wb = r.water_bodies;
              const id = r.water_body_id || wb?.id;
              return (
                <button
                  key={id}
                  onClick={() => {
                    onSelect(id);
                    setQuery('');
                    setOpen(false);
                    inputRef.current?.blur();
                  }}
                  className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-white/5 transition-colors text-left"
                >
                  <div>
                    <div className="text-sm text-white">{wb?.name || r.alias}</div>
                    <div className="text-[11px] text-[var(--text-muted)]">
                      {wb?.county} County · {wb?.type}
                    </div>
                  </div>
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="text-[var(--text-muted)]">
                    <path d="M5 3L9 7L5 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
