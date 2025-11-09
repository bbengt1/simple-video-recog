# Git Commit Standards

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring (no behavior change)
- `test`: Add or update tests
- `docs`: Documentation changes
- `perf`: Performance improvements
- `style`: Code style changes (formatting, no logic change)
- `chore`: Build process, dependency updates

**Examples:**
```
feat(coreml): add YOLOv8 model support for object detection

Implement CoreMLObjectDetector class with YOLOv8n model.
Validates model runs on Apple Neural Engine for <100ms inference.

Closes #12
```

```
fix(pipeline): prevent crash when RTSP connection lost

Add reconnection logic with exponential backoff (1s, 2s, 4s, 8s).
Log warning on connection loss, error after 5 consecutive failures.

Fixes #23
```

```
test(database): add integration tests for SQLite migrations

Cover schema version tracking, migration application, and rollback.
```

---
