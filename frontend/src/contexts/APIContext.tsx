import { useMemo, type ReactNode } from 'react';
import { APIClient, API_BASE_URL } from '@/lib/apiClient';
import { useAuth } from './AuthContext';
import { APIContext } from './api-context';

interface APIProviderProps {
  children: ReactNode;
}

/**
 * API Provider - Provides API client instance to all components
 *
 * Automatically injects auth token and handles 401 errors
 */
export function APIProvider({ children }: APIProviderProps) {
  const { token, logout } = useAuth();

  const client = useMemo(
    () => new APIClient(
      API_BASE_URL,
      () => token,
      logout // Logout on 401 errors
    ),
    [token, logout]
  );

  return <APIContext.Provider value={client}>{children}</APIContext.Provider>;
}
