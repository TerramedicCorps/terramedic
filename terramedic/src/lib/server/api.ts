import { env } from '$env/dynamic/private';

const API_BASE = env.API_BASE || 'http://localhost:8000/api';

export interface Organization {
  id: number;
  name: string;
  description: string;
  action_text: string;
  website_url: string;
  image_url: string;
  categories: string[];
  tags: string[];
  sort_order: number;
}

export async function fetchOrganizations(
  category?: string,
  acceptLanguage?: string
): Promise<Organization[]> {
  const params = new URLSearchParams();
  if (category) params.set('category', category);
  const query = params.toString();
  const url = `${API_BASE}/organizations/${query ? `?${query}` : ''}`;

  const headers: Record<string, string> = {};
  if (acceptLanguage) headers['Accept-Language'] = acceptLanguage;
  const response = await fetch(url, { headers });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return await response.json();
}

/**
 * Build a streaming SSR `load` result that fetches organizations for
 * the given category. The returned object contains an unresolved
 * Promise so SvelteKit streams the list to the client while the
 * page shell renders immediately.
 */
export function loadOrganizations(
  category: string,
  request: Request
): { organizations: Promise<Organization[]> } {
  const acceptLanguage = request.headers.get('accept-language') ?? undefined;
  return {
    organizations: fetchOrganizations(category, acceptLanguage).catch((error) => {
      // Structured log so aggregators can pivot on category; rethrow
      // so the client's {:catch} branch renders the error message.
      console.error('fetchOrganizations failed', {
        category,
        message: error instanceof Error ? error.message : String(error)
      });
      throw error;
    })
  };
}
