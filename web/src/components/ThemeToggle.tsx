import { Check, Monitor, Moon, Sun } from 'lucide-react';
import { useEffect, useId, useRef, useState } from 'react';
import { useTheme } from '../theme/useTheme';
import type { ThemeMode } from '../theme/theme';

const OPTIONS: { value: ThemeMode; label: string; Icon: typeof Sun }[] = [
  { value: 'light', label: 'Light', Icon: Sun },
  { value: 'dark', label: 'Dark', Icon: Moon },
  { value: 'system', label: 'System', Icon: Monitor },
];

const BUTTON_LABELS: Record<ThemeMode, string> = {
  light: 'Theme: light. Change theme',
  dark: 'Theme: dark. Change theme',
  system: 'Theme: system. Change theme',
};

export function ThemeToggle() {
  const { mode, setMode } = useTheme();
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const menuId = useId();
  const ActiveIcon = OPTIONS.find(option => option.value === mode)?.Icon ?? Monitor;

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!wrapRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('pointerdown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open ]);

  return (
    <div className="theme-toggle" ref={wrapRef}>
      <button
        type="button"
        className="theme-toggle-button"
        aria-label={BUTTON_LABELS[mode]}
        title={BUTTON_LABELS[mode]}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen(value => !value)}
      >
        <ActiveIcon aria-hidden="true" width="18" height="18" />
      </button>
      {open && (
        <div className="theme-menu" role="menu" id={menuId} aria-label="Color theme">
          {OPTIONS.map(({ value, label, Icon }) => (
            <button
              key={value}
              type="button"
              role="menuitemradio"
              aria-checked={mode === value}
              className="theme-menu-item"
              data-active={mode === value || undefined}
              onClick={() => {
                setMode(value);
                setOpen(false);
              }}
            >
              <Icon aria-hidden="true" width="15" height="15" />
              <span>{label}</span>
              {mode === value && <Check aria-hidden="true" width="14" height="14" className="theme-menu-check" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
