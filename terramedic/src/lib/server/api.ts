import { env } from '$env/dynamic/private';

const API_BASE = env.API_BASE || 'http://localhost:8000/api';

export interface Organization {
  id: number;
  name: string;
  description: string;
  action_text: string;
  website_url: string;
  image_url: string;
  category: string;
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
