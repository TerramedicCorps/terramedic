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

export async function fetchOrganizations(category?: string): Promise<Organization[]> {
  const url = category
    ? `${API_BASE}/organizations/?category=${category}`
    : `${API_BASE}/organizations/`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}
