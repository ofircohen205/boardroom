# Security Guide

This document covers security considerations and features for the **Boardroom** platform.

## Table of Contents

1. [Authentication](#authentication)
2. [Data Protection](#data-protection)
3. [API Security](#api-security)
4. [Best Practices](#best-practices)

## Authentication

### JWT (JSON Web Tokens)

- Core authentication mechanism.
- **Access Tokens**: Short-lived (default 30 minutes), signed with `HS256` and a secret key.
- **Payload**: Contains `sub` (user email).
- **Validation**: Every protected endpoint validates the signature and expiration of the token.

### Password Storage

- **Algorithm**: Bcrypt (`passlib` context `schemes=["bcrypt"]`).
- **Policy**: Passwords are never stored in plain text. Only the hash is persisted in the database.
- **Verification**: `passlib` handles secure hash comparison.

### Frontend Session

- **Storage**: Tokens are currently stored in `localStorage` for ease of implementation in Phase 1.
- **Context**: `AuthContext` manages the token lifecycle.
- **Future Improvement**: Move to `HttpOnly` cookies to mitigate XSS risks.

## Data Protection

### Database

- **Schema**: Users, Watchlists, and Portfolios are isolated by `user_id`.
- **ORMs**: SQLAlchemy prevents SQL injection by default through parameterized queries.

### API Security

- **Endpoints**: Protected by `get_current_user` dependency.
- **WebSockets**:
  - Connection requires a valid JWT in the query parameter (`?token=...`).
  - Connection is rejected immediately if token is invalid or missing.
- **CORS**: Configured to allow requests from the frontend origin (e.g., `http://localhost:5173`).

## Best Practices

1. **Environment Variables**:
   - `JWT_SECRET` must be kept secret and strong in production.
   - Database credentials should benefit from limited permissions.

2. **Input Validation**:
   - **Frontend**: Typed forms preventing invalid submissions.
   - **Backend**: Pydantic models validate all incoming request bodies.

3. **HTTPS**:
   - In production, all traffic (HTTP and WebSocket) must be encrypted via TLS.

## Security Concerns & Roadmap

### Token Storage (XSS)

- **Current**: `localStorage` is vulnerable to XSS.
- **Mitigation**: Ensure all dependencies are trusted and updated. Use CSP headers.
- **Roadmap**: Transition to `HttpOnly` cookies.

### Rate Limiting

- **Current**: Basic implementation.
- **Roadmap**: Implement Redis-based rate limiting for API and WebSocket connections.
