import type { PageServerLoad } from './$types';
import { fetchOrganizations } from '$lib/server/api';

export const load: PageServerLoad = ({ request }) => {
  const acceptLanguage = request.headers.get('accept-language') ?? undefined;
  // Streaming SSR: return the promise rather than awaiting so SvelteKit
  // sends the page shell immediately and streams the org list when the
  // API responds. The component uses {#await} to show a skeleton until
  // the promise resolves.
  return {
    organizations: fetchOrganizations('donate', acceptLanguage).catch((error) => {
      console.error('Failed to load donate organizations:', error);
      throw error;
    })
  };
};
