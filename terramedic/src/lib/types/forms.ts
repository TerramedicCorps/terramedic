/**
 * Result returned by a SvelteKit/Netlify form action and surfaced to
 * form components (ContactForm, SignupForm) via the page `form` prop.
 */
export type FormResult = {
  success?: boolean;
  error?: boolean;
  message?: string;
};
