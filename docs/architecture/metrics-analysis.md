# Metrics Analysis

## Analyzing Metrics with Command-Line Tools

**View latest metrics:**
```bash
# View last 10 metrics snapshots
tail -n 10 logs/metrics.json | jq .

# Pretty-print latest snapshot
tail -n 1 logs/metrics.json | jq .
```

**Calculate averages over time:**
```bash
# Average CoreML inference time over last 100 snapshots
tail -n 100 logs/metrics.json | jq -s 'map(.coreml_inference_avg) | add / length'

# Average CPU usage
tail -n 100 logs/metrics.json | jq -s 'map(.cpu_usage) | add / length'
```

**Check for NFR violations:**
```bash
# Find snapshots where CoreML p95 exceeds 100ms
cat logs/metrics.json | jq 'select(.coreml_inference_p95 > 100)'

# Find snapshots where LLM p95 exceeds 3000ms
cat logs/metrics.json | jq 'select(.llm_inference_p95 > 3000)'

# Check storage approaching limit
cat logs/metrics.json | jq 'select(.storage_usage_gb > 3.2)' | tail -n 5
```

**Generate time-series data for plotting:**
```bash
# Extract timestamp and CPU usage for plotting
cat logs/metrics.json | jq -r '[.timestamp, .cpu_usage] | @csv' > cpu_usage.csv

# Extract inference times
cat logs/metrics.json | jq -r '[.timestamp, .coreml_inference_avg, .llm_inference_avg] | @csv' > inference_times.csv
```

## Python Analysis Script

```python
# scripts/analyze_metrics.py
"""Analyze metrics.json to generate performance report."""
import json
from pathlib import Path
from datetime import datetime, timedelta

def analyze_metrics(metrics_file="logs/metrics.json"):
    """Generate performance report from metrics."""
    metrics = []

    with open(metrics_file) as f:
        for line in f:
            metrics.append(json.loads(line))

    if not metrics:
        print("No metrics found")
        return

    # Get metrics from last 24 hours
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_metrics = [
        m for m in metrics
        if datetime.fromisoformat(m["timestamp"].replace("Z", "")) > cutoff
    ]

    # Calculate statistics
    print("=== Performance Report (Last 24 Hours) ===\n")

    print(f"Total Snapshots: {len(recent_metrics)}")
    print(f"Uptime: {recent_metrics[-1]['uptime_seconds'] // 3600} hours\n")

    # Processing stats
    total_frames = recent_metrics[-1]["frames_processed"]
    total_motion = recent_metrics[-1]["motion_detected"]
    total_events = recent_metrics[-1]["events_created"]

    print(f"Frames Processed: {total_frames:,}")
    print(f"Motion Detected: {total_motion:,} ({total_motion/total_frames*100:.1f}%)")
    print(f"Events Created: {total_events:,}\n")

    # Performance metrics
    avg_coreml = sum(m["coreml_inference_avg"] for m in recent_metrics) / len(recent_metrics)
    max_coreml_p95 = max(m["coreml_inference_p95"] for m in recent_metrics)

    avg_llm = sum(m["llm_inference_avg"] for m in recent_metrics) / len(recent_metrics)
    max_llm_p95 = max(m["llm_inference_p95"] for m in recent_metrics)

    print(f"CoreML Inference (avg): {avg_coreml:.1f}ms")
    print(f"CoreML Inference (max p95): {max_coreml_p95:.1f}ms {'❌ EXCEEDS TARGET' if max_coreml_p95 > 100 else '✅ MEETS TARGET'}")

    print(f"\nLLM Inference (avg): {avg_llm:.0f}ms")
    print(f"LLM Inference (max p95): {max_llm_p95:.0f}ms {'❌ EXCEEDS TARGET' if max_llm_p95 > 3000 else '✅ MEETS TARGET'}\n")

    # Resource usage
    avg_cpu = sum(m["cpu_usage"] for m in recent_metrics) / len(recent_metrics)
    max_cpu = max(m["cpu_usage"] for m in recent_metrics)
    avg_memory = sum(m["memory_usage_mb"] for m in recent_metrics) / len(recent_metrics)
    max_memory = max(m["memory_usage_mb"] for m in recent_metrics)

    print(f"CPU Usage (avg): {avg_cpu:.1f}%")
    print(f"CPU Usage (max): {max_cpu:.1f}%")
    print(f"Memory Usage (avg): {avg_memory:.0f}MB")
    print(f"Memory Usage (max): {max_memory:.0f}MB\n")

    # Storage
    current_storage = recent_metrics[-1]["storage_usage_gb"]
    print(f"Storage Usage: {current_storage:.2f}GB / 4.00GB ({current_storage/4*100:.1f}%)")

if __name__ == "__main__":
    analyze_metrics()
```

---
