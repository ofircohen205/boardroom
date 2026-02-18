# Rate Limiting Options & Configuration

This document covers all rate limiting mechanisms in the Boardroom application across LLM APIs, backend endpoints, and frontend request throttling.

## Table of Contents

1. [LLM API Rate Limits](#1-llm-api-rate-limits)
2. [Backend API Rate Limiting](#2-backend-api-rate-limiting)
3. [Frontend Request Throttling](#3-frontend-request-throttling)
4. [Implementation Recommendations](#4-implementation-recommendations)

---

## 1. LLM API Rate Limits

### Current Status: ⚠️ **Relies on Provider Defaults**

The application currently relies on each LLM provider's native rate limiting without additional client-side controls.

### Provider Rate Limits (as of 2026)

#### Anthropic Claude
- **Claude Sonnet 4.5** (current default model):
  - Free tier: ~50 requests/minute
  - Paid tier: ~1,000 requests/minute
  - Token limits: 200K tokens/request
- **Rate limit headers**: Anthropic returns `X-RateLimit-*` headers
- **Error handling**: Returns `429 Too Many Requests` when exceeded

#### OpenAI GPT-4
- **GPT-4o** (current model):
  - Free tier: ~3 requests/minute
  - Paid tier: ~10,000 requests/minute (tier-based)
  - Token limits: 128K tokens/request
- **Rate limit headers**: Returns `X-RateLimit-*` headers
- **Error handling**: Returns `429 Too Many Requests` with `Retry-After` header

#### Google Gemini
- **Gemini 2.0 Flash** (current model):
  - Free tier: ~15 requests/minute
  - Paid tier: ~360 requests/minute
  - Token limits: 1M tokens/request
- **Rate limit headers**: Returns quota information in response
- **Error handling**: Returns `429` or `503` when quota exceeded

### Current Implementation

**File**: `backend/ai/agents/base.py`

```python
class AnthropicClient(BaseLLMClient):
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = model

    async def complete(self, messages: list[dict], tools: list[dict] | None = None) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
        )
        return response.content[0].text
```

**Issues**:
- ❌ No retry logic for 429 errors
- ❌ No exponential backoff
- ❌ No request queuing
- ❌ No client-side rate limiting to prevent hitting provider limits

### Recommended Improvements

#### Option 1: Add Retry Logic with Exponential Backoff

```python
import asyncio
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1.0):
    """Decorator to retry LLM calls with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if "429" in str(e) or "rate_limit" in str(e).lower():
                        if attempt == max_retries - 1:
                            raise
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator

class AnthropicClient(BaseLLMClient):
    @retry_with_backoff(max_retries=3, base_delay=2.0)
    async def complete(self, messages: list[dict], tools: list[dict] | None = None) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
        )
        return response.content[0].text
```

#### Option 2: Implement Token Bucket Rate Limiter

```python
import time
from asyncio import Lock

class TokenBucket:
    """Token bucket algorithm for rate limiting."""

    def __init__(self, rate: float, capacity: float):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = Lock()

    async def acquire(self, tokens: float = 1.0):
        """Acquire tokens, waiting if necessary."""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return

            # Wait until enough tokens are available
            wait_time = (tokens - self.tokens) / self.rate
            await asyncio.sleep(wait_time)
            self.tokens = 0

# Global rate limiters per provider
_anthropic_limiter = TokenBucket(rate=10.0, capacity=50.0)  # 10 req/sec, burst 50
_openai_limiter = TokenBucket(rate=5.0, capacity=20.0)       # 5 req/sec, burst 20
_gemini_limiter = TokenBucket(rate=3.0, capacity=15.0)       # 3 req/sec, burst 15

class AnthropicClient(BaseLLMClient):
    async def complete(self, messages: list[dict], tools: list[dict] | None = None) -> str:
        await _anthropic_limiter.acquire()
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
        )
        return response.content[0].text
```

#### Option 3: Use Redis-Based Distributed Rate Limiting

For production with multiple backend instances:

```python
from redis.asyncio import Redis
import time

class RedisRateLimiter:
    """Redis-based distributed rate limiter."""

    def __init__(self, redis: Redis, key_prefix: str, limit: int, window: int):
        self.redis = redis
        self.key_prefix = key_prefix
        self.limit = limit  # max requests
        self.window = window  # time window in seconds

    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed."""
        key = f"{self.key_prefix}:{identifier}"
        current = int(time.time())
        window_start = current - self.window

        # Remove old entries
        await self.redis.zremrangebyscore(key, 0, window_start)

        # Count requests in current window
        count = await self.redis.zcard(key)

        if count < self.limit:
            # Add current request
            await self.redis.zadd(key, {str(current): current})
            await self.redis.expire(key, self.window)
            return True

        return False

# Usage
anthropic_limiter = RedisRateLimiter(
    redis=get_cache().redis,
    key_prefix="llm:anthropic",
    limit=50,
    window=60
)

class AnthropicClient(BaseLLMClient):
    async def complete(self, messages: list[dict], tools: list[dict] | None = None) -> str:
        if not await anthropic_limiter.is_allowed("global"):
            raise Exception("Rate limit exceeded for Anthropic API")

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
        )
        return response.content[0].text
```

### Configuration via Environment Variables

Add to `.env`:

```bash
# LLM Rate Limiting
LLM_RATE_LIMIT_ENABLED=true
ANTHROPIC_RATE_LIMIT_RPM=50      # Requests per minute
OPENAI_RATE_LIMIT_RPM=20
GEMINI_RATE_LIMIT_RPM=15
LLM_RETRY_MAX_ATTEMPTS=3
LLM_RETRY_BASE_DELAY=2.0         # Base delay in seconds
```

---

## 2. Backend API Rate Limiting

### Current Status: ⚠️ **Limited Implementation**

Currently, only specific features have rate limiting:

#### Implemented Rate Limits

1. **Scheduled Analysis** (`backend/services/schedules/service.py`):
   - **Limit**: 50 schedules per user
   - **Type**: Hard cap (not time-based)
   - **Error**: `ScheduleRateLimitError`

2. **Price Alerts** (`backend/services/alerts/service.py`):
   - **Limit**: 50 alerts per user
   - **Type**: Hard cap (not time-based)
   - **Error**: `AlertValidationError`

3. **Alert Cooldown**:
   - **Limit**: 60 minutes between alert triggers
   - **Type**: Time-based cooldown per alert

#### Missing Rate Limiting

- ❌ No rate limiting on `/api/auth/login` (vulnerable to brute force)
- ❌ No rate limiting on `/api/auth/register` (vulnerable to spam)
- ❌ No rate limiting on WebSocket connections
- ❌ No global API endpoint rate limiting
- ❌ No IP-based throttling

### Recommended Implementation: SlowAPI

**SlowAPI** is the standard FastAPI rate limiting library (similar to Flask-Limiter).

#### Installation

```bash
uv add slowapi
```

#### Implementation

**File**: `backend/core/rate_limit.py` (new file)

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from backend.core.settings import settings

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],  # Global default
    storage_uri=settings.redis_url,  # Use Redis for distributed limiting
    strategy="fixed-window",  # Options: fixed-window, moving-window
)

# Custom key functions
def get_user_id(request: Request) -> str:
    """Extract user ID from JWT token for authenticated rate limiting."""
    from backend.auth.dependencies import get_current_user_optional

    user = get_current_user_optional(request)
    if user:
        return f"user:{user.id}"
    return get_remote_address(request)

# Rate limit exception handler
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit errors."""
    return Response(
        content="Rate limit exceeded. Please try again later.",
        status_code=429,
        headers={
            "Retry-After": str(exc.detail.split("Retry after ")[1] if "Retry after" in exc.detail else "60")
        }
    )
```

**File**: `backend/main.py` (add exception handler)

```python
from slowapi.errors import RateLimitExceeded
from backend.core.rate_limit import rate_limit_exceeded_handler, limiter

app = FastAPI(...)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
```

**File**: `backend/api/auth/endpoints.py` (apply rate limiting)

```python
from slowapi import Limiter
from backend.core.rate_limit import limiter

@router.post("/login")
@limiter.limit("5/minute")  # 5 login attempts per minute per IP
async def login(
    request: Request,  # Required for SlowAPI
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    # ... existing login logic
    pass

@router.post("/register")
@limiter.limit("3/hour")  # 3 registrations per hour per IP
async def register(
    request: Request,
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    # ... existing registration logic
    pass
```

**File**: `backend/api/analysis/endpoints.py` (WebSocket rate limiting)

```python
from backend.core.rate_limit import limiter

@router.websocket("/analyze")
@limiter.limit("10/minute")  # 10 analysis requests per minute per user
async def analyze_stock(websocket: WebSocket):
    # ... existing WebSocket logic
    pass
```

### Rate Limiting Strategies

1. **Fixed Window**: Resets at fixed intervals (e.g., every minute)
   - Simple, fast
   - Allows burst at window boundaries

2. **Sliding Window**: Smooth rate limiting across time
   - More accurate
   - Slightly more resource-intensive

3. **Token Bucket**: Allow bursts up to capacity
   - Good for APIs with bursty traffic
   - More complex

### Recommended Rate Limits

| Endpoint | Limit | Reasoning |
|----------|-------|-----------|
| `POST /api/auth/login` | 5/minute | Prevent brute force attacks |
| `POST /api/auth/register` | 3/hour | Prevent spam registrations |
| `POST /api/auth/password` | 3/hour | Prevent password reset abuse |
| `GET /api/portfolios` | 60/minute | Generous for normal usage |
| `POST /api/portfolios` | 10/minute | Prevent spam creation |
| `GET /api/alerts` | 60/minute | High read limit |
| `POST /api/alerts` | 10/minute | Prevent alert spam |
| `WS /ws/analyze` | 10/minute | Expensive LLM operations |
| `WS /ws/backtest` | 5/minute | Very expensive operations |
| Global fallback | 100/minute | Catch-all safety net |

### Configuration via Environment Variables

Add to `backend/core/settings.py`:

```python
class Settings(BaseSettings):
    # ... existing settings

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_storage_url: str = "redis://localhost:6379/1"
    rate_limit_strategy: str = "fixed-window"  # fixed-window, moving-window

    # Per-endpoint limits (can override defaults)
    rate_limit_login: str = "5/minute"
    rate_limit_register: str = "3/hour"
    rate_limit_websocket: str = "10/minute"
    rate_limit_global: str = "100/minute"
```

Add to `.env`:

```bash
# Backend Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/1
RATE_LIMIT_STRATEGY=fixed-window
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_REGISTER=3/hour
RATE_LIMIT_WEBSOCKET=10/minute
RATE_LIMIT_GLOBAL=100/minute
```

---

## 3. Frontend Request Throttling

### Current Status: ✅ **Partially Implemented**

The frontend has basic debouncing for stock search autocomplete.

#### Implemented Throttling

**File**: `frontend/src/components/TickerInput.tsx`

```typescript
// Debounced search with 300ms delay
useEffect(() => {
  if (!ticker.trim() || ticker.length < 1) {
    setSuggestions([]);
    setShowDropdown(false);
    return;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(async () => {
    setIsSearching(true);
    try {
      const response = await fetch(
        `/api/stocks/search?q=${encodeURIComponent(ticker)}&market=${market}`,
        { signal: controller.signal }
      );
      // ... handle response
    } catch (e) {
      // ... handle error
    }
  }, 300);  // 300ms debounce

  return () => {
    clearTimeout(timeoutId);
    controller.abort();  // Cancel in-flight request
  };
}, [ticker, market]);
```

**Features**:
- ✅ 300ms debounce on input changes
- ✅ Request cancellation via `AbortController`
- ✅ Prevents duplicate requests

#### Missing Throttling

- ❌ No throttling on analysis requests (can spam "Analyze" button)
- ❌ No throttling on portfolio/watchlist updates
- ❌ No throttling on alert creation
- ❌ No global request queue
- ❌ No retry logic for failed requests

### Recommended Implementation

#### Option 1: Create Reusable Debounce Hook

**File**: `frontend/src/hooks/useDebounce.ts` (new file)

```typescript
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Usage
const debouncedSearchTerm = useDebounce(searchTerm, 300);
```

#### Option 2: Create Throttle Hook

**File**: `frontend/src/hooks/useThrottle.ts` (new file)

```typescript
import { useCallback, useRef } from 'react';

export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const lastRun = useRef(Date.now());

  return useCallback(
    (...args: Parameters<T>) => {
      const now = Date.now();
      if (now - lastRun.current >= delay) {
        callback(...args);
        lastRun.current = now;
      }
    },
    [callback, delay]
  ) as T;
}

// Usage
const throttledAnalyze = useThrottle((ticker: string) => {
  onAnalyze(ticker, market);
}, 2000);  // Maximum 1 analysis per 2 seconds
```

#### Option 3: Create Request Queue System

**File**: `frontend/src/lib/requestQueue.ts` (new file)

```typescript
class RequestQueue {
  private queue: Array<() => Promise<any>> = [];
  private activeRequests = 0;
  private maxConcurrent: number;

  constructor(maxConcurrent: number = 3) {
    this.maxConcurrent = maxConcurrent;
  }

  async enqueue<T>(request: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await request();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });
      this.processQueue();
    });
  }

  private async processQueue() {
    if (this.activeRequests >= this.maxConcurrent || this.queue.length === 0) {
      return;
    }

    this.activeRequests++;
    const request = this.queue.shift()!;

    try {
      await request();
    } finally {
      this.activeRequests--;
      this.processQueue();
    }
  }
}

export const apiQueue = new RequestQueue(3);  // Max 3 concurrent requests

// Usage
await apiQueue.enqueue(() =>
  fetch(`${API_BASE_URL}/api/analyze`, { method: 'POST', ... })
);
```

#### Option 4: Enhanced API Utility with Retry Logic

**File**: `frontend/src/lib/api.ts` (enhance existing file)

```typescript
export const API_BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) || 'http://localhost:8000';

interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  shouldRetry?: (error: any) => boolean;
}

export async function fetchAPIWithRetry(
  endpoint: string,
  options?: RequestInit,
  retryOptions?: RetryOptions
) {
  const {
    maxRetries = 3,
    baseDelay = 1000,
    maxDelay = 10000,
    shouldRetry = (error) => error.status === 429 || error.status >= 500,
  } = retryOptions || {};

  let lastError: any;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const url = `${API_BASE_URL}${endpoint}`;
      const response = await fetch(url, options);

      if (!response.ok) {
        const error = new Error(`API request failed: ${response.statusText}`);
        (error as any).status = response.status;

        if (shouldRetry(error) && attempt < maxRetries) {
          // Rate limited - wait for Retry-After header or exponential backoff
          const retryAfter = response.headers.get('Retry-After');
          const delay = retryAfter
            ? parseInt(retryAfter) * 1000
            : Math.min(baseDelay * Math.pow(2, attempt), maxDelay);

          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }

        throw error;
      }

      return response.json();
    } catch (error) {
      lastError = error;
      if (attempt === maxRetries) {
        throw lastError;
      }
    }
  }

  throw lastError;
}

// Helper for rate-limited endpoints
export async function fetchAPIAuthenticated(
  endpoint: string,
  token: string,
  options?: RequestInit
) {
  return fetchAPIWithRetry(endpoint, {
    ...options,
    headers: {
      ...options?.headers,
      'Authorization': `Bearer ${token}`,
    },
  });
}
```

### Recommended Frontend Throttling

| Action | Strategy | Delay | Reasoning |
|--------|----------|-------|-----------|
| Stock search autocomplete | Debounce | 300ms | Reduce API calls while typing |
| Analysis request | Throttle | 2000ms | Prevent button spam |
| Portfolio updates | Debounce | 500ms | Batch rapid changes |
| Alert creation | Throttle | 1000ms | Prevent accidental duplicates |
| Settings changes | Debounce | 1000ms | Wait for user to finish |
| Failed API requests | Retry with exponential backoff | 1s → 2s → 4s | Handle temporary failures |

### Implementation in TickerInput

**Updated**: `frontend/src/components/TickerInput.tsx`

```typescript
import { useThrottle } from "@/hooks/useThrottle";

export function TickerInput({ onAnalyze, isLoading }: Props) {
  // ... existing state

  // Throttle analyze requests to max 1 per 2 seconds
  const throttledAnalyze = useThrottle((ticker: string, market: Market) => {
    onAnalyze(ticker, market);
  }, 2000);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      setShowDropdown(false);
      throttledAnalyze(ticker.trim().toUpperCase(), market);
    }
  };

  // ... rest of component
}
```

---

## 4. Implementation Recommendations

### Priority 1: Critical (Implement Immediately)

1. **Backend Auth Rate Limiting**
   - Add SlowAPI to protect `/api/auth/login` and `/api/auth/register`
   - Prevents brute force and spam attacks
   - **Effort**: 2-3 hours
   - **Risk if not implemented**: High (security vulnerability)

2. **LLM Retry Logic**
   - Add exponential backoff for 429 errors
   - Prevents analysis failures during peak usage
   - **Effort**: 2-3 hours
   - **Risk if not implemented**: Medium (poor user experience)

### Priority 2: Important (Implement Soon)

3. **Frontend Request Throttling**
   - Add throttle hooks for analysis and form submissions
   - Improves UX and reduces backend load
   - **Effort**: 3-4 hours
   - **Risk if not implemented**: Medium (potential abuse)

4. **WebSocket Rate Limiting**
   - Limit concurrent analysis and backtest requests
   - Prevents expensive operation spam
   - **Effort**: 2-3 hours
   - **Risk if not implemented**: Medium (resource exhaustion)

### Priority 3: Nice to Have (Future Enhancement)

5. **Redis-Based Distributed Rate Limiting**
   - Required when scaling to multiple backend instances
   - **Effort**: 4-6 hours
   - **Risk if not implemented**: Low (only needed at scale)

6. **Advanced LLM Token Bucket**
   - Smooth out burst traffic to LLM providers
   - **Effort**: 4-5 hours
   - **Risk if not implemented**: Low (providers handle this)

### Monitoring & Observability

Add rate limit metrics:

```python
# backend/core/metrics.py
from prometheus_client import Counter, Histogram

rate_limit_hits = Counter(
    'rate_limit_hits_total',
    'Total rate limit hits',
    ['endpoint', 'limit_type']
)

request_duration = Histogram(
    'request_duration_seconds',
    'Request duration',
    ['endpoint', 'method']
)
```

### Testing Rate Limits

**Backend Test**:

```python
# tests/integration/test_rate_limiting.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_rate_limit(client: AsyncClient):
    """Test that login endpoint is rate limited."""
    # Make 6 requests (limit is 5/minute)
    for i in range(6):
        response = await client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrong"
        })

        if i < 5:
            assert response.status_code in [200, 401]  # Normal or auth error
        else:
            assert response.status_code == 429  # Rate limited
            assert "Retry-After" in response.headers
```

**Frontend Test**:

```typescript
// frontend/src/hooks/__tests__/useThrottle.test.ts
import { renderHook, act } from '@testing-library/react';
import { useThrottle } from '../useThrottle';

test('throttles function calls', async () => {
  const callback = jest.fn();
  const { result } = renderHook(() => useThrottle(callback, 1000));

  // Call 3 times rapidly
  act(() => {
    result.current();
    result.current();
    result.current();
  });

  // Only first call should execute
  expect(callback).toHaveBeenCalledTimes(1);

  // Wait for throttle period
  await new Promise(resolve => setTimeout(resolve, 1100));

  // Call again
  act(() => {
    result.current();
  });

  // Second call should now execute
  expect(callback).toHaveBeenCalledTimes(2);
});
```

---

## Summary

| Component | Current Status | Recommendation | Priority |
|-----------|---------------|----------------|----------|
| **LLM APIs** | ⚠️ No client-side limiting | Add retry logic with exponential backoff | 🔴 High |
| **Auth Endpoints** | ❌ Not rate limited | Add SlowAPI with 5/min for login | 🔴 Critical |
| **WebSocket** | ❌ Not rate limited | Add SlowAPI with 10/min per user | 🟡 Medium |
| **Frontend Search** | ✅ 300ms debounce | Keep current implementation | ✅ Done |
| **Frontend Analyze** | ❌ No throttling | Add 2s throttle on button | 🟡 Medium |
| **Global API** | ❌ No limiting | Add 100/min fallback limit | 🟡 Medium |
| **Distributed** | ❌ Not implemented | Add Redis-based limiting (future) | 🟢 Low |

## Next Steps

1. **Immediate**: Implement auth rate limiting (SlowAPI)
2. **This Week**: Add LLM retry logic
3. **This Month**: Add frontend throttling hooks
4. **Future**: Migrate to Redis-based distributed rate limiting when scaling
