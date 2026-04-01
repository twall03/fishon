'use client';

import { useEffect, useState } from 'react';
import { getWaterBodyDetail, type StockingEvent, type Condition, type WeatherForecast, type WaterBodySpecies } from '@/lib/supabase';

type Props = {
  waterBodyId: string | null;
  onClose: () => void;
};

function formatDate(dateStr: string) {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function daysAgo(dateStr: string) {
  const d = new Date(dateStr + 'T00:00:00');
  const now = new Date();
  const diff = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Yesterday';
  return `${diff}d ago`;
}

function timeAgo(timestamp: string) {
  const d = new Date(timestamp);
  const now = new Date();
  const mins = Math.floor((now.getTime() - d.getTime()) / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function TypeBadge({ type }: { type: string }) {
  const colors: Record<string, string> = {
    lake: 'bg-blue-500/20 text-blue-400',
    reservoir: 'bg-cyan-500/20 text-cyan-400',
    river: 'bg-teal-500/20 text-teal-400',
    creek: 'bg-emerald-500/20 text-emerald-400',
    pond: 'bg-sky-500/20 text-sky-400',
    stream: 'bg-green-500/20 text-green-400',
  };
  return (
    <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ${colors[type] || 'bg-gray-500/20 text-gray-400'}`}>
      {type}
    </span>
  );
}

export default function DetailSheet({ waterBodyId, onClose }: Props) {
  const [data, setData] = useState<{
    waterBody: any;
    stocking: StockingEvent[];
    conditions: Condition | null;
    weather: WeatherForecast[];
    species: WaterBodySpecies[];
  } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!waterBodyId) { setData(null); return; }
    setLoading(true);
    getWaterBodyDetail(waterBodyId).then(d => {
      setData(d);
      setLoading(false);
    });
  }, [waterBodyId]);

  if (!waterBodyId) return null;

  return (
    <div
      className="absolute bottom-0 left-0 right-0 z-30 transform transition-transform duration-300 ease-out"
      style={{ maxHeight: '80vh' }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 -top-[100vh] z-0" onClick={onClose} />

      {/* Sheet */}
      <div className="relative z-10 glass rounded-t-2xl overflow-hidden">
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-2">
          <div className="w-10 h-1 rounded-full bg-white/20" />
        </div>

        {loading || !data?.waterBody ? (
          <div className="px-5 pb-8 space-y-3">
            <div className="h-6 w-48 bg-white/5 rounded animate-pulse" />
            <div className="h-4 w-32 bg-white/5 rounded animate-pulse" />
            <div className="h-20 bg-white/5 rounded-lg animate-pulse" />
          </div>
        ) : (
          <div className="px-5 pb-20 overflow-y-auto" style={{ maxHeight: 'calc(80vh - 40px)' }}>
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold tracking-tight text-white">
                  {data.waterBody.name}
                </h2>
                <div className="flex items-center gap-2 mt-1">
                  <TypeBadge type={data.waterBody.type} />
                  <span className="text-xs text-[var(--text-muted)]">
                    {data.waterBody.county} County
                  </span>
                  {data.waterBody.elevation_ft && (
                    <span className="text-xs text-[var(--text-muted)]">
                      · {data.waterBody.elevation_ft.toLocaleString()}ft
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg hover:bg-white/10 transition-colors text-[var(--text-muted)]"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </button>
            </div>

            {/* Conditions Row */}
            {(data.conditions?.flow_cfs != null || data.conditions?.temp_f != null || data.conditions?.level_ft != null || data.weather.length > 0) && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">Conditions</h3>
                  <div className="flex items-center gap-2">
                    {data.conditions?.timestamp && (
                      <span className="text-[10px] text-[var(--text-muted)]">
                        {timeAgo(data.conditions.timestamp)}
                      </span>
                    )}
                    {data.conditions?.gauge_id && (
                      <a
                        href={data.conditions.gauge_id.startsWith('USGS-')
                          ? `https://waterdata.usgs.gov/monitoring-location/${data.conditions.gauge_id.replace('USGS-', '')}/`
                          : data.conditions.gauge_id.startsWith('state-parks-')
                            ? `https://stateparks.utah.gov/parks/${data.conditions.gauge_id.replace('state-parks-', '')}/current-conditions/`
                            : '#'
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] text-[var(--accent)] hover:underline"
                      >
                        {data.conditions.source || 'Source'} ↗
                      </a>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {data.conditions?.flow_cfs != null && (
                    <div className="bg-white/5 rounded-xl p-3 text-center">
                      <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Flow</div>
                      <div className="text-base font-bold text-[var(--accent)]">
                        {data.conditions.flow_cfs.toLocaleString()}
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)]">CFS</div>
                    </div>
                  )}
                  {data.conditions?.temp_f != null && (
                    <div className="bg-white/5 rounded-xl p-3 text-center">
                      <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Water</div>
                      <div className="text-base font-bold text-[var(--accent)]">
                        {data.conditions.temp_f}°
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)]">°F</div>
                    </div>
                  )}
                  {data.conditions?.level_ft != null && (
                    <div className="bg-white/5 rounded-xl p-3 text-center">
                      <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Level</div>
                      <div className="text-base font-bold text-[var(--accent)]">
                        {data.conditions.level_ft.toFixed(1)}
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)]">ft</div>
                    </div>
                  )}
                  {data.weather.length > 0 && (
                    <div className="bg-white/5 rounded-xl p-3 text-center">
                      <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-1">Tomorrow</div>
                      <div className="text-base font-bold text-white">
                        {data.weather[0]?.temp_high_f ?? '--'}°
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)]">
                        {data.weather[0]?.summary || ''}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Species */}
            {data.species.length > 0 && (
              <div className="mb-4">
                <h3 className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-2">Species</h3>
                <div className="flex flex-wrap gap-1.5">
                  {data.species.map((s) => (
                    <span
                      key={s.id}
                      className="text-xs px-2.5 py-1 rounded-full bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/20"
                    >
                      {s.species?.common_name || 'Unknown'}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Stocking */}
            {data.stocking.length > 0 && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">Recent Stocking</h3>
                  {data.stocking[0]?.source_url && (
                    <a
                      href={data.stocking[0].source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-[var(--accent)] hover:underline"
                    >
                      {data.stocking[0].source_agency || 'Source'} ↗
                    </a>
                  )}
                </div>
                <div className="space-y-1.5">
                  {data.stocking.slice(0, 5).map((s) => (
                    <div key={s.id} className="bg-white/5 rounded-lg px-3 py-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-[var(--green)]" />
                          <span className="text-sm text-white">{s.species_raw}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
                          {s.quantity != null && s.quantity > 0 && (
                            <span>{s.quantity.toLocaleString()} fish</span>
                          )}
                          <span>{daysAgo(s.date)}</span>
                        </div>
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)] mt-1 pl-4">
                        {formatDate(s.date)}{s.source_agency ? ` · ${s.source_agency}` : ''}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Weather Forecast */}
            {data.weather.length > 1 && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">Forecast</h3>
                  {data.weather[0]?.fetched_at && (
                    <span className="text-[10px] text-[var(--text-muted)]">
                      {timeAgo(data.weather[0].fetched_at)} · NOAA
                    </span>
                  )}
                </div>
                <div className="flex gap-2 overflow-x-auto pb-1">
                  {data.weather.map((w) => (
                    <div key={w.forecast_date} className="flex-shrink-0 bg-white/5 rounded-lg px-3 py-2 text-center min-w-[60px]">
                      <div className="text-[10px] text-[var(--text-muted)]">
                        {formatDate(w.forecast_date)}
                      </div>
                      <div className="text-sm font-bold text-white mt-0.5">
                        {w.temp_high_f ?? '--'}°
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)]">
                        {w.temp_low_f ?? '--'}°
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Empty state — no data at all */}
            {!data.conditions && data.species.length === 0 && data.stocking.length === 0 && data.weather.length === 0 && (
              <div className="text-center py-6">
                <div className="text-[var(--text-muted)] text-xs">
                  No fishery data available yet for this water.
                </div>
                <div className="text-[var(--text-muted)] text-[10px] mt-1">
                  Weather and conditions will appear as data sources are connected.
                </div>
              </div>
            )}

            {/* Surface acres if available */}
            {data.waterBody.surface_acres && (
              <div className="mt-3 text-[10px] text-[var(--text-muted)]">
                {data.waterBody.surface_acres.toLocaleString()} acres
                {data.waterBody.max_depth_ft ? ` · ${data.waterBody.max_depth_ft}ft max depth` : ''}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
