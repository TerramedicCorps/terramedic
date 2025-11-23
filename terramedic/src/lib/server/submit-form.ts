export async function submitForm(formData: FormData): Promise<'success' | 'error'> {
  try {
    const res = await fetch('https://terramedic.netlify.app/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams(formData as unknown as Record<string, string>).toString()
    });

    return res.ok ? 'success' : 'error';
  } catch {
    return 'error';
  }
}
