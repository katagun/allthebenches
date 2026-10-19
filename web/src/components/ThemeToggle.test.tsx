import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { ThemeToggle } from './ThemeToggle';
import { THEME_STORAGE_KEY } from '../theme/theme';

beforeEach(() => {
  window.localStorage.clear();
  document.documentElement.classList.remove('dark', 'light');
});

afterEach(() => {
  cleanup();
  window.localStorage.clear();
  document.documentElement.classList.remove('dark', 'light');
});

describe('ThemeToggle', () => {
  it('defaults to system with no theme classes applied', () => {
    render(<ThemeToggle />);
    expect(screen.getByRole('button', { name: /theme: system/i })).toBeTruthy();
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(document.documentElement.classList.contains('light')).toBe(false);
  });

  it('opens a menu with light, dark, and system options', async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);
    await user.click(screen.getByRole('button', { name: /change theme/i }));
    expect(screen.getByRole('menu', { name: /color theme/i })).toBeTruthy();
    for (const label of ['Light', 'Dark', 'System']) {
      expect(screen.getByRole('menuitemradio', { name: label })).toBeTruthy();
    }
  });

  it('selects dark: applies the class and persists it', async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);
    await user.click(screen.getByRole('button', { name: /change theme/i }));
    await user.click(screen.getByRole('menuitemradio', { name: 'Dark' }));
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark');
    expect(screen.getByRole('button', { name: /theme: dark/i })).toBeTruthy();
  });

  it('selects light: applies the class and persists it', async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);
    await user.click(screen.getByRole('button', { name: /change theme/i }));
    await user.click(screen.getByRole('menuitemradio', { name: 'Light' }));
    expect(document.documentElement.classList.contains('light')).toBe(true);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('light');
  });

  it('returns to system: clears theme classes', async () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, 'dark');
    document.documentElement.classList.add('dark');
    const user = userEvent.setup();
    render(<ThemeToggle />);
    await user.click(screen.getByRole('button', { name: /theme: dark/i }));
    await user.click(screen.getByRole('menuitemradio', { name: 'System' }));
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(document.documentElement.classList.contains('light')).toBe(false);
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('system');
  });

  it('restores the stored theme on mount', () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, 'light');
    document.documentElement.classList.add('light');
    render(<ThemeToggle />);
    expect(screen.getByRole('button', { name: /theme: light/i })).toBeTruthy();
  });

  it('closes the menu with Escape', async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);
    await user.click(screen.getByRole('button', { name: /change theme/i }));
    expect(screen.queryByRole('menu')).toBeTruthy();
    await user.keyboard('{Escape}');
    expect(screen.queryByRole('menu')).toBeNull();
  });
});
