# Deployment Procedures

## Initial Production Setup

```bash
# On Production Machine (Mac Mini/Studio)

# 1. Install system dependencies
brew install python@3.10 ollama sqlite

# 2. Start Ollama service
brew services start ollama

# 3. Download LLM model
ollama pull llava:7b

# 4. Clone repository
git clone <repository-url> /opt/video-recognition
cd /opt/video-recognition

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install dependencies
pip install -r requirements.txt

# 7. Download CoreML model
bash scripts/download_models.sh

# 8. Configure environment
cp .env.example .env
nano .env  # Edit with production values

# 9. Create data directories
mkdir -p data/events logs models

# 10. Initialize database
python main.py --dry-run

# 11. Test run (foreground)
python main.py
# Ctrl+C after verifying it works

# 12. Install as launchd service
cp scripts/com.local.video-recognition.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.local.video-recognition.plist

# 13. Verify service is running
launchctl list | grep video-recognition
tail -f logs/app.log
```

## launchd Service Configuration

**Processing Engine Service** (`com.local.video-recognition.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.local.video-recognition</string>

    <key>ProgramArguments</key>
    <array>
        <string>/opt/video-recognition/venv/bin/python</string>
        <string>/opt/video-recognition/main.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/opt/video-recognition</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>

    <key>StandardOutPath</key>
    <string>/opt/video-recognition/logs/stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/opt/video-recognition/logs/stderr.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>  <!-- Restart on crash -->
    </dict>

    <key>ProcessType</key>
    <string>Interactive</string>  <!-- Allows access to GPU/Neural Engine -->
</dict>
</plist>
```

**API Server Service (Phase 2)** (`com.local.video-recognition.api.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.local.video-recognition.api</string>

    <key>ProgramArguments</key>
    <array>
        <string>/opt/video-recognition/venv/bin/uvicorn</string>
        <string>api.server:app</string>
        <string>--host</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>8000</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/opt/video-recognition</string>

    <key>StandardOutPath</key>
    <string>/opt/video-recognition/logs/api-stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/opt/video-recognition/logs/api-stderr.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

## Updating Production Deployment

```bash
# On Production Machine

# 1. Stop services
launchctl unload ~/Library/LaunchAgents/com.local.video-recognition.plist
launchctl unload ~/Library/LaunchAgents/com.local.video-recognition.api.plist  # Phase 2

# 2. Backup database
bash scripts/backup_database.sh

# 3. Pull latest code
cd /opt/video-recognition
git pull origin main

# 4. Update dependencies (if requirements.txt changed)
source venv/bin/activate
pip install -r requirements.txt

# 5. Run migrations (if database schema changed)
python scripts/run_migrations.py

# 6. Restart services
launchctl load ~/Library/LaunchAgents/com.local.video-recognition.plist
launchctl load ~/Library/LaunchAgents/com.local.video-recognition.api.plist  # Phase 2

# 7. Verify deployment
sleep 5
curl http://localhost:8000/api/v1/health  # Phase 2
tail -f logs/app.log
```

## Rollback Procedure

```bash
# If deployment fails, rollback to previous version

# 1. Stop services
launchctl unload ~/Library/LaunchAgents/com.local.video-recognition.plist

# 2. Rollback code
git reset --hard HEAD~1  # Or specific commit: git reset --hard <commit-sha>

# 3. Restore database backup (if schema changed)
cp backups/events_backup_<timestamp>.db data/events.db

# 4. Restart services
launchctl load ~/Library/LaunchAgents/com.local.video-recognition.plist

# 5. Verify rollback
tail -f logs/app.log
```

## Monitoring Production

```bash
# Check service status
launchctl list | grep video-recognition

# View recent logs
tail -n 100 logs/app.log

# View real-time logs
tail -f logs/app.log

# Check health endpoint (Phase 2)
curl http://localhost:8000/api/v1/health | jq .

# View metrics
tail -n 10 logs/metrics.json | jq .

# Check disk usage
du -sh data/
df -h .

# Check system resources
top -pid $(pgrep -f "python main.py")

# View database stats
sqlite3 data/events.db "SELECT COUNT(*) FROM events;"
sqlite3 data/events.db "SELECT DATE(timestamp) as day, COUNT(*) as count FROM events GROUP BY day ORDER BY day DESC LIMIT 7;"
```

---
