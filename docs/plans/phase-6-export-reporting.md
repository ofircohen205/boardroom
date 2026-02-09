# Phase 6: Export & Reporting

## Goal

Let users export analysis results as professional PDF reports, CSV data, and shareable links. Enable programmatic access via API keys for integration with other tools.

## Why This Matters

- Users want to save and share analysis with colleagues, advisors, or for record-keeping
- Professional reports add credibility and polish
- API access enables power users and integrations
- No dependency on other phases — can be built independently

## Features

### 6.1 PDF Report Generation

Generate polished, printable analysis reports.

**Backend — new module `backend/reports/pdf_generator.py`:**
- Use Jinja2 templates + WeasyPrint for HTML→PDF conversion
- Report sections:
  1. **Header:** Boardroom logo, report date, ticker, market
  2. **Executive Summary:** Chairperson's decision, confidence, rationale
  3. **Fundamental Analysis:** Key metrics table + agent summary
  4. **Technical Analysis:** Price chart image + indicators + agent summary
  5. **Sentiment Analysis:** Overall sentiment score, key news items, agent summary
  6. **Risk Assessment:** VaR, sector weight, veto status
  7. **Disclaimer:** Standard "not financial advice" footer
- Chart rendering: Use matplotlib (server-side) to generate static chart images for the PDF since lightweight-charts is browser-only

**Template structure:**
```
backend/reports/
├── templates/
│   ├── analysis_report.html    # Main report template
│   ├── comparison_report.html  # Multi-stock comparison (Phase 3)
│   └── base.html               # Shared layout, styles
├── pdf_generator.py
└── chart_renderer.py           # matplotlib chart generation
```

**Endpoint:**
- `GET /api/reports/analysis/{session_id}/pdf` → returns PDF file
- `GET /api/reports/analysis/{session_id}/preview` → returns HTML preview

### 6.2 CSV/Excel Export

Export raw data for users who want to analyze in their own tools.

**Backend — new module `backend/reports/data_export.py`:**
- Export formats:
  - CSV: Simple, universal
  - XLSX: Multiple sheets (one per agent report), formatted headers
- Export types:
  - Single analysis: All agent data for one session
  - Analysis history: All analyses for a ticker over time
  - Portfolio summary: All positions with current values
  - Performance data: Outcomes and accuracy metrics (Phase 2)

**Endpoints:**
- `GET /api/export/analysis/{session_id}?format=csv`
- `GET /api/export/analysis/{session_id}?format=xlsx`
- `GET /api/export/history?ticker=AAPL&format=csv`
- `GET /api/export/portfolio/{id}?format=csv`

### 6.3 Shareable Analysis Links

Let users share a read-only view of an analysis.

**Backend:**
- New DB model:
  ```python
  class SharedAnalysis(Base):
      __tablename__ = "shared_analyses"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      session_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("analysis_sessions.id"))
      share_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
      created_by: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"))
      expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
      view_count: Mapped[int] = mapped_column(default=0)
      created_at: Mapped[datetime] = mapped_column(default=datetime.now)
  ```
- Endpoints:
  - `POST /api/share/analysis/{session_id}` → returns `{share_url, share_token, expires_at}`
  - `GET /api/shared/{share_token}` → returns analysis data (no auth required)
- Default expiry: 30 days
- Option for no-expiry permanent links

**Frontend:**
- "Share" button on completed analyses → copies link to clipboard
- Shared view page: read-only dashboard showing the analysis results
  - Reuse existing components (DecisionCard, AgentPanel, StockChart)
  - No ticker input or interactive features
  - "Analyze on Boardroom" CTA for viewers

### 6.4 API Key Management

Let users access Boardroom programmatically.

**Backend:**
- New DB model:
  ```python
  class ApiKey(Base):
      __tablename__ = "api_keys"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"))
      key_hash: Mapped[str] = mapped_column(String(255))  # bcrypt hash of the key
      key_prefix: Mapped[str] = mapped_column(String(8))   # First 8 chars for identification
      name: Mapped[str] = mapped_column(String(100))
      last_used: Mapped[Optional[datetime]] = mapped_column(nullable=True)
      expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
      created_at: Mapped[datetime] = mapped_column(default=datetime.now)
  ```
- Key format: `br_live_xxxxxxxxxxxxxxxxxxxx` (prefix + random)
- Auth: Accept API key via `Authorization: Bearer br_live_xxx` header
- Rate limiting: 100 requests/hour per key (configurable)
- Endpoints:
  - `POST /api/keys` → generates key (only shown once)
  - `GET /api/keys` → list keys (prefix only, not full key)
  - `DELETE /api/keys/{id}`

**REST API for external use:**
- `POST /api/v1/analyze` — run analysis, returns full result (synchronous)
  ```json
  // Request
  {"ticker": "AAPL", "market": "US"}
  // Response
  {"session_id": "...", "decision": {...}, "fundamental": {...}, ...}
  ```
- `GET /api/v1/analyze/{session_id}` — retrieve past analysis
- Rate-limited and authenticated via API key

### 6.5 Webhook Delivery

Push analysis results to external services.

**Backend:**
- New DB model:
  ```python
  class Webhook(Base):
      __tablename__ = "webhooks"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"))
      url: Mapped[str] = mapped_column(String(500))
      secret: Mapped[str] = mapped_column(String(255))  # For HMAC signing
      events: Mapped[list] = mapped_column(JSONB)  # ["analysis_complete", "alert_triggered"]
      active: Mapped[bool] = mapped_column(Boolean, default=True)
      created_at: Mapped[datetime] = mapped_column(default=datetime.now)
  ```
- Events:
  - `analysis_complete` — sends full analysis result
  - `alert_triggered` — sends alert details (Phase 4)
  - `recommendation_change` — when re-analysis changes the recommendation
- Delivery: POST to URL with HMAC-SHA256 signature in `X-Boardroom-Signature` header
- Retry: 3 attempts with exponential backoff on failure

**Endpoints:**
- `POST /api/webhooks`
- `GET /api/webhooks`
- `DELETE /api/webhooks/{id}`
- `POST /api/webhooks/{id}/test` — sends test payload

### 6.6 Frontend

**Components:**
- `ExportMenu` — dropdown on analysis results with options: PDF, CSV, Share, API
- `ShareDialog` — modal for creating/managing shared links
- `ApiKeysPage` — page for managing API keys
  - Create key form
  - Key list with last-used timestamps
  - Code examples for using the API (curl, Python, JavaScript)
- `WebhookManager` — configure webhook endpoints
- `SharedAnalysisView` — public read-only analysis page

**Dashboard integration:**
- Export button group on DecisionCard
- Share icon in analysis history items

## File Changes Summary

| Action | Path | Description |
|--------|------|-------------|
| Create | `backend/reports/__init__.py` | Reports module |
| Create | `backend/reports/pdf_generator.py` | PDF generation with Jinja2+WeasyPrint |
| Create | `backend/reports/chart_renderer.py` | Server-side chart images with matplotlib |
| Create | `backend/reports/data_export.py` | CSV/XLSX export logic |
| Create | `backend/reports/templates/` | Jinja2 HTML templates for PDF |
| Modify | `backend/dao/models.py` | Add SharedAnalysis, ApiKey, Webhook models |
| Create | `backend/api/reports.py` | Report generation endpoints |
| Create | `backend/api/export.py` | Data export endpoints |
| Create | `backend/api/sharing.py` | Share link endpoints |
| Create | `backend/api/api_keys.py` | API key management endpoints |
| Create | `backend/api/webhooks.py` | Webhook management and delivery |
| Create | `backend/api/v1.py` | Versioned public API |
| Modify | `backend/api/routes.py` | Mount all new routers |
| Modify | `backend/config.py` | Add rate limit, webhook settings |
| Create | `frontend/src/components/ExportMenu.tsx` | Export dropdown |
| Create | `frontend/src/components/ShareDialog.tsx` | Share link modal |
| Create | `frontend/src/pages/ApiKeysPage.tsx` | API key management |
| Create | `frontend/src/pages/SharedAnalysisView.tsx` | Public shared view |
| Modify | `frontend/src/components/DecisionCard.tsx` | Add export/share buttons |
| Create | `alembic/versions/xxx_add_sharing_api.py` | DB migration |

## Dependencies

- `weasyprint` — HTML to PDF conversion
- `jinja2` — PDF template rendering (may already be a FastAPI dependency)
- `openpyxl` — Excel file generation
- `matplotlib` — server-side chart rendering for PDFs

## Testing

- `tests/test_pdf_generator.py` — template rendering, chart inclusion, PDF validity
- `tests/test_data_export.py` — CSV/XLSX content correctness, formatting
- `tests/test_sharing.py` — token generation, expiry, view counting, access control
- `tests/test_api_keys.py` — key generation, hashing, auth middleware, rate limiting
- `tests/test_webhooks.py` — delivery, signing, retry logic

## Security Considerations

- API keys: Only show full key once at creation, store bcrypt hash
- Shared links: Use cryptographically random tokens (secrets.token_urlsafe)
- Webhooks: HMAC signing to prevent spoofing
- Rate limiting: Per-key limits to prevent abuse
- PDF generation: Sanitize all user content to prevent injection in templates
- Export: Ensure users can only export their own data
