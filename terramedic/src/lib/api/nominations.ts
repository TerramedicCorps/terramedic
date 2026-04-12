/**
 * Nominations API client.
 *
 * Calls the Django backend at POST /api/nominations/ and
 * GET /api/nominations/{id}/status/.
 */

import { env } from '$env/dynamic/public';

const API_BASE = env.PUBLIC_API_BASE || 'http://localhost:8000/api';

export class ValidationError extends Error {
  fields: Record<string, string>;
  constructor(fields: Record<string, string>) {
    const firstMessage = Object.values(fields)[0] || 'Validation failed';
    super(firstMessage);
    this.name = 'ValidationError';
    this.fields = fields;
  }
}

export interface NominationPayload {
  url: string;
  categories: string[];
  notes: string;
  website?: string;
}

export interface NominationResponse {
  confirmation_id: string;
}

export interface NominationStatus {
  confirmation_id: string;
  status: 'pending' | 'evaluating' | 'evaluated' | 'approved' | 'rejected';
  display_url: string;
  submitted_at: string;
}

/**
 * Submit a nomination to the API.
 */
export async function submitNomination(payload: NominationPayload): Promise<NominationResponse> {
  const response = await fetch(`${API_BASE}/nominations/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (response.status === 422) {
    const data = await response.json();
    // Django Ninja returns validation errors as { detail: [...] }
    const fields: Record<string, string> = {};
    if (Array.isArray(data.detail)) {
      for (const err of data.detail) {
        const field = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : 'general';
        fields[field] = err.msg;
      }
    }
    throw new ValidationError(fields);
  }

  if (response.status === 429) {
    throw new Error('Too many nominations submitted. Please try again later.');
  }

  if (!response.ok) {
    throw new Error('Something went wrong. Please try again.');
  }

  return await response.json();
}

/**
 * Look up the status of a nomination by confirmation ID.
 */
export async function lookupNominationStatus(confirmationId: string): Promise<NominationStatus> {
  const trimmed = confirmationId.trim();

  if (!trimmed) {
    throw new Error('Confirmation ID is required');
  }

  const response = await fetch(`${API_BASE}/nominations/${encodeURIComponent(trimmed)}/status/`);

  if (response.status === 422) {
    throw new Error('Invalid confirmation ID format');
  }

  if (response.status === 404) {
    throw new Error('Nomination not found');
  }

  if (!response.ok) {
    throw new Error('Something went wrong. Please try again.');
  }

  return await response.json();
}
