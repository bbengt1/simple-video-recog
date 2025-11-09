# Rationale

**Why monorepo over polyrepo?**
- All code changes are atomic (single commit touches backend + frontend + tests)
- Shared types/models between Python and JavaScript (via JSON schema generation)
- Simpler dependency management (single requirements.txt)
- Better suited for AI-driven development (agent sees complete context)

**Why functional grouping (core/, platform/, integrations/) over feature-based (events/, cameras/)?**
- Clear separation of concerns by architectural layer
- Platform-specific code isolated in platform/ (easier to port to other OSes in future)
- Dependencies flow one direction (integrations → platform → core)
- Aligns with testing strategy (unit tests for core, integration tests for integrations)

**Why three-tier test organization (unit/, integration/, performance/)?**
- Fast feedback loop: unit tests run in <10s, integration in <60s
- Selective test execution: `pytest tests/unit` for quick checks
- Clear expectations: unit tests must have mocked dependencies
- NFR validation: performance tests explicitly validate quantitative targets

**Why models not in git?**
- CoreML files are large (50-500MB), would bloat repository
- Model versions may change frequently during experimentation
- Download script (scripts/download_models.sh) ensures reproducibility
- Models are effectively binary artifacts, not source code

**Why config as example file (.env.example vs .env)?**
- Prevents accidental credential leaks (RTSP passwords)
- Documents required environment variables for new developers
- Allows per-developer customization (different camera URLs)

---
