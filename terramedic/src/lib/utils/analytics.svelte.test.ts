import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock $env/static/public before importing analytics
vi.mock('$env/static/public', () => ({
  PUBLIC_GA_MEASUREMENT_ID: 'G-TEST123'
}));

const mockGtag = vi.fn();
let mockObserve: ReturnType<typeof vi.fn>;
let mockDisconnect: ReturnType<typeof vi.fn>;
let capturedCallback: ((entries: Array<{ isIntersecting: boolean }>) => void) | undefined;

describe('trackPageView', () => {
  beforeEach(() => {
    vi.resetModules();
    mockGtag.mockClear();
    (globalThis as Record<string, unknown>).gtag = mockGtag;
  });

  it('should call gtag config with the measurement ID from env', async () => {
    const { trackPageView } = await import('./analytics');
    trackPageView('/test', 'Test Page');

    expect(mockGtag).toHaveBeenCalledWith('config', 'G-TEST123', {
      page_path: '/test',
      page_title: 'Test Page'
    });
  });

  it('should not throw if gtag is undefined', async () => {
    delete (globalThis as Record<string, unknown>).gtag;
    const { trackPageView } = await import('./analytics');

    expect(() => trackPageView('/test', 'Test Page')).not.toThrow();
  });
});

describe('trackEvent', () => {
  beforeEach(() => {
    vi.resetModules();
    mockGtag.mockClear();
    (globalThis as Record<string, unknown>).gtag = mockGtag;
  });

  it('should call gtag event with provided params', async () => {
    const { trackEvent } = await import('./analytics');
    trackEvent('test_event', { key: 'value' });

    expect(mockGtag).toHaveBeenCalledWith('event', 'test_event', { key: 'value' });
  });

  it('should default to empty params', async () => {
    const { trackEvent } = await import('./analytics');
    trackEvent('test_event');

    expect(mockGtag).toHaveBeenCalledWith('event', 'test_event', {});
  });
});

describe('trackSectionView', () => {
  beforeEach(() => {
    vi.resetModules();
    mockGtag.mockClear();
    (globalThis as Record<string, unknown>).gtag = mockGtag;

    mockObserve = vi.fn();
    mockDisconnect = vi.fn();
    capturedCallback = undefined;

    // Use a class-style mock so it can be called with `new`
    vi.stubGlobal(
      'IntersectionObserver',
      class {
        constructor(cb: (entries: Array<{ isIntersecting: boolean }>) => void) {
          capturedCallback = cb;
        }
        observe = mockObserve;
        disconnect = mockDisconnect;
      }
    );
  });

  it('should return a Svelte action that observes the element', async () => {
    const { trackSectionView } = await import('./analytics');
    const el = document.createElement('div');
    const result = trackSectionView(el, { section: 'hero', page: 'home' });

    expect(mockObserve).toHaveBeenCalledWith(el);
    expect(result).toHaveProperty('destroy');
  });

  it('should fire section_view event when element becomes visible', async () => {
    const { trackSectionView } = await import('./analytics');
    const el = document.createElement('div');
    trackSectionView(el, { section: 'action_cards', page: 'home' });

    capturedCallback!([{ isIntersecting: true }]);

    expect(mockGtag).toHaveBeenCalledWith('event', 'section_view', {
      section: 'action_cards',
      page: 'home'
    });
    expect(mockDisconnect).toHaveBeenCalled();
  });

  it('should not fire event when element is not intersecting', async () => {
    const { trackSectionView } = await import('./analytics');
    const el = document.createElement('div');
    trackSectionView(el, { section: 'hero', page: 'home' });

    capturedCallback!([{ isIntersecting: false }]);

    expect(mockGtag).not.toHaveBeenCalledWith('event', 'section_view', expect.anything());
  });
});
