'use client';

type Filter = {
  id: string;
  label: string;
  active: boolean;
};

type Props = {
  filters: Filter[];
  onToggle: (id: string) => void;
};

export default function FilterChips({ filters, onToggle }: Props) {
  return (
    <div className="absolute top-[72px] left-4 right-4 z-20 max-w-lg mx-auto">
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
        {filters.map((f) => (
          <button
            key={f.id}
            onClick={() => onToggle(f.id)}
            className={`
              flex-shrink-0 text-xs font-medium px-3 py-1.5 rounded-full
              transition-all duration-200
              ${f.active
                ? 'bg-[var(--accent)] text-white shadow-lg shadow-[var(--accent)]/20'
                : 'glass text-[var(--text-secondary)] hover:text-white'
              }
            `}
          >
            {f.label}
          </button>
        ))}
      </div>
    </div>
  );
}
