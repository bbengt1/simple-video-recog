"""Split-screen terminal UI for video recognition system.

Provides a terminal interface with metrics display on top and logs on bottom.
Uses Rich library for terminal UI components.
"""

import threading
import time
from typing import Optional

from rich.console import Console  # type: ignore
from rich.layout import Layout  # type: ignore
from rich.live import Live  # type: ignore
from rich.panel import Panel  # type: ignore
from rich.text import Text  # type: ignore

from core.logging_config import get_logger

logger = get_logger(__name__)


class SplitScreenUI:
    """Split-screen terminal UI with metrics on top and logs on bottom."""

    def __init__(self, metrics_collector, config):
        """Initialize the split-screen UI.

        Args:
            metrics_collector: MetricsCollector instance for metrics display
            config: SystemConfig instance
        """
        self.metrics_collector = metrics_collector
        self.config = config
        self.console = Console()
        self.live: Optional[Live] = None  # type: ignore
        self.layout = Layout()
        self.log_lines = []
        self.max_log_lines = 100  # Keep last 100 log lines
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # Setup layout
        self.layout.split_column(
            Layout(name="metrics", size=10),  # Top panel for metrics (compact display)
            Layout(name="logs")               # Bottom panel for logs
        )

        # Override logging to capture logs for display
        self._setup_log_capture()

    def _setup_log_capture(self):
        """Setup log capture to display logs in the bottom panel."""
        import logging
        from core.logging_config import get_logger

        # Create a custom handler that captures log messages
        class LogCaptureHandler(logging.Handler):
            def __init__(self, ui):
                super().__init__()
                self.ui = ui
                # Set formatter to match the existing log format
                formatter = logging.Formatter(
                    '%(asctime)s.%(msecs)03d [%(levelname)s] [%(name)s] %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S'
                )
                self.setFormatter(formatter)

            def emit(self, record):
                try:
                    msg = self.format(record)
                    self.ui.add_log_line(msg)
                except Exception:
                    pass  # Don't let log capture errors break the system

        # Add our handler to the root logger
        root_logger = logging.getLogger()
        self.log_handler = LogCaptureHandler(self)
        root_logger.addHandler(self.log_handler)

    def add_log_line(self, line: str):
        """Add a log line to the display buffer."""
        self.log_lines.append(line)
        # Keep only the last N lines
        if len(self.log_lines) > self.max_log_lines:
            self.log_lines = self.log_lines[-self.max_log_lines:]

    def _get_metrics_display(self) -> str:
        """Get a compact metrics display optimized for split-screen."""
        try:
            snapshot = self.metrics_collector.collect()

            # Format uptime
            uptime_seconds = time.time() - self.metrics_collector.system_start_time
            if uptime_seconds < 60:
                uptime_str = f"{uptime_seconds:.0f}s"
            elif uptime_seconds < 3600:
                uptime_str = f"{uptime_seconds/60:.0f}m"
            else:
                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                uptime_str = f"{hours}h{minutes}m"

            # NFR indicators
            coreml_indicator = "✓" if snapshot.coreml_inference_avg < 100 else ("⚠" if snapshot.coreml_inference_avg < 200 else "✗")
            llm_indicator = "✓" if snapshot.llm_inference_avg < 2.0 else ("⚠" if snapshot.llm_inference_avg < 5.0 else "✗")
            latency_indicator = "✓" if snapshot.frame_processing_latency_avg < 3.0 else ("⚠" if snapshot.frame_processing_latency_avg < 5.0 else "✗")
            cpu_indicator = "✓" if snapshot.cpu_usage_avg < 60 else ("⚠" if snapshot.cpu_usage_avg < 80 else "✗")
            mem_indicator = "✓" if snapshot.memory_usage_percent < 60 else ("⚠" if snapshot.memory_usage_percent < 80 else "✗")
            uptime_indicator = "✓" if snapshot.system_uptime_percent >= 99.0 else ("⚠" if snapshot.system_uptime_percent >= 95.0 else "✗")

            # Create compact multi-line display for split-screen
            lines = [
                f"📊 System Metrics - {time.strftime('%H:%M:%S')} (up: {uptime_str})",
                f"Frames: {snapshot.frames_processed:,} | Motion: {snapshot.motion_detected:,} ({snapshot.motion_hit_rate:.1f}%)",
                f"Events: {snapshot.events_created:,} created, {snapshot.events_suppressed:,} suppressed",
                f"CoreML: {coreml_indicator} {snapshot.coreml_inference_avg:.0f}ms | LLM: {llm_indicator} {snapshot.llm_inference_avg:.1f}s",
                f"Latency: {latency_indicator} {snapshot.frame_processing_latency_avg:.1f}s | Uptime: {uptime_indicator} {snapshot.system_uptime_percent:.1f}%",
                f"CPU: {cpu_indicator} {snapshot.cpu_usage_avg:.1f}% ({snapshot.cpu_usage_current:.1f}%) | Mem: {mem_indicator} {snapshot.memory_usage_gb:.1f}GB ({snapshot.memory_usage_percent:.1f}%)",
                "[✓] Good  [⚠] Warning  [✗] Critical"
            ]

            return "\n".join(lines)
        except Exception as e:
            return f"Error getting metrics: {e}"

    def _get_logs_display(self) -> str:
        """Get the current logs display."""
        if not self.log_lines:
            return "No logs yet..."

        # Join the last log lines
        return "\n".join(self.log_lines[-50:])  # Show last 50 lines in the panel

    def _generate_display(self) -> Layout:
        """Generate the current display layout."""
        # Update the layout with current content
        metrics_content = self._get_metrics_display()
        logs_content = self._get_logs_display()

        # Create fresh panels to avoid stacking issues
        metrics_panel = Panel(
            Text(metrics_content, style="bold cyan"),
            title="📊 System Metrics",
            border_style="blue"
        )

        logs_panel = Panel(
            Text(logs_content, style="dim white"),
            title="📝 System Logs",
            border_style="green"
        )

        self.layout["metrics"].update(metrics_panel)
        self.layout["logs"].update(logs_panel)

        return self.layout

    def start(self):
        """Start the split-screen UI display."""
        if self.running:
            return

        self.running = True
        self.live = Live(self._generate_display(), console=self.console, refresh_per_second=2)
        if self.live:
            self.live.start()

        # Start update thread
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

        logger.info("Split-screen UI started")

    def stop(self):
        """Stop the split-screen UI display."""
        if not self.running:
            return

        self.running = False

        if self.live:
            self.live.stop()

        if self.thread:
            self.thread.join(timeout=1.0)

        logger.info("Split-screen UI stopped")

    def _update_loop(self):
        """Update loop for the live display."""
        while self.running:
            try:
                if self.live:
                    self.live.update(self._generate_display())
                time.sleep(0.5)  # Update twice per second
            except Exception as e:
                logger.error(f"Error updating split-screen UI: {e}")
                break

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()