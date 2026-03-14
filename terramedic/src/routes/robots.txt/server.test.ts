import { describe, it, expect } from 'vitest';
import { GET } from './+server';

describe('robots.txt', () => {
  it('should allow all user agents', async () => {
    const response = await GET({} as Parameters<typeof GET>[0]);
    const text = await response.text();
    expect(text).toContain('User-agent: *');
    expect(text).toContain('Allow: /');
    expect(text).not.toContain('Disallow: /');
  });

  it('should include sitemap URL', async () => {
    const response = await GET({} as Parameters<typeof GET>[0]);
    const text = await response.text();
    expect(text).toContain('Sitemap: https://terramedic.org/sitemap.xml');
  });

  it('should return text/plain content type', async () => {
    const response = await GET({} as Parameters<typeof GET>[0]);
    expect(response.headers.get('Content-Type')).toBe('text/plain');
  });
});
