'use client';

type MapStyle = 'outdoors' | 'satellite' | 'topo';

type Props = {
  activeStyle: MapStyle;
  onStyleChange: (style: MapStyle) => void;
};

export default function MapControls({ activeStyle, onStyleChange }: Props) {
  const styles: { id: MapStyle; label: string; icon: string }[] = [
    { id: 'outdoors', label: 'Terrain', icon: '⛰' },
    { id: 'satellite', label: 'Satellite', icon: '🛰' },
    { id: 'topo', label: 'Topo', icon: '📐' },
  ];

  return (
    <div className="absolute top-[72px] right-4 z-20 flex flex-col gap-1">
      {styles.map(s => (
        <button
          key={s.id}
          onClick={() => onStyleChange(s.id)}
          className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm transition-all ${
            activeStyle === s.id
              ? 'glass border-[var(--accent)] shadow-lg shadow-[var(--accent)]/10 text-white'
              : 'glass text-[var(--text-muted)] hover:text-white'
          }`}
          title={s.label}
        >
          {s.icon}
        </button>
      ))}
    </div>
  );
}
