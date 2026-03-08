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

  try {
    const response = await fetch(url);

    if (!response.ok) {
      console.error(`API error: ${response.status}`);
      return [];
    }

    return response.json();
  } catch (error) {
    console.error('Failed to fetch organizations:', error);
    return [];
  }
}
