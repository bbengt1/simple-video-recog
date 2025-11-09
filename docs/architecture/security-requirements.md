# Security Requirements

## Frontend Security (Phase 2)

**CSP Headers:** Not implemented in Phase 1/2 (localhost-only access)
- Phase 3 consideration: If remote access is added, implement Content Security Policy headers
- Recommended policy: `default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'`
- Rationale for Phase 2: Localhost-only deployment means CSP provides minimal security benefit

**XSS Prevention:**
- Strategy: Escape all user-generated content before rendering to DOM
- Implementation: Use `textContent` instead of `innerHTML` for dynamic text
- Example: `element.textContent = event.llm_description` (safe) vs `element.innerHTML = event.llm_description` (unsafe)
- LLM descriptions sanitized: Ollama output is plain text, no HTML/script injection risk
- Object labels from CoreML: Predefined class names (person, car, dog), no user input

**Secure Storage:**
- Strategy: No sensitive data stored in browser (no auth tokens, no credentials)
- LocalStorage: Not used (all state is ephemeral, reloaded from API on page refresh)
- SessionStorage: Not used
- Cookies: Not used (no authentication in Phase 2)
- Rationale: Stateless frontend reduces attack surface

## Backend Security

**Input Validation:**
- Approach: Pydantic validation for all configuration and API inputs
- Configuration: SystemConfig Pydantic model validates all environment variables
- API requests: FastAPI automatically validates query parameters and request bodies
- Example: `limit` parameter constrained to 1-1000, `confidence` to 0.0-1.0
- SQL injection prevention: Parameterized queries used exclusively (no string concatenation)

**Rate Limiting:**
- Configuration: Not implemented in Phase 2 (localhost-only, single user)
- Phase 3 consideration: If remote access added, implement rate limiting via FastAPI middleware
- Recommended: 100 requests/minute per IP, 1000 requests/hour
- Implementation: `slowapi` library (FastAPI-compatible rate limiter)

**CORS Policy:**
- Configuration: Restricted to localhost origins only
- Allowed origins: `http://localhost:3000`, `http://localhost`
- Allowed methods: `GET`, `POST` (no `DELETE` or `PUT` in API)
- Credentials: Enabled (allow cookies for future auth)
- Example configuration in `api/server.py`:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:3000", "http://localhost"],
      allow_credentials=True,
      allow_methods=["GET", "POST"],
      allow_headers=["*"],
  )
  ```

## Authentication Security (Phase 2: None, Phase 3: Planned)

**Token Storage (Phase 3):**
- Strategy: HttpOnly cookies for refresh tokens, memory-only for access tokens
- Rationale: HttpOnly cookies prevent XSS theft, memory storage prevents CSRF
- Implementation: FastAPI OAuth2PasswordBearer with JWT tokens

**Session Management (Phase 3):**
- Approach: Stateless JWT tokens with 15-minute expiration
- Refresh tokens: 7-day expiration, stored in HttpOnly cookie
- Session invalidation: Token blacklist in Redis (if remote access added)

**Password Policy (Phase 3):**
- Requirements: Not applicable - no user accounts in Phase 1/2
- Future: If multi-user support added, enforce minimum 12 characters, complexity requirements
- Recommendation: Use passkeys/WebAuthn instead of passwords for better security

## Additional Security Considerations

**RTSP Credentials:**
- Storage: Environment variables only (`.env` file, gitignored)
- Never logged: Credentials redacted from all log output
- Example: Log shows `rtsp://***:***@192.168.1.100:554/stream1` instead of actual password
- Transmission: RTSP uses Basic Auth over local network (acceptable for home use)
- Phase 3: Consider RTSP over TLS (RTSPS) if camera supports it

**Database Security:**
- File permissions: SQLite database file has 0600 permissions (owner read/write only)
- Access control: Single application user, no multi-user access
- Encryption at rest: Not implemented (macOS FileVault provides disk-level encryption)
- Backup security: Database backups inherit same file permissions

**API Endpoint Security:**
- Localhost binding: API server only binds to `0.0.0.0` (all interfaces) for local network access
- Firewall: macOS firewall blocks external access (only local network can reach API)
- No public internet exposure: Router firewall prevents WAN access
- Phase 3: Add basic auth or API keys if exposing to internet

**Secret Management:**
- Current approach: `.env` file with restrictive permissions (0600)
- Production: Ensure `.env` is not readable by other users on system
- Future: Consider macOS Keychain integration for RTSP credentials
- No cloud secrets: No AWS/Azure/GCP credentials needed (100% local)

**Vulnerability Management:**
- Dependency scanning: GitHub Dependabot enabled for automated security updates
- Python packages: `safety check` runs in CI pipeline (checks for known vulnerabilities)
- Update cadence: Monthly review of dependency updates, immediate for critical CVEs
- Minimal dependencies: Only 10 production dependencies reduces attack surface

---
