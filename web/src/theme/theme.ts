export type ThemeMode = 'light' | 'dark' | 'system';

export const THEME_STORAGE_KEY = 'atb-theme';
export const THEME_DARK_CLASS = 'dark';
export const THEME_LIGHT_CLASS = 'light';

/** Background color matching the light/dark surfaces, for the theme-color meta tag. */
export const THEME_COLORS = { light: '#f8faf7', dark: '#202825' } as const;

export function isThemeMode(value: unknown): value is ThemeMode {
  return value === 'light' || value === 'dark' || value === 'system';
}

export function readStoredTheme(storage: Pick<Storage, 'getItem'> | null | undefined): ThemeMode {
  try {
    const raw = storage?.getItem(THEME_STORAGE_KEY);
    return isThemeMode(raw) ? raw : 'system';
  } catch {
    return 'system';
  }
}

/** Apply a theme mode to the document root. `system` clears overrides so the OS media query decides. */
export function applyThemeMode(root: HTMLElement, mode: ThemeMode): void {
  root.classList.toggle(THEME_DARK_CLASS, mode === 'dark');
  root.classList.toggle(THEME_LIGHT_CLASS, mode === 'light');
  root.style.colorScheme = mode === 'system' ? '' : mode;
}

export function systemPrefersDark(win: Window | undefined): boolean {
  try {
    return typeof win?.matchMedia === 'function' && win.matchMedia('(prefers-color-scheme: dark)').matches;
  } catch {
    return false;
  }
}

/** Effective rendered theme, used for the toggle icon and the theme-color meta tag. */
export function resolveEffectiveTheme(mode: ThemeMode, prefersDark: boolean): 'light' | 'dark' {
  if (mode === 'light') return 'light';
  if (mode === 'dark') return 'dark';
  return prefersDark ? 'dark' : 'light';
}

export function syncThemeColorMeta(doc: Document | undefined, effective: 'light' | 'dark'): void {
  try {
    const meta = doc?.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', THEME_COLORS[effective]);
  } catch {
    // The meta tag is a nicety; a missing DOM must never break the toggle.
  }
}
