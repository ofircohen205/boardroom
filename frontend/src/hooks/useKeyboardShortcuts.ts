import { useEffect } from 'react';

/**
 * Keyboard shortcuts hook
 *
 * Registers global keyboard shortcuts
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
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Build key combination string
      const parts: string[] = [];

      if (e.ctrlKey || e.metaKey) parts.push('Ctrl');
      if (e.shiftKey) parts.push('Shift');
      if (e.altKey) parts.push('Alt');
      parts.push(e.key);

      const combination = parts.join('+');

      // Find matching shortcut
      const handler = shortcuts[combination];
      if (handler) {
        e.preventDefault();
        handler(e);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
}
