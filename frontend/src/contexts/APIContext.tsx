import { createContext, useContext, useMemo, type ReactNode } from 'react';
import { APIClient } from '@/lib/apiClient';
import { API_BASE_URL } from '@/lib/api';
import { useAuth } from './AuthContext';

const APIContext = createContext<APIClient | null>(null);

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
