# JavaScript Code Style

## ES6+ Standards

Use modern JavaScript (ES6+) with these conventions:

**Module System:**
- Use ES6 modules (`import`/`export`), not CommonJS (`require`)
- Named exports for utilities, default export for main component
```javascript
// Good
export function EventCard(event, onClick) { ... }
export function formatTimestamp(timestamp) { ... }

// Also good for main component
export default function Dashboard() { ... }
```

**Variable Declaration:**
- Use `const` by default, `let` only when reassignment needed
- Never use `var`
```javascript
const event = { ... };  // Immutable reference
let counter = 0;        // Will be reassigned
```

**Arrow Functions:**
- Use arrow functions for callbacks and short functions
- Use regular functions for component factories (better stack traces)
```javascript
// Arrow for callbacks
events.map(event => EventCard(event, handleClick));

// Regular function for components
export function EventCard(event, onClick) {
  const card = document.createElement('div');
  // ...
}
```

**Template Literals:**
- Use template literals for string interpolation and multiline strings
```javascript
card.innerHTML = `
  <div class="event-card__header">
    <span>${event.camera_id}</span>
    <span>${formatTimestamp(event.timestamp)}</span>
  </div>
`;
```

**Object and Array Destructuring:**
```javascript
// Object destructuring
const { event_id, timestamp, llm_description } = event;

// Array destructuring
const [events, setEvents] = useState([]);
```

**Async/Await:**
- Prefer async/await over raw Promises
```javascript
// Good
async function fetchEvents() {
  try {
    const response = await fetch('/api/v1/events');
    const data = await response.json();
    return data.events;
  } catch (error) {
    console.error('Failed to fetch events:', error);
    throw error;
  }
}

// Avoid
function fetchEvents() {
  return fetch('/api/v1/events')
    .then(response => response.json())
    .then(data => data.events)
    .catch(error => console.error(error));
}
```

**No Semicolons:**
- Omit semicolons (consistent with modern JavaScript style guides)
- Exception: Required when line starts with `[` or `(`
```javascript
const events = []
const card = document.createElement('div')

// Exception
;[1, 2, 3].forEach(n => console.log(n))
```

---
