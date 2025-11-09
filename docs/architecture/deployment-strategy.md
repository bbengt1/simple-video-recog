# Deployment Strategy

**Frontend Deployment (Phase 2):**
- **Platform:** Local machine (Mac Mini/Studio) - served via nginx or Python HTTP server
- **Build Command:** None - vanilla JavaScript served directly from `web/` directory
- **Output Directory:** `web/` (source files served as-is, no compilation)
- **CDN/Edge:** Not applicable - localhost-only access, no CDN needed

**Backend Deployment:**
- **Platform:** macOS (Mac Mini or Mac Studio with Apple Silicon)
- **Build Command:** None - Python is interpreted, no compilation step
- **Deployment Method:** Manual file transfer to production machine, managed as system service

**Processing Engine (Phase 1):**
- Runs as `launchd` service (macOS system daemon)
- Service file: `~/Library/LaunchAgents/com.local.video-recognition.plist`
- Auto-starts on boot, restarts on crash
- Logs to `logs/app.log` and system log

**API Server (Phase 2):**
- Runs as separate `launchd` service
- Service file: `~/Library/LaunchAgents/com.local.video-recognition.api.plist`
- Listens on `http://localhost:8000`
- Only accessible from local network (no public internet exposure)

**Web Dashboard (Phase 2):**
- Served via nginx reverse proxy or Python HTTP server
- Accessible at `http://[mac-mini-ip]:3000` on local network
- Static file serving (no server-side rendering)

**Rationale:**
- No cloud deployment needed - privacy-first architecture requires local processing
- systemd/launchd ensures 24/7 operation with automatic recovery
- Manual deployment acceptable for personal project (no CI/CD deployment pipeline)
- Nginx provides production-grade static file serving and reverse proxy

---
