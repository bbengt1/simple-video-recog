"""Data models for the video recognition system.

This module defines Pydantic models for core data structures used throughout
the system, including detected objects and bounding boxes.
"""

from pydantic import BaseModel, Field


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

    class Config:
        json_schema_extra = {
            "example": {
                "x": 120,
                "y": 50,
                "width": 180,
                "height": 320
            }
        }


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

    class Config:
        json_schema_extra = {
            "example": {
                "label": "person",
                "confidence": 0.92,
                "bbox": {
                    "x": 120,
                    "y": 50,
                    "width": 180,
                    "height": 320
                }
            }
        }