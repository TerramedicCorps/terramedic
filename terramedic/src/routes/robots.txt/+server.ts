// filepath: /Users/lhadjchikh/Documents/GitHub.nosync/terramedic/terramedic/src/routes/robots.txt/+server.ts
import type { RequestHandler } from '@sveltejs/kit';

export const GET: RequestHandler = async () => {
  const robots = `User-agent: *
Allow: /

Sitemap: https://terramedic.org/sitemap.xml`;

  return new Response(robots.trim(), {
    headers: {
      'Content-Type': 'text/plain'
    }
  });
};
