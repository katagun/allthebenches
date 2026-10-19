import { useCallback, useSyncExternalStore } from 'react';
import {
  applyThemeMode,
  readStoredTheme,
  resolveEffectiveTheme,
  syncThemeColorMeta,
  systemPrefersDark,
  THEME_STORAGE_KEY,
  type ThemeMode,
} from './theme';

function getStorage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function currentDocumentMode(): ThemeMode {
  return readStoredTheme(getStorage());
}

function persistMode(mode: ThemeMode): void {
  try {
    getStorage()?.setItem(THEME_STORAGE_KEY, mode);
  } catch {
    // Private-mode storage must not break theming; the class still applies below.
  }
  if (typeof document !== 'undefined') {
    applyThemeMode(document.documentElement, mode);
    syncThemeColorMeta(document, resolveEffectiveTheme(mode, systemPrefersDark(window)));
  }
  window.dispatchEvent(new CustomEvent<ThemeMode>('atb-theme-change', { detail: mode }));
}

function subscribe(notify: () => void): () => void {
  const onChange = () => notify();
  window.addEventListener('atb-theme-change', onChange);
  window.addEventListener('storage', onChange);
  return () => {
    window.removeEventListener('atb-theme-change', onChange);
    window.removeEventListener('storage', onChange);
  };
}

function snapshot(): ThemeMode {
  return currentDocumentMode();
}

/** Shared theme state: every toggle instance reads and writes the same mode. */
export function useTheme(): { mode: ThemeMode; effective: 'light' | 'dark'; setMode: (mode: ThemeMode) => void } {
  const mode = useSyncExternalStore(subscribe, snapshot, () => 'system' as ThemeMode);
  const setMode = useCallback((next: ThemeMode) => {
    persistMode(next);
  }, []);
  return { mode, effective: resolveEffectiveTheme(mode, systemPrefersDark(typeof window === 'undefined' ? undefined : window)), setMode };
}
