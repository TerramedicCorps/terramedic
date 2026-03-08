import type { Actions, PageServerLoad } from './$types';
import { submitForm } from '$lib/server/submit-form';
import { fetchOrganizations } from '$lib/server/api';

export const load: PageServerLoad = async ({ request }) => {
  const lang = request.headers.get('accept-language') ?? undefined;
  const organizations = await fetchOrganizations('action', lang);
  return { organizations };
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
