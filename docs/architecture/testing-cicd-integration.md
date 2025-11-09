# Testing CI/CD Integration

**GitHub Actions Test Workflow:**
- Run on every push and pull request
- Separate jobs for unit, integration, and performance tests
- Unit tests must pass for PR to merge
- Integration tests may be skipped if dependencies unavailable
- Performance tests run manually (too slow for CI)

**Local Pre-commit Testing:**
```bash
# Run before committing
pytest tests/unit -v              # Fast unit tests only
black --check core/ platform/     # Code formatting
ruff check core/ platform/        # Linting

# Full test suite before push
pytest tests/ -v --cov            # All tests with coverage
```

---
