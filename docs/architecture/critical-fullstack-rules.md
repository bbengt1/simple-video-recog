# Critical Fullstack Rules

These are **MANDATORY** rules that prevent common mistakes and ensure consistency across the codebase. All AI agents and developers must follow these rules.

- **Type Safety:** Use Pydantic models for all configuration and data entities. Never use raw dictionaries for structured data that crosses module boundaries.

- **Dependency Injection:** Components must receive dependencies through constructor parameters, never instantiate dependencies internally. This enables testing with mocks.

- **Error Handling:** All exceptions must be caught at module boundaries, logged with context, and either handled gracefully or re-raised with additional context. Never silently swallow exceptions.

- **Configuration Access:** Access configuration only through SystemConfig Pydantic model, never read environment variables directly with `os.getenv()` in application code.

- **Database Access:** All database operations must go through DatabaseManager methods. Never execute raw SQL queries outside the DatabaseManager class.

- **Logging Standards:** Use structured logging with consistent format: `logger.info(f"Event created: {event_id}", extra={"event_id": event_id})`. Include relevant context in log messages.

- **API Error Responses:** All API endpoints must use standard error format (see Error Handling section). Never return plain text error messages.

- **Resource Cleanup:** Always use context managers (`with` statements) for file operations, database connections, and external service clients. Never leave resources open after use.

- **Secrets in Logs:** Never log credentials, API keys, or RTSP URLs with passwords. Redact sensitive data: `rtsp://***:***@192.168.1.100:554/stream1`

- **Immutable Events:** Events are write-once, never modify after creation. No UPDATE statements on events table, only INSERT and SELECT.

- **Path Handling:** Use `pathlib.Path` for all file path operations, never string concatenation. Ensures cross-platform compatibility and prevents path injection.

- **Timezone Awareness:** All datetime objects must be timezone-aware (UTC). Use `datetime.utcnow()` and store with timezone info.

- **Import Organization:** Follow PEP 8 import order: standard library, third-party, local application. Use absolute imports, avoid relative imports outside of tests.

- **Frontend DOM Manipulation:** Use `textContent` for plain text, `innerHTML` only for trusted content. Always escape user-generated content before rendering.

- **Frontend API Calls:** All API calls must go through `services/apiClient.js`, never use `fetch()` directly in components. Centralizes error handling and request configuration.

---
