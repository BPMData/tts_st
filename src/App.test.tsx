import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { strings } from '../shared/strings.ts';
import { App } from './App.tsx';

const pwa = vi.hoisted(() => ({
  offlineReady: false,
  needRefresh: false,
  updateServiceWorker: vi.fn().mockResolvedValue(undefined),
  onRegisterError: undefined as undefined | (() => void),
}));

vi.mock('virtual:pwa-register/react', () => ({
  useRegisterSW: (options: { onRegisterError: () => void }) => {
    pwa.onRegisterError = options.onRegisterError;
    return {
      offlineReady: [pwa.offlineReady],
      needRefresh: [pwa.needRefresh],
      updateServiceWorker: pwa.updateServiceWorker,
    };
  },
}));

beforeEach(() => {
  pwa.offlineReady = false;
  pwa.needRefresh = false;
  pwa.updateServiceWorker.mockClear();
  vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
});
afterEach(cleanup);

describe('app accessibility and offline feedback', () => {
  it('offers a skip link to the main content and installation instructions', () => {
    render(<App />);
    const main = screen.getByRole('main');
    expect(screen.getByRole('link', { name: strings.skipLink }).getAttribute('href')).toBe(`#${main.id}`);
    expect(main.tabIndex).toBe(-1);
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe(strings.welcome);
    fireEvent.click(screen.getByText(strings.installTitle));
    expect(screen.getByText(strings.installChrome)).toBeDefined();
  });

  it('announces loss and return of a connection without reloading', () => {
    render(<App />);
    const status = screen.getByRole('status');
    expect(status.getAttribute('aria-live')).toBe('polite');
    expect(status.textContent).toContain(strings.online);
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false);
    fireEvent(window, new Event('offline'));
    expect(status.textContent).toContain(strings.offline);
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
    fireEvent(window, new Event('online'));
    expect(status.textContent).toContain(strings.online);
  });

  it('starts with an offline message when opened without a connection', () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false);
    render(<App />);
    expect(screen.getByRole('status').textContent).toContain(strings.offline);
  });

  it('reports a failed registration without claiming offline readiness', () => {
    render(<App />);
    act(() => pwa.onRegisterError?.());
    expect(screen.getByRole('status').textContent).toContain(strings.offlineError);
    expect(screen.queryByText(strings.offlineReady)).toBeNull();
  });

  it('announces when the app is saved for offline use', () => {
    pwa.offlineReady = true;
    render(<App />);
    expect(screen.getByRole('status').textContent).toContain(strings.offlineReady);
  });

  it('waits for the user before applying an update', () => {
    pwa.needRefresh = true;
    render(<App />);
    expect(pwa.updateServiceWorker).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: strings.update }));
    expect(pwa.updateServiceWorker).toHaveBeenCalledWith(true);
  });
});
