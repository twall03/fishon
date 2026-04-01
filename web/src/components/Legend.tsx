'use client';

export default function Legend() {
  return (
    <div className="absolute bottom-4 left-4 z-10 glass rounded-xl px-3 py-2 flex items-center gap-4">
      <div className="flex items-center gap-1.5">
        <div className="w-2.5 h-2.5 rounded-full bg-[var(--green)]" />
        <span className="text-[10px] text-[var(--text-muted)]">Stocked 7d</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="w-2.5 h-2.5 rounded-full bg-[var(--yellow)]" />
        <span className="text-[10px] text-[var(--text-muted)]">Stocked 30d</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="w-2.5 h-2.5 rounded-full bg-[var(--blue)]" />
        <span className="text-[10px] text-[var(--text-muted)]">Flow data</span>
      </div>
    </div>
  );
}
