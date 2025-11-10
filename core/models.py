"""Data models for the video recognition system.

This module defines Pydantic models for core data structures used throughout
the system, including detected objects, bounding boxes, and detection results.
"""

from typing import List, Tuple

from pydantic import BaseModel, ConfigDict, Field


class BoundingBox(BaseModel):
    """Bounding box coordinates for detected objects.

    Represents pixel coordinates of a detected object's bounding box
    in the original frame coordinate system.
    """

    x: int = Field(
        ...,
        description="Top-left X coordinate in pixels",
        ge=0
    )
    y: int = Field(
        ...,
        description="Top-left Y coordinate in pixels",
        ge=0
    )
    width: int = Field(
        ...,
        description="Box width in pixels",
        gt=0
    )
    height: int = Field(
        ...,
        description="Box height in pixels",
        gt=0
    )

    model_config = ConfigDict()


class DetectedObject(BaseModel):
    """Object detected by CoreML within a frame.

    Represents a single detected object with its label, confidence score,
    and bounding box coordinates.
    """

    label: str = Field(
        ...,
        description="Object class label from CoreML model",
        examples=["person"]
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence score",
        examples=[0.92]
    )
    bbox: BoundingBox = Field(
        ...,
        description="Bounding box coordinates"
    )

    model_config = ConfigDict()


class DetectionResult(BaseModel):
    """Result of object detection inference on a frame.

    Contains the list of detected objects, inference timing, and frame metadata.
    Returned by CoreML detector after processing a frame.
    """

    objects: List[DetectedObject] = Field(
        default_factory=list,
        description="List of detected objects in the frame"
    )
    inference_time: float = Field(
        ...,
        description="Time taken for inference in seconds",
        ge=0.0,
        examples=[0.05]
    )
    frame_shape: Tuple[int, int, int] = Field(
        ...,
        description="Shape of the processed frame (height, width, channels)",
        examples=[(480, 640, 3)]
    )

    model_config = ConfigDict()
