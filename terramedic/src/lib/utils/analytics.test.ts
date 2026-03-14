import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock $env/static/public before importing analytics
vi.mock('$env/static/public', () => ({
  PUBLIC_GA_MEASUREMENT_ID: 'G-TEST123'
}));

const mockGtag = vi.fn();

describe('analytics', () => {
  beforeEach(() => {
    vi.resetModules();
    mockGtag.mockClear();
    // Set up global gtag
    (globalThis as Record<string, unknown>).gtag = mockGtag;
  });

  describe('trackPageView', () => {
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

  describe('GA_MEASUREMENT_ID', () => {
    it('should export the measurement ID from env', async () => {
      const { GA_MEASUREMENT_ID } = await import('./analytics');
      expect(GA_MEASUREMENT_ID).toBe('G-TEST123');
    });
  });

  describe('initAnalytics', () => {
    it('should not throw in a non-browser environment', async () => {
      const { initAnalytics } = await import('./analytics');
      expect(() => initAnalytics()).not.toThrow();
    });
  });
});
