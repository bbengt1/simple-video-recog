# Python Code Style

## PEP 8 Compliance

Follow [PEP 8](https://peps.python.org/pep-0008/) with these specific requirements:

**Line Length:**
- Maximum 100 characters (not 79) for better readability on modern displays
- Configured in `.pyproject.toml`: `line-length = 100`

**Indentation:**
- 4 spaces per indentation level (never tabs)
- Hanging indents: 4 spaces for continuation lines

**Whitespace:**
- One blank line between methods in a class
- Two blank lines between top-level functions and classes
- No trailing whitespace on any lines

**Imports:**
```python
# Standard library imports
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Third-party imports
import numpy as np
from pydantic import BaseModel, Field

# Local application imports
from core.database import DatabaseManager
from core.models import Event, DetectedObject
```

**String Quotes:**
- Prefer double quotes `"` for strings (configured in Black)
- Use f-strings for formatting, not `.format()` or `%` operator
- Example: `logger.info(f"Event created: {event.event_id}")`

**Type Hints:**
```python
from typing import List, Optional, Tuple

def detect_motion(frame: np.ndarray) -> Tuple[bool, float]:
    """Detect motion in frame.

    Args:
        frame: OpenCV frame (numpy array)

    Returns:
        Tuple of (has_motion, confidence_score)
    """
    # Implementation
    return True, 0.87
```

**Docstrings:**
- Use Google style docstrings for all public functions and classes
- Include Args, Returns, Raises sections
- Example:
```python
def create_event(
    self,
    frame: np.ndarray,
    objects: List[DetectedObject],
    description: str,
    motion_confidence: float
) -> Optional[Event]:
    """Create event from processed frame data.

    Args:
        frame: OpenCV frame with detected objects
        objects: List of detected objects from CoreML
        description: Semantic description from LLM
        motion_confidence: Motion detection confidence score (0.0-1.0)

    Returns:
        Event object if created, None if suppressed by de-duplication

    Raises:
        ValueError: If motion_confidence not in range [0.0, 1.0]
    """
```

---
