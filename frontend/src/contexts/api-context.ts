import { createContext } from 'react';
import type { APIClient } from '@/lib/apiClient';

export const APIContext = createContext<APIClient | null>(null);
