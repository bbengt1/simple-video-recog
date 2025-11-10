# Metrics and configuration API endpoints

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from api.models import ConfigResponse, MetricsResponse
from core.metrics import get_metrics_collector

router = APIRouter()
logger = logging.getLogger(__name__)


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
            timestamp=snapshot.timestamp,
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
