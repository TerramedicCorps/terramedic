import type { PageServerLoad } from './$types';
import { fetchOrganizations } from '$lib/server/api';

export const prerender = true;

export const load: PageServerLoad = async ({ request }) => {
  // NOTE: accept-language is empty at prerender time. This is fine while
  // content is English-only but will need revisiting when translations are added.
  const acceptLanguage = request.headers.get('accept-language') ?? undefined;
  try {
    const organizations = await fetchOrganizations('resource', acceptLanguage);
    return { organizations };
  } catch (error) {
    console.error('Failed to load organizations:', error);
    return { organizations: [] };
  }
};
