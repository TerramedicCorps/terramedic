import type { Actions, PageServerLoad } from './$types';
import { submitForm } from '$lib/server/submit-form';
import { fetchOrganizations } from '$lib/server/api';

export const load: PageServerLoad = async ({ request }) => {
  const acceptLanguage = request.headers.get('accept-language') ?? undefined;
  try {
    const organizations = await fetchOrganizations('action', acceptLanguage);
    return { organizations };
  } catch (error) {
    console.error('Failed to load organizations:', error);
    return { organizations: [] };
  }
};

export const actions: Actions = {
  default: async ({ request }) => {
    const formData = await request.formData();
    const formName = formData.get('form-name');

    // Only handle newsletter signup from footer on this page
    if (formName !== 'newsletter-signup') {
      return { error: true, message: 'Invalid form submission' };
    }

    const result = await submitForm(formData);
    return result === 'success' ? { success: true } : { error: true };
  }
};
