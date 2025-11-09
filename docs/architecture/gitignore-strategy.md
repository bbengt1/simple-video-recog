# Gitignore Strategy

```.gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo

# macOS
.DS_Store

# Runtime data
data/
logs/
models/

# Environment
.env
.env.local

# Test coverage
.coverage
htmlcov/
.pytest_cache/
```

**Rationale:**
- `data/`, `logs/`, `models/` excluded because they're generated at runtime
- `.env` excluded to prevent credentials from being committed
- `__pycache__/` excluded (Python bytecode, regenerated on import)
- IDE configs excluded (developer preference, not project requirement)

---
