# Code Organization Patterns

## Python Module Structure

**Standard module template:**
```python
"""Module description.

This module provides [brief description of functionality].
Example usage is in tests/unit/test_[module_name].py.
"""
import logging
from typing import List, Optional

from core.models import Event
from core.config import SystemConfig

logger = logging.getLogger(__name__)


class ComponentName:
    """Class description.

    Attributes:
        config: System configuration
        dependency: Injected dependency
    """

    def __init__(self, config: SystemConfig, dependency: DependencyType):
        """Initialize component with dependencies.

        Args:
            config: System configuration
            dependency: External dependency to inject
        """
        self.config = config
        self.dependency = dependency
        self._internal_state = None

    def public_method(self, param: str) -> bool:
        """Public method description.

        Args:
            param: Parameter description

        Returns:
            Success status
        """
        return self._private_method(param)

    def _private_method(self, param: str) -> bool:
        """Private method (leading underscore).

        Args:
            param: Parameter description

        Returns:
            Success status
        """
        # Implementation
        return True


# Module-level functions (if needed, prefer class methods)
def utility_function(value: int) -> int:
    """Utility function description."""
    return value * 2
```

## JavaScript Component Pattern

**Functional component template:**
```javascript
/**
 * EventCard component - Displays single event with thumbnail
 *
 * @param {Event} event - Event object from API
 * @param {Function} onClick - Click handler
 * @returns {HTMLElement} Rendered card element
 */
export function EventCard(event, onClick) {
  // Create container
  const card = document.createElement('div')
  card.className = 'event-card'

  // Render content
  card.innerHTML = `
    <div class="event-card__image">
      <img src="/api/v1/events/${event.event_id}/image"
           alt="${event.llm_description}"
           loading="lazy">
    </div>
    <div class="event-card__content">
      <h3>${event.llm_description}</h3>
      <p>${formatTimestamp(event.timestamp)}</p>
    </div>
  `

  // Attach event listeners
  card.addEventListener('click', () => onClick(event.event_id))

  return card
}

// Helper functions at bottom
function formatTimestamp(timestamp) {
  return new Date(timestamp).toLocaleString()
}
```

---
