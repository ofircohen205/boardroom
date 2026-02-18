import { useState, useCallback } from 'react';

/**
 * Copy to clipboard hook with visual feedback
 *
 * @example
 * ```tsx
 * const { copy, copied } = useCopyToClipboard();
 *
 * <Button onClick={() => copy('Hello World')}>
 *   {copied ? 'Copied!' : 'Copy'}
 * </Button>
 * ```
 */
export function useCopyToClipboard(resetAfter = 2000) {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(
    async (text: string) => {
      try {
        await navigator.clipboard.writeText(text);
        setCopied(true);

        // Reset after timeout
        setTimeout(() => setCopied(false), resetAfter);
      } catch (err) {
        console.error('Failed to copy to clipboard:', err);
      }
    },
    [resetAfter]
  );

  return { copy, copied };
}
