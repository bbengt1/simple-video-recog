# Repository Structure

**Structure:** Monorepo with functional separation
**Monorepo Tool:** Not applicable (Python project, no workspace tooling needed)
**Package Organization:** Functional grouping by architectural layer

```
video-recognition/
├── core/           # Platform-independent business logic
├── platform/       # Apple Silicon-specific implementations
├── integrations/   # External service clients (Ollama, RTSP)
├── api/            # Phase 2: FastAPI web server
├── web/            # Phase 2: Vanilla JavaScript dashboard
├── tests/          # Test organization mirrors source structure
└── config/         # Configuration files and schemas
```

The monorepo structure provides clear separation of concerns while keeping all code in a single repository. This approach simplifies dependency management and ensures atomic commits across the entire stack. Functional grouping (rather than feature-based modules) aligns with the sequential processing pipeline architecture and makes dependencies explicit.
