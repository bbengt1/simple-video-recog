# Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|-----------|---------|---------|-----------|
| Core Language | Python | 3.10+ | Primary development language | Native ARM64 support, rich ML/CV ecosystem, CoreML bindings available |
| Computer Vision | OpenCV | 4.8.1+ | RTSP stream capture, motion detection, image processing | Industry standard, M1-optimized builds available, mature RTSP client |
| ML Framework | CoreML Tools | 7.0+ | Neural Engine interface for object detection | Only framework with Apple Neural Engine access for <100ms inference |
| LLM Integration | ollama-python | 0.1.0+ | Ollama HTTP API client | Official Python client for local LLM inference |
| API Framework | FastAPI | 0.104+ | Phase 2 REST API and WebSocket server | Async support, auto-generated OpenAPI docs, excellent performance |
| Frontend Language | JavaScript | ES6+ | Web dashboard implementation | Native browser support, no transpilation needed, simple deployment |
| State Management | Custom Observer Pattern | N/A | Reactive UI updates | Lightweight alternative to frameworks, no external dependencies |
| Database | SQLite | 3.42+ | Event storage and querying | File-based, zero-config, ACID compliant, sufficient for single-user |
| Cache | None | N/A | Not needed for MVP | Event data is write-heavy, reads are infrequent, no performance benefit |
| File Storage | Local Filesystem | N/A | Annotated images, JSON/plaintext logs | Simple, no additional infrastructure, aligns with privacy-first approach |
| Authentication | None (Phase 1-2) | N/A | Not implemented in MVP | Localhost-only access, future enhancement for remote access |
| Frontend Testing | None (Phase 1) | N/A | Vanilla JS with manual testing initially | Defer to Phase 3, focus on backend test coverage for MVP |
| Backend Testing | pytest | 7.4+ | Unit, integration, and performance tests | Python standard, fixture support, parametrization, ≥70% coverage target |
| E2E Testing | Playwright (Phase 3) | TBD | Full workflow validation | Deferred to Phase 3, manual testing sufficient for Phase 1-2 |
| Build Tool | None | N/A | No build step required | Python is interpreted, JavaScript uses native ES6 modules |
| Bundler | None | N/A | No bundling required | Vanilla JS served directly, no framework compilation needed |
| IaC Tool | None | N/A | Local deployment only | No cloud infrastructure, manual setup on Mac Mini/Studio |
| CI/CD | GitHub Actions | N/A | Automated testing on push/PR | Free for public repos, macOS runners available for testing |
| Monitoring | Custom Metrics Logger | N/A | Performance metrics to logs/metrics.json | Simple JSON Lines format, no external service needed |
| Logging | Python logging + custom | 3.10+ stdlib | Application logs, event logs, metrics | Built-in logging module + custom JSON/plaintext event loggers |
| CSS Framework | Custom CSS | N/A | Web dashboard styling | Simple layout, dark mode optimized, no framework overhead |

---
