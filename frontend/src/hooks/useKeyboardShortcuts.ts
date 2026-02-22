import { useEffect, useRef } from 'react';

/**
 * Keyboard shortcuts hook
 *
 * Registers global keyboard shortcuts. Ignores events originating from
 * input, textarea, or select elements so shortcuts don't fire while typing.
 *
 * @example
 * ```tsx
 * useKeyboardShortcuts({
 *   'Ctrl+K': () => searchRef.current?.focus(),
 *   'Escape': () => setShowModal(false),
 * });
 * ```
 */
export function useKeyboardShortcuts(shortcuts: Record<string, (e: KeyboardEvent) => void>) {
  // Keep a ref to the latest shortcuts map so the effect never needs to re-subscribe
  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't fire shortcuts when focus is inside a form element
      const tag = (e.target as HTMLElement).tagName;
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return;

      // Build key combination string
      const parts: string[] = [];
      if (e.ctrlKey || e.metaKey) parts.push('Ctrl');
      if (e.shiftKey) parts.push('Shift');
      if (e.altKey) parts.push('Alt');
      parts.push(e.key);

      const combination = parts.join('+');

      const handler = shortcutsRef.current[combination];
      if (handler) {
        e.preventDefault();
        handler(e);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []); // empty deps — shortcutsRef always has the latest value
}
