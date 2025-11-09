# Comments and Documentation

## When to Comment

**DO comment:**
- Complex algorithms (e.g., motion detection, de-duplication logic)
- Non-obvious business rules (e.g., "80% overlap triggers suppression")
- Performance optimizations (e.g., "Skip frames to reduce CPU usage")
- Workarounds for bugs in third-party libraries
- Security considerations (e.g., "Redact credentials before logging")

**DON'T comment:**
- Self-explanatory code (good naming is better than comments)
- What the code does (docstrings cover this)
- Commented-out code (use version control instead)

**Good comments:**
```python
# De-duplication: Compare new event to last 5 events
# Suppress if object labels overlap ≥80%
# This prevents duplicate alerts for stationary objects
overlap_threshold = 0.8
recent_events = self._get_recent_events(limit=5)
```

**Bad comments:**
```python
# Create event
event = Event(...)

# Insert into database
db.insert_event(event)
```

## TODO Comments

Use TODO comments sparingly, only for planned enhancements:
```python
# TODO(Phase 3): Add multi-camera support - requires cameras table
# TODO: Optimize by caching recent events in memory (low priority)
```

Format: `TODO(context): Description`

---
