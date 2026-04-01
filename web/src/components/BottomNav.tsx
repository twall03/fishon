'use client';

export type Tab = 'map' | 'hotbites' | 'search' | 'profile';

type Props = {
  active: Tab;
  onChange: (tab: Tab) => void;
  isLoggedIn: boolean;
};

export default function BottomNav({ active, onChange, isLoggedIn }: Props) {
  return (
    <div className="absolute bottom-0 left-0 right-0 z-30 glass border-t border-white/5 safe-bottom">
      <div className="flex items-center justify-around px-4 py-2 max-w-lg mx-auto">
        <button
          onClick={() => onChange('map')}
          className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg transition-colors ${
            active === 'map' ? 'text-[var(--accent)]' : 'text-[var(--text-muted)] hover:text-white'
          }`}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M3 7L8 4L12 7L17 4V16L12 19L8 16L3 19V7Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
          </svg>
          <span className="text-[10px] font-medium">Map</span>
        </button>

        <button
          onClick={() => onChange('hotbites')}
          className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg transition-colors ${
            active === 'hotbites' ? 'text-[var(--accent)]' : 'text-[var(--text-muted)] hover:text-white'
          }`}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 2C10 2 6 6 6 10C6 12.2 7.8 14 10 14C12.2 14 14 12.2 14 10C14 6 10 2 10 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
            <path d="M10 14V18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            <path d="M7 18H13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <span className="text-[10px] font-medium">Hot Bites</span>
        </button>

        <button
          onClick={() => onChange('search')}
          className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg transition-colors ${
            active === 'search' ? 'text-[var(--accent)]' : 'text-[var(--text-muted)] hover:text-white'
          }`}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M12.5 12.5L17 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <span className="text-[10px] font-medium">Explore</span>
        </button>

        <button
          onClick={() => onChange('profile')}
          className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg transition-colors ${
            active === 'profile' ? 'text-[var(--accent)]' : 'text-[var(--text-muted)] hover:text-white'
          }`}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="7" r="3.5" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M3.5 17.5C3.5 14.2 6.2 11.5 10 11.5C13.8 11.5 16.5 14.2 16.5 17.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <span className="text-[10px] font-medium">{isLoggedIn ? 'Profile' : 'Sign In'}</span>
        </button>
      </div>
    </div>
  );
}
