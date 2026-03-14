import { describe, it, expect, vi } from 'vitest';

// Mock $env/static/public before importing analytics
vi.mock('$env/static/public', () => ({
  PUBLIC_GA_MEASUREMENT_ID: 'G-TEST123'
}));

describe('analytics (server environment)', () => {
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

  describe('trackPageView', () => {
    it('should not throw in a non-browser environment', async () => {
      const { trackPageView } = await import('./analytics');
      expect(() => trackPageView('/test', 'Test Page')).not.toThrow();
    });
  });

  describe('trackEvent', () => {
    it('should not throw in a non-browser environment', async () => {
      const { trackEvent } = await import('./analytics');
      expect(() => trackEvent('test_event')).not.toThrow();
    });
  });
});
