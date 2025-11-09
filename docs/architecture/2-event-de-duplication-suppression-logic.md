# 2. Event De-duplication (Suppression Logic)

```mermaid
sequenceDiagram
    participant Pipeline as Processing Pipeline
    participant EventMgr as Event Manager
    participant Cache as Suppression Cache

    Pipeline->>EventMgr: create_event(frame, objects, description)

    EventMgr->>Cache: get_recent_events(limit=5)
    Cache-->>EventMgr: [event1, event2, event3]

    EventMgr->>EventMgr: calculate_object_overlap(new_event, event1)
    Note over EventMgr: 85% overlap - exceeds 80% threshold

    EventMgr->>EventMgr: increment_suppression_counter()

    EventMgr-->>Pipeline: None (event suppressed)

    Note over Pipeline: No persistence, continue to next frame
```

**Suppression Algorithm:**
- Compare new event's detected object labels to last 5 events
- Calculate overlap: `len(set(new) & set(old)) / len(set(new) | set(old))`
- Suppress if overlap ≥ 80%
- Example: ["person", "package"] vs ["person", "dog"] = 1/3 = 33% → NOT suppressed
- Example: ["person", "package"] vs ["person", "package"] = 2/2 = 100% → suppressed

---
