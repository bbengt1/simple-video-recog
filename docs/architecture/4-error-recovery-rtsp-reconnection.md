# 4. Error Recovery (RTSP Reconnection)

```mermaid
sequenceDiagram
    participant Pipeline as Processing Pipeline
    participant RTSP as RTSP Client
    participant Logger as Application Logger

    Pipeline->>RTSP: get_frame()
    RTSP-->>Pipeline: None (connection lost)

    Pipeline->>Logger: log.warning("RTSP connection lost")

    Pipeline->>RTSP: is_connected()
    RTSP-->>Pipeline: False

    Pipeline->>Pipeline: sleep(1s)
    Pipeline->>RTSP: connect()
    RTSP-->>Pipeline: False (retry 1 failed)

    Pipeline->>Pipeline: sleep(2s)
    Pipeline->>RTSP: connect()
    RTSP-->>Pipeline: False (retry 2 failed)

    Pipeline->>Pipeline: sleep(4s)
    Pipeline->>RTSP: connect()
    RTSP-->>Pipeline: True (reconnected)

    Pipeline->>Logger: log.info("RTSP connection restored")

    Note over Pipeline: Resume normal processing
```

**Reconnection Strategy:**
- Exponential backoff: 1s, 2s, 4s, 8s (max)
- After 5 consecutive failures: log ERROR and exit
- Reset backoff counter on successful connection
- Continue processing other frames during reconnection attempts

---
