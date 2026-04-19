import type { PageServerLoad } from './$types';
import { loadOrganizations } from '$lib/server/api';

export const load: PageServerLoad = ({ request }) => loadOrganizations('volunteer', request);
