# CI/CD Pipeline

**GitHub Actions Configuration:**

```yaml
# .github/workflows/ci.yaml
name: Continuous Integration

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Test Suite
    runs-on: macos-13  # macOS runner required for CoreML testing

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov black ruff

      - name: Run linters
        run: |
          black --check core/ platform/ integrations/ api/ tests/
          ruff check core/ platform/ integrations/ api/

      - name: Run unit tests
        run: |
          pytest tests/unit -v --cov=core --cov=platform --cov=integrations --cov-report=xml

      - name: Run integration tests
        run: |
          pytest tests/integration -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=70

  lint-frontend:
    name: Lint Frontend (Phase 2)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run ESLint (if configured)
        run: |
          # Phase 2: Add ESLint check for web/ directory
          echo "Frontend linting placeholder"

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Bandit (Python security linter)
        run: |
          pip install bandit
          bandit -r core/ platform/ integrations/ api/ -ll

      - name: Check dependencies for vulnerabilities
        run: |
          pip install safety
          safety check -r requirements.txt
```

**CI/CD Limitations:**
- **No automatic deployment** - CI only runs tests, deployment is manual
- **macOS runners required** - CoreML tests only run on Apple Silicon (expensive on GitHub Actions)
- **Performance tests skipped in CI** - NFR validation tests run too long for CI (run manually)
- **WebSocket tests may be flaky** - Integration tests with real WebSocket connections can timeout

**Manual Deployment Process:**
1. Run full test suite locally (including performance tests)
2. Tag release version: `git tag v1.0.0 && git push --tags`
3. Copy files to production machine via rsync or git pull
4. Restart services: `launchctl restart com.local.video-recognition`
5. Verify health check: `curl http://localhost:8000/api/v1/health`

---
