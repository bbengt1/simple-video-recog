#!/usr/bin/env python3
"""Demo script for split-screen UI functionality.

This script demonstrates the split-screen interface with mock metrics and logs.
"""

import time
import threading
from core.config import SystemConfig
from core.metrics import MetricsCollector
from core.split_screen_ui import SplitScreenUI

def mock_metrics_updates(metrics_collector: MetricsCollector):
    """Mock metrics updates to simulate system activity."""
    for i in range(20):
        # Simulate some processing activity (increment multiple times for demo)
        for _ in range(10):
            metrics_collector.increment_counter("frames_processed")
        if i % 3 == 0:
            metrics_collector.increment_counter("events_created")
        time.sleep(1)

def mock_logging():
    """Mock logging activity to show logs in the bottom panel."""
    import logging
    logger = logging.getLogger("demo")

    for i in range(20):
        if i % 2 == 0:
            logger.info(f"Processing frame {i*10}, motion detected")
        else:
            logger.debug(f"Frame {i*10} processed successfully")
        time.sleep(0.8)

def main():
    """Run the split-screen demo."""
    print("Split-Screen UI Demo")
    print("====================")
    print("This demo shows the split-screen interface with:")
    print("- Top panel: System metrics")
    print("- Bottom panel: System logs")
    print("")
    print("Press Ctrl+C to exit")
    print("")

    # Create a basic config
    config = SystemConfig(
        camera_rtsp_url="rtsp://demo",
        camera_id="demo_camera",
        motion_threshold=0.5,
        frame_sample_rate=5,
        coreml_model_path="models/demo.mlmodel",
        blacklist_objects=["bird"],
        min_object_confidence=0.5,
        ollama_base_url="http://localhost:11434",
        ollama_model="llava:7b",
        llm_timeout=10,
        deduplication_window=30,
        db_path="data/demo.db",
        max_storage_gb=4.0,
        min_retention_days=7,
        log_level="INFO",
        metrics_interval=10  # Update every 10 seconds for demo
    )

    # Create metrics collector
    metrics_collector = MetricsCollector(config)

    # Create and start split-screen UI
    ui = SplitScreenUI(metrics_collector, config)

    try:
        with ui:
            # Start mock threads
            metrics_thread = threading.Thread(target=mock_metrics_updates, args=(metrics_collector,))
            logging_thread = threading.Thread(target=mock_logging)

            metrics_thread.start()
            logging_thread.start()

            # Wait for threads to complete
            metrics_thread.join()
            logging_thread.join()

    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    finally:
        print("Demo completed")

if __name__ == "__main__":
    main()