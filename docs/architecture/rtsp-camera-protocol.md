# RTSP Camera Protocol

- **Purpose:** Capture video stream from IP camera for motion detection and object recognition
- **Documentation:** RTSP standard (RFC 2326), camera manufacturer docs for specific URL format
- **Base URL(s):** rtsp://[username:password]@[camera_ip]:[port]/[stream_path]
- **Authentication:** Basic auth via RTSP URL credentials
- **Rate Limits:** Limited by camera's maximum frame rate (typically 15-30 fps)

**Key Endpoints Used:**
- Primary stream: High resolution (1920x1080) for object detection
- Substream: Lower resolution (640x480) for motion detection (camera-dependent)

**Integration Notes:**
- OpenCV VideoCapture handles RTSP protocol negotiation automatically
- URL format varies by manufacturer (Hikvision, Dahua, Reolink, etc.)
- Connection stability depends on network quality
- Implements reconnection logic with exponential backoff
- Frame capture timeout: 5 seconds
- Supports only H.264/H.265 video codecs (most common)

**Example URLs:**
```
# Hikvision
rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101

# Reolink
rtsp://admin:password@192.168.1.100:554/h264Preview_01_main

# Generic
rtsp://username:password@camera-ip:554/stream1
```

---
