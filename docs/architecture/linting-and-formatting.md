# Linting and Formatting

## Python Tools

**Black (code formatter):**
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ["py310"]
```

**Ruff (linter):**
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
select = [
  "E",   # pycodestyle errors
  "F",   # pyflakes
  "W",   # pycodestyle warnings
  "I",   # isort (import sorting)
  "N",   # pep8-naming
  "UP",  # pyupgrade
]
ignore = [
  "E501",  # Line too long (handled by Black)
]
```

**Running linters:**
```bash
# Format code
black core/ platform/ integrations/ api/

# Check formatting (CI)
black --check core/ platform/ integrations/ api/

# Lint code
ruff check core/ platform/ integrations/ api/

# Fix auto-fixable issues
ruff check --fix core/
```

## JavaScript Tools (Phase 2)

**ESLint configuration:**
```json
{
  "env": {
    "browser": true,
    "es2021": true
  },
  "extends": "eslint:recommended",
  "parserOptions": {
    "ecmaVersion": 2021,
    "sourceType": "module"
  },
  "rules": {
    "no-console": "off",
    "no-unused-vars": "warn",
    "prefer-const": "error",
    "no-var": "error"
  }
}
```

**Prettier (code formatter):**
```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100
}
```

---
