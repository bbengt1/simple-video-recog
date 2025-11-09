# FastAPI Server (Phase 2)

**Responsibility:** Provides REST API endpoints for web dashboard to query events, retrieve images, and access system metrics.

**Key Interfaces:**
- FastAPI route handlers for all OpenAPI endpoints
- CORS middleware for localhost:3000 (dev) and localhost (prod)
- Static file serving for annotated images

**Dependencies:**
- DatabaseManager (to query events)
- MetricsCollector (to provide current metrics)
- SystemConfig (to provide sanitized config)

**Technology Stack:**
- Python 3.10+, FastAPI 0.104+, Uvicorn ASGI server
- Module path: `api/server.py`
- Class: `FastAPIServer`

**Implementation Notes:**
- Runs in separate process from processing pipeline (dual-process architecture)
- Shares SQLite database via file access (read-only for API)
- No authentication in Phase 2 (localhost-only)
- CORS enabled for http://localhost:3000 (development)
- Static files served from /images route (maps to data/events directory)
- Startup validation: check database exists and is readable

---
