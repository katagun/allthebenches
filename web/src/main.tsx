import React from 'react';
import { createRoot } from 'react-dom/client';
import Router from './Router';
import './index.css';
import './app.css';
import { applyThemeMode, readStoredTheme, resolveEffectiveTheme, syncThemeColorMeta, systemPrefersDark } from './theme/theme';

try {
  const stored = readStoredTheme(window.localStorage);
  applyThemeMode(document.documentElement, stored);
  syncThemeColorMeta(document, resolveEffectiveTheme(stored, systemPrefersDark(window)));
} catch {
  // The default system theme already applies through CSS; a failed init must not block render.
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><Router /></React.StrictMode>);
