# REST API Specification (Phase 2)

```yaml
openapi: 3.0.0
info:
  title: Local Video Recognition System API
  version: 1.0.0
  description: |
    REST API for the Local Video Recognition System web dashboard.
    Provides access to event data, system metrics, and real-time event streaming via WebSocket.

    **Authentication:** None (localhost-only access in Phase 2)
    **Base URL:** http://localhost:8000/api/v1

servers:
  - url: http://localhost:8000/api/v1
    description: Local development server

paths:
  /health:
    get:
      summary: Health check endpoint
      description: Returns system health status including service availability
      responses:
        '200':
          description: System is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"
                  services:
                    type: object
                    properties:
                      database:
                        type: string
                        example: "ok"
                      ollama:
                        type: string
                        example: "ok"
                      rtsp_camera:
                        type: string
                        example: "ok"
                  uptime_seconds:
                    type: integer
                    example: 86400

  /metrics:
    get:
      summary: Get current system metrics
      description: Returns latest performance metrics snapshot
      responses:
        '200':
          description: Current metrics
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MetricsSnapshot'

  /events:
    get:
      summary: List events with filtering
      description: Retrieve events with optional time range and pagination
      parameters:
        - name: start
          in: query
          schema:
            type: string
            format: date-time
          description: Start of time range (ISO 8601)
        - name: end
          in: query
          schema:
            type: string
            format: date-time
          description: End of time range (ISO 8601)
        - name: camera_id
          in: query
          schema:
            type: string
          description: Filter by camera ID
        - name: limit
          in: query
          schema:
            type: integer
            default: 100
            minimum: 1
            maximum: 1000
          description: Maximum number of results
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
            minimum: 0
          description: Pagination offset
      responses:
        '200':
          description: List of events
          content:
            application/json:
              schema:
                type: object
                properties:
                  events:
                    type: array
                    items:
                      $ref: '#/components/schemas/Event'
                  total:
                    type: integer
                    description: Total count of events matching filters
                  limit:
                    type: integer
                  offset:
                    type: integer

  /events/{event_id}:
    get:
      summary: Get event by ID
      parameters:
        - name: event_id
          in: path
          required: true
          schema:
            type: string
          description: Event identifier
      responses:
        '200':
          description: Event details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Event'
        '404':
          description: Event not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /events/{event_id}/image:
    get:
      summary: Get annotated image for event
      parameters:
        - name: event_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Annotated image with bounding boxes
          content:
            image/jpeg:
              schema:
                type: string
                format: binary
        '404':
          description: Image not found

  /config:
    get:
      summary: Get current system configuration
      description: Returns sanitized configuration (excludes sensitive fields like passwords)
      responses:
        '200':
          description: System configuration
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SystemConfig'

components:
  schemas:
    Event:
      type: object
      properties:
        event_id:
          type: string
          example: "evt_1699459335_a7b3c"
        timestamp:
          type: string
          format: date-time
          example: "2025-11-08T14:32:15Z"
        camera_id:
          type: string
          example: "front_door"
        motion_confidence:
          type: number
          format: float
          minimum: 0
          maximum: 1
          example: 0.87
        detected_objects:
          type: array
          items:
            $ref: '#/components/schemas/DetectedObject'
        llm_description:
          type: string
          example: "Person in blue shirt carrying brown package approaching front door"
        image_path:
          type: string
          example: "data/events/2025-11-08/evt_1699459335_a7b3c.jpg"
        json_log_path:
          type: string
          example: "data/events/2025-11-08/events.json"
        created_at:
          type: string
          format: date-time
          example: "2025-11-08T14:32:16Z"

    DetectedObject:
      type: object
      properties:
        label:
          type: string
          example: "person"
        confidence:
          type: number
          format: float
          minimum: 0
          maximum: 1
          example: 0.92
        bbox:
          $ref: '#/components/schemas/BoundingBox'

    BoundingBox:
      type: object
      properties:
        x:
          type: integer
          minimum: 0
          example: 120
        y:
          type: integer
          minimum: 0
          example: 50
        width:
          type: integer
          minimum: 1
          example: 180
        height:
          type: integer
          minimum: 1
          example: 320

    MetricsSnapshot:
      type: object
      properties:
        timestamp:
          type: string
          format: date-time
        frames_processed:
          type: integer
        motion_detected:
          type: integer
        events_created:
          type: integer
        events_suppressed:
          type: integer
        coreml_inference_avg:
          type: number
          format: float
        coreml_inference_p95:
          type: number
          format: float
        llm_inference_avg:
          type: number
          format: float
        llm_inference_p95:
          type: number
          format: float
        cpu_usage:
          type: number
          format: float
        memory_usage_mb:
          type: integer
        storage_usage_gb:
          type: number
          format: float
        uptime_seconds:
          type: integer

    SystemConfig:
      type: object
      description: Sanitized system configuration (sensitive fields excluded)
      properties:
        camera_id:
          type: string
        motion_threshold:
          type: number
        frame_sample_rate:
          type: integer
        blacklist_objects:
          type: array
          items:
            type: string
        ollama_model:
          type: string
        max_storage_gb:
          type: number
        log_level:
          type: string

    Error:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
              example: "NOT_FOUND"
            message:
              type: string
              example: "Event not found"
            details:
              type: object
              additionalProperties: true
            timestamp:
              type: string
              format: date-time
            requestId:
              type: string
```
