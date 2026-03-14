/**
 * Google Analytics utility functions for tracking page views and events
 */

import { PUBLIC_GA_MEASUREMENT_ID } from '$env/static/public';

export const GA_MEASUREMENT_ID = PUBLIC_GA_MEASUREMENT_ID;

/**
 * Dynamically load the Google Analytics gtag.js script and initialize it.
 * This replaces the hardcoded snippet previously in app.html.
 */
export function initAnalytics(): void {
  if (typeof window === 'undefined' || !GA_MEASUREMENT_ID) return;

  // Avoid loading twice
  if (document.querySelector(`script[src*="googletagmanager.com/gtag/js"]`)) return;

  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  document.head.appendChild(script);

  window.dataLayer = window.dataLayer || [];
  window.gtag = function () {
    // eslint-disable-next-line prefer-rest-params
    window.dataLayer.push(arguments);
  };
  window.gtag('js', new Date());
  window.gtag('config', GA_MEASUREMENT_ID);
}

/**
 * Track a page view with Google Analytics
 * @param url - The URL of the page view to track
 * @param title - The title of the page
 */
export function trackPageView(url: string, title: string): void {
  if (typeof gtag !== 'undefined') {
    gtag('config', GA_MEASUREMENT_ID, {
      page_path: url,
      page_title: title
    });
  }
}

/**
 * Track an event with Google Analytics
 * @param eventName - The name of the event to track
 * @param eventParams - Additional parameters to include with the event
 */
export function trackEvent(eventName: string, eventParams: Record<string, unknown> = {}): void {
  if (typeof gtag !== 'undefined') {
    gtag('event', eventName, eventParams);
  }
}

/**
 * Initialize page view tracking in SvelteKit
 * This should be called from the root +layout.svelte
 * @param navigation - The navigation object
 */
export function initPageTracking(navigation: {
  subscribe: (callback: (data: { url: URL }) => void) => void;
}): void {
  if (typeof window !== 'undefined') {
    // Track initial page view
    trackPageView(window.location.pathname, document.title);

    // Track navigation changes
    navigation.subscribe(({ url }) => {
      if (url) {
        trackPageView(url.pathname, document.title);
      }
    });
  }
}
