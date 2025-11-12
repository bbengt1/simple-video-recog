# Metrics and configuration API endpoints

import logging
import time
from datetime import datetime, timedelta

import psutil
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db_connection
from api.models import (
    CameraActivity,
    ConfigResponse,
    DashboardMetricsResponse,
    EventStatistics,
    MetricsResponse,
    SystemMetrics,
)
from core.metrics import get_metrics_collector

router = APIRouter()
logger = logging.getLogger(__name__)

# Track application startup time for uptime calculation
_app_start_time = time.time()

# Cache for legacy metrics endpoint to reduce collection frequency
_metrics_cache = None
_metrics_cache_time = 0
_METRICS_CACHE_TTL = 10  # Cache metrics for 10 seconds


@router.get("/dashboard/metrics", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(db_conn = Depends(get_db_connection)):
    """
    Get dashboard metrics for system health display.

    Returns system health metrics, event statistics, and camera activity
    in the format expected by the dashboard metrics panel.
    """
    try:
        # Get system metrics
        system_metrics = _collect_system_metrics()

        # Get event statistics
        event_stats = _collect_event_statistics(db_conn)

        # Get camera activity
        camera_activity = _collect_camera_activity(db_conn)

        response = DashboardMetricsResponse(
            system=system_metrics,
            events=event_stats,
            cameras=camera_activity
        )

        logger.info("Dashboard metrics retrieved successfully")
        return response

    except Exception as e:
        logger.error(f"Error retrieving dashboard metrics: {e}")
        # Return minimal metrics rather than failing
        return DashboardMetricsResponse(
            system=SystemMetrics(
                cpu_usage_percent=0.0,
                memory_used=0,
                memory_total=psutil.virtual_memory().total,
                disk_used=0,
                disk_total=psutil.disk_usage('/').total,
                disk_usage_percent=0.0,
                system_uptime_seconds=int(time.time() - psutil.boot_time()),
                app_uptime_seconds=int(time.time() - _app_start_time)
            ),
            events=EventStatistics(
                total_events=0,
                events_today=0,
                events_this_hour=0,
                events_per_hour_avg=0.0,
                events_per_hour_previous=0.0
            ),
            cameras=[]
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get current system metrics.

    Returns latest performance metrics from the MetricsCollector singleton.
    Includes processing statistics, inference times, and resource usage.
    """
    try:
        collector = get_metrics_collector()
        snapshot = collector.collect()

        response = MetricsResponse(
            timestamp=datetime.fromtimestamp(snapshot.timestamp),
            frames_processed=snapshot.frames_processed,
            motion_detected=snapshot.motion_detected,
            motion_hit_rate=snapshot.motion_hit_rate,
            events_created=snapshot.events_created,
            events_suppressed=snapshot.events_suppressed,
            coreml_inference_avg=snapshot.coreml_inference_avg,
            coreml_inference_min=snapshot.coreml_inference_min,
            coreml_inference_max=snapshot.coreml_inference_max,
            coreml_inference_p95=snapshot.coreml_inference_p95,
            llm_inference_avg=snapshot.llm_inference_avg,
            llm_inference_min=snapshot.llm_inference_min,
            llm_inference_max=snapshot.llm_inference_max,
            llm_inference_p95=snapshot.llm_inference_p95,
            frame_processing_latency_avg=snapshot.frame_processing_latency_avg,
            cpu_usage_current=snapshot.cpu_usage_current,
            cpu_usage_avg=snapshot.cpu_usage_avg,
            memory_usage_mb=snapshot.memory_usage_mb,
            memory_usage_gb=snapshot.memory_usage_gb,
            memory_usage_percent=snapshot.memory_usage_percent,
            system_uptime_percent=snapshot.system_uptime_percent,
            version="1.0.0"
        )

        logger.info("Metrics retrieved successfully")
        return response

    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        # Return empty metrics rather than failing
        return MetricsResponse(
            timestamp=datetime.now(),
            frames_processed=0,
            motion_detected=0,
            motion_hit_rate=0.0,
            events_created=0,
            events_suppressed=0,
            coreml_inference_avg=0.0,
            coreml_inference_min=0.0,
            coreml_inference_max=0.0,
            coreml_inference_p95=0.0,
            llm_inference_avg=0.0,
            llm_inference_min=0.0,
            llm_inference_max=0.0,
            llm_inference_p95=0.0,
            frame_processing_latency_avg=0.0,
            cpu_usage_current=0.0,
            cpu_usage_avg=0.0,
            memory_usage_mb=0,
            memory_usage_gb=0.0,
            memory_usage_percent=0.0,
            system_uptime_percent=0.0,
            version="1.0.0"
        )


def _collect_system_metrics() -> SystemMetrics:
    """Collect system health metrics."""
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return SystemMetrics(
        cpu_usage_percent=psutil.cpu_percent(interval=0.1),
        memory_used=int(vm.used),
        memory_total=int(vm.total),
        disk_used=int(disk.used),
        disk_total=int(disk.total),
        disk_usage_percent=disk.percent,
        system_uptime_seconds=int(time.time() - psutil.boot_time()),
        app_uptime_seconds=int(time.time() - _app_start_time)
    )


def _collect_event_statistics(db_conn) -> EventStatistics:
    """Collect event statistics from database."""
    cursor = db_conn.cursor()

    # Total events
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    # Events today
    today = datetime.now().date()
    cursor.execute("SELECT COUNT(*) FROM events WHERE DATE(timestamp) = ?", (today.isoformat(),))
    events_today = cursor.fetchone()[0]

    # Events this hour
    one_hour_ago = datetime.now() - timedelta(hours=1)
    cursor.execute("SELECT COUNT(*) FROM events WHERE timestamp >= ?", (one_hour_ago.isoformat(),))
    events_this_hour = cursor.fetchone()[0]

    # Events per hour average (last 24 hours)
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
    cursor.execute("SELECT COUNT(*) FROM events WHERE timestamp >= ?", (twenty_four_hours_ago.isoformat(),))
    events_last_24h = cursor.fetchone()[0]
    events_per_hour_avg = events_last_24h / 24.0 if events_last_24h > 0 else 0.0

    # Events per hour previous (previous 24 hour period)
    forty_eight_hours_ago = datetime.now() - timedelta(hours=48)
    cursor.execute(
        "SELECT COUNT(*) FROM events WHERE timestamp >= ? AND timestamp < ?",
        (forty_eight_hours_ago.isoformat(), twenty_four_hours_ago.isoformat())
    )
    events_previous_24h = cursor.fetchone()[0]
    events_per_hour_previous = events_previous_24h / 24.0 if events_previous_24h > 0 else 0.0

    return EventStatistics(
        total_events=total_events,
        events_today=events_today,
        events_this_hour=events_this_hour,
        events_per_hour_avg=events_per_hour_avg,
        events_per_hour_previous=events_per_hour_previous
    )


def _collect_camera_activity(db_conn) -> list[CameraActivity]:
    """Collect camera activity statistics."""
    cursor = db_conn.cursor()

    # Get event counts and last event times per camera
    cursor.execute("""
        SELECT
            camera_id,
            COUNT(*) as event_count,
            MAX(timestamp) as last_event_time
        FROM events
        GROUP BY camera_id
        ORDER BY last_event_time DESC
    """)

    cameras = []
    for row in cursor.fetchall():
        cameras.append(CameraActivity(
            camera_id=row['camera_id'],
            event_count=row['event_count'],
            last_event_time=row['last_event_time']
        ))

    return cameras


@router.get("/metrics/legacy", response_model=MetricsResponse)
async def get_legacy_metrics():
    """
    Get legacy processing metrics.

    Returns the original processing-focused metrics for backward compatibility.
    Uses caching to reduce collection frequency.
    """
    global _metrics_cache, _metrics_cache_time

    try:
        # Check cache first
        current_time = time.time()
        if _metrics_cache is not None and (current_time - _metrics_cache_time) < _METRICS_CACHE_TTL:
            logger.debug("Returning cached metrics")
            return _metrics_cache

        # Collect fresh metrics
        collector = get_metrics_collector()
        snapshot = collector.collect()

        response = MetricsResponse(
            timestamp=datetime.fromtimestamp(snapshot.timestamp),
            frames_processed=snapshot.frames_processed,
            motion_detected=snapshot.motion_detected,
            motion_hit_rate=snapshot.motion_hit_rate,
            events_created=snapshot.events_created,
            events_suppressed=snapshot.events_suppressed,
            coreml_inference_avg=snapshot.coreml_inference_avg,
            coreml_inference_min=snapshot.coreml_inference_min,
            coreml_inference_max=snapshot.coreml_inference_max,
            coreml_inference_p95=snapshot.coreml_inference_p95,
            llm_inference_avg=snapshot.llm_inference_avg,
            llm_inference_min=snapshot.llm_inference_min,
            llm_inference_max=snapshot.llm_inference_max,
            llm_inference_p95=snapshot.llm_inference_p95,
            frame_processing_latency_avg=snapshot.frame_processing_latency_avg,
            cpu_usage_current=snapshot.cpu_usage_current,
            cpu_usage_avg=snapshot.cpu_usage_avg,
            memory_usage_mb=snapshot.memory_usage_mb,
            memory_usage_gb=snapshot.memory_usage_gb,
            memory_usage_percent=snapshot.memory_usage_percent,
            system_uptime_percent=snapshot.system_uptime_percent,
            version="1.0.0"
        )

        # Cache the response
        _metrics_cache = response
        _metrics_cache_time = current_time

        logger.info("Legacy metrics retrieved successfully")
        return response

    except Exception as e:
        logger.error(f"Error retrieving legacy metrics: {e}")
        # Return empty metrics rather than failing
        return MetricsResponse(
            timestamp=datetime.now(),
            frames_processed=0,
            motion_detected=0,
            motion_hit_rate=0.0,
            events_created=0,
            events_suppressed=0,
            coreml_inference_avg=0.0,
            coreml_inference_min=0.0,
            coreml_inference_max=0.0,
            coreml_inference_p95=0.0,
            llm_inference_avg=0.0,
            llm_inference_min=0.0,
            llm_inference_max=0.0,
            llm_inference_p95=0.0,
            frame_processing_latency_avg=0.0,
            cpu_usage_current=0.0,
            cpu_usage_avg=0.0,
            memory_usage_mb=0,
            memory_usage_gb=0.0,
            memory_usage_percent=0.0,
            system_uptime_percent=0.0,
            version="1.0.0"
        )


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """
    Get sanitized system configuration.

    Returns configuration excluding sensitive fields (RTSP URL, passwords).
    """
    from api.dependencies import get_config

    try:
        config = get_config()

        response = ConfigResponse(
            camera_id=config.camera_id,
            motion_threshold=config.motion_threshold,
            frame_sample_rate=config.frame_sample_rate,
            blacklist_objects=config.blacklist_objects,
            min_object_confidence=config.min_object_confidence,
            ollama_model=config.ollama_model,
            max_storage_gb=config.max_storage_gb,
            min_retention_days=config.min_retention_days,
            log_level=config.log_level,
            metrics_interval=config.metrics_interval,
            version="1.0.0"
        )

        logger.info("Configuration retrieved successfully")
        return response

    except Exception as e:
        logger.error(f"Error retrieving configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
