/**
 * Nominations API client with mock implementation.
 *
 * The backend endpoint (POST /api/nominations/, GET /api/nominations/{id}/status)
 * is being built on another branch. This module provides a mock that returns
 * realistic responses for development and testing. Replace the mock functions
 * with real fetch calls once the backend is available.
 */

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
  url: string;
  created_at: string;
}

/**
 * Submit a nomination to the API.
 * Currently mocked — returns a generated confirmation ID after a short delay.
 */
export async function submitNomination(payload: NominationPayload): Promise<NominationResponse> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 600));

  // Validate URL is present (backend would also validate)
  if (!payload.url) {
    throw new Error('URL is required');
  }

  if (payload.categories.length === 0) {
    throw new Error('At least one category is required');
  }

  // Generate a mock confirmation ID
  const id = `NOM-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).substring(2, 6).toUpperCase()}`;

  return { confirmation_id: id };
}

/**
 * Look up the status of a nomination by confirmation ID.
 * Currently mocked — always returns "pending" for valid-looking IDs.
 */
export async function lookupNominationStatus(confirmationId: string): Promise<NominationStatus> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 400));

  const trimmed = confirmationId.trim();

  if (!trimmed) {
    throw new Error('Confirmation ID is required');
  }

  // Mock: any ID starting with "NOM-" is treated as valid
  if (!trimmed.startsWith('NOM-')) {
    throw new Error('Nomination not found');
  }

  return {
    confirmation_id: trimmed,
    status: 'pending',
    url: 'https://example.org',
    created_at: new Date().toISOString()
  };
}
