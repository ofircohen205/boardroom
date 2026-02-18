/**
 * Custom API error types for better error handling
 */

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: unknown
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// ... (AuthenticationError, ValidationError, NotFoundError, RateLimitError unchanged ideally, but I need to include them if I replace block)
// I will just replace the specific parts or the whole file content to be safe.

export class AuthenticationError extends APIError {
  constructor(message = 'Authentication required') {
    super(message, 401);
    this.name = 'AuthenticationError';
  }
}

export class ValidationError extends APIError {
  constructor(message: string, public errors?: Record<string, string[]>) {
    super(message, 422);
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends APIError {
  constructor(message = 'Resource not found') {
    super(message, 404);
    this.name = 'NotFoundError';
  }
}

export class RateLimitError extends APIError {
  constructor(message = 'Rate limit exceeded') {
    super(message, 429);
    this.name = 'RateLimitError';
  }
}

/**
 * Parse error response and return appropriate error instance
 */
export function parseAPIError(statusCode: number, responseData: unknown): APIError {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = responseData as any;
  const message = data?.detail || data?.message || 'An error occurred';

  switch (statusCode) {
    case 401:
      return new AuthenticationError(message);
    case 404:
      return new NotFoundError(message);
    case 422:
      return new ValidationError(message, data?.errors);
    case 429:
      return new RateLimitError(message);
    default:
      return new APIError(message, statusCode, responseData);
  }
}
