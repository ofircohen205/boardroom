import { useContext } from 'react';
import { APIContext } from '@/contexts/api-context';
import type { APIClient } from '@/lib/apiClient';

/**
 * Hook to access the API client
 *
 * @throws Error if used outside of APIProvider
 */
export function useAPIClient(): APIClient {
  const client = useContext(APIContext);
  if (!client) {
    throw new Error('useAPIClient must be used within APIProvider');
  }
  return client;
}
