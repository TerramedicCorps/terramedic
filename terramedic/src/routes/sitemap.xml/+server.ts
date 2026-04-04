import type { RequestHandler } from '@sveltejs/kit';

export const GET: RequestHandler = async () => {
  const baseUrl = 'https://terramedic.org';

  const pages: string[] = [
    '/',
    '/about',
    '/warming-stripes',
    '/volunteer',
    '/donate',
    '/other-actions',
    '/resources',
    '/careers',
    '/contact-us',
    '/privacy',
    '/methodology'
  ];

  const sitemap: string = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${pages
    .map(
      (page) => `
    <url>
      <loc>${baseUrl}${page}</loc>
      <changefreq>weekly</changefreq>
      <priority>${page === '/' ? '1.0' : '0.8'}</priority>
    </url>
  `
    )
    .join('')}
</urlset>`;

  return new Response(sitemap.trim(), {
    headers: {
      'Content-Type': 'application/xml'
    }
  });
};
