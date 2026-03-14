import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock $env/static/public before importing analytics
vi.mock('$env/static/public', () => ({
  PUBLIC_GA_MEASUREMENT_ID: 'G-TEST123'
}));

const mockGtag = vi.fn();
let mockObserve: ReturnType<typeof vi.fn>;
let mockDisconnect: ReturnType<typeof vi.fn>;
let capturedCallback: ((entries: Array<{ isIntersecting: boolean }>) => void) | undefined;

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
