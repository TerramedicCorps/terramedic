import type { PageServerLoad } from './$types';
import { fetchOrganizations } from '$lib/server/api';

export const prerender = true;

export const load: PageServerLoad = async ({ request }) => {
  const acceptLanguage = request.headers.get('accept-language') ?? undefined;
  try {
    const organizations = await fetchOrganizations('volunteer', acceptLanguage);
    return { organizations };
  } catch (error) {
    console.error('Failed to load organizations:', error);
    return { organizations: [] };
  }
};
