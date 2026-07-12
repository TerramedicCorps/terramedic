import { describe, test, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import ImageModal from './ImageModal.svelte';

describe('ImageModal', () => {
  const baseProps = {
    show: true,
    imageSrc: '/images/test.png',
    imageAlt: 'Test image'
  };

  test('close button invokes the onclose callback', async () => {
    const onclose = vi.fn();
    const { container } = render(ImageModal, { props: { ...baseProps, onclose } });
    const closeButton = container.querySelector('button[aria-label="Close"]');
    expect(closeButton).toBeInTheDocument();
    await fireEvent.click(closeButton as Element);
    expect(onclose).toHaveBeenCalledTimes(1);
  });

  test('backdrop click invokes the onclose callback', async () => {
    const onclose = vi.fn();
    render(ImageModal, { props: { ...baseProps, onclose } });
    // The backdrop is the outer role="button" wrapper; the inner
    // <button> close control shares the "Close" name, so pick the
    // backdrop by document order.
    const [backdrop] = screen.getAllByRole('button', { name: 'Close' });
    await fireEvent.click(backdrop);
    expect(onclose).toHaveBeenCalledTimes(1);
  });

  test('Escape key invokes the onclose callback', async () => {
    const onclose = vi.fn();
    render(ImageModal, { props: { ...baseProps, onclose } });
    await fireEvent.keyDown(window, { key: 'Escape' });
    expect(onclose).toHaveBeenCalledTimes(1);
  });

  test('clicking the image content does not close the modal', async () => {
    const onclose = vi.fn();
    render(ImageModal, { props: { ...baseProps, onclose } });
    await fireEvent.click(screen.getByRole('dialog'));
    expect(onclose).not.toHaveBeenCalled();
  });
});
