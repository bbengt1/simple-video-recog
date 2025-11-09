# Project Metadata (pyproject.toml)

```toml
[project]
name = "video-recognition-system"
version = "1.0.0"
description = "Local video recognition system optimized for Apple Silicon"
authors = [{name = "Your Name", email = "you@example.com"}]
requires-python = ">=3.10"
dependencies = [
    "opencv-python>=4.8.1",
    "coremltools>=7.0",
    "ollama>=0.1.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "pyyaml>=6.0",
    "fastapi>=0.104",
    "uvicorn>=0.24",
    "websockets>=12.0",
    "psutil>=5.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "black>=23.0",
    "ruff>=0.1",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "--cov=core --cov=platform --cov=integrations --cov-report=html --cov-report=term"

[tool.black]
line-length = 100
target-version = ["py310"]

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I"]
ignore = ["E501"]  # Line too long (handled by black)
```

---
