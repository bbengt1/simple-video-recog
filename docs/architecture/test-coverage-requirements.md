# Test Coverage Requirements

**Coverage Target:** ≥70% code coverage (NFR requirement)

**Coverage by Module:**
- `core/`: ≥80% (critical business logic)
- `platform/`: ≥70% (CoreML integration)
- `integrations/`: ≥60% (external service clients, harder to test)
- `api/`: ≥75% (FastAPI endpoints, Phase 2)

**Excluded from Coverage:**
- `main.py`: Entry point, tested manually
- `scripts/`: Utility scripts, not production code
- Test files themselves

**Coverage Reporting:**
```bash
# Generate HTML coverage report
pytest --cov=core --cov=platform --cov=integrations --cov-report=html

# View report
open htmlcov/index.html

# Fail CI if coverage below 70%
pytest --cov --cov-fail-under=70
```

---
