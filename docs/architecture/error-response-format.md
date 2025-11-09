# Error Response Format

## Standard API Error Response

All API error responses follow this consistent JSON structure:

```typescript
interface ApiError {
  error: {
    code: string;           // Machine-readable error code
    message: string;        // Human-readable error message
    details?: Record<string, any>;  // Optional additional context
    timestamp: string;      // ISO 8601 timestamp
    requestId: string;      // Unique request identifier for debugging
  };
}
```

**Example Error Responses:**

**400 Bad Request (Invalid Parameters):**
```json
{
  "error": {
    "code": "INVALID_PARAMETERS",
    "message": "Query parameter 'limit' must be between 1 and 1000",
    "details": {
      "parameter": "limit",
      "value": 5000,
      "constraint": "1 <= limit <= 1000"
    },
    "timestamp": "2025-11-08T14:32:15.123Z",
    "requestId": "req_abc123def456"
  }
}
```

**404 Not Found (Resource Not Found):**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Event not found",
    "details": {
      "event_id": "evt_nonexistent",
      "resource_type": "Event"
    },
    "timestamp": "2025-11-08T14:32:15.123Z",
    "requestId": "req_xyz789ghi012"
  }
}
```

**500 Internal Server Error (Database Failure):**
```json
{
  "error": {
    "code": "DATABASE_ERROR",
    "message": "Failed to retrieve events from database",
    "details": {
      "operation": "get_recent_events",
      "retryable": true
    },
    "timestamp": "2025-11-08T14:32:15.123Z",
    "requestId": "req_mno345pqr678"
  }
}
```

**503 Service Unavailable (Dependency Failure):**
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Ollama service is unavailable",
    "details": {
      "service": "ollama",
      "url": "http://localhost:11434",
      "retryAfter": 60
    },
    "timestamp": "2025-11-08T14:32:15.123Z",
    "requestId": "req_stu901vwx234"
  }
}
```

---
