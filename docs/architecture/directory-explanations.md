# Directory Explanations

**core/**: Platform-independent business logic that could theoretically run on any OS. Contains the processing pipeline, event management, database access, logging, and metrics. No Apple-specific code here.

**platform/**: Apple Silicon-specific implementations. Currently only CoreML detector. Future: Metal-accelerated image processing, Vision framework integration.

**integrations/**: External service clients. RTSP camera client (OpenCV) and Ollama LLM client. These are abstracted to enable mocking in tests.

**api/**: Phase 2 FastAPI web server. Separate from core processing pipeline to enable dual-process architecture. Includes REST endpoints and WebSocket server.

**web/**: Phase 2 vanilla JavaScript web dashboard. No build step required - served directly from this directory. Uses ES6 modules with native browser imports.

**config/**: YAML configuration files with Pydantic schema validation. Keeps sensitive data (RTSP credentials) out of code.

**tests/**: Three-tier test organization:
- **unit/**: Fast, isolated tests with mocked dependencies (<1s per test)
- **integration/**: Tests with real dependencies (database, file system) (1-5s per test)
- **performance/**: NFR validation tests (inference times, throughput) (10-60s per test)

**data/**: Runtime data directory. Gitignored. Created automatically on first run. Contains SQLite database and date-organized event files.

**logs/**: Application logs. Gitignored. Contains rotating application log and metrics log (JSON Lines format).

**models/**: CoreML model files. Gitignored (large files). Downloaded during setup via scripts/download_models.sh.

**migrations/**: Manual SQL migration scripts. Versioned files (001_initial.sql, 002_*.sql, etc.) applied sequentially on startup.

**scripts/**: Setup and maintenance scripts. Bash scripts for environment setup, model downloads, database backups.

---
