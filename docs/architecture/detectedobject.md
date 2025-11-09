# DetectedObject

**Purpose:** Represents a single object detected by CoreML within a frame, including its label, confidence score, and bounding box coordinates. Multiple DetectedObject instances are associated with each Event.

**Key Attributes:**
- `label` (str): Object class label from CoreML model (e.g., "person", "car", "dog")
- `confidence` (float): Detection confidence score (0.0-1.0)
- `bbox` (BoundingBox): Bounding box coordinates for the detected object

## Pydantic Schema

```python
class BoundingBox(BaseModel):
    """Bounding box coordinates for detected objects."""

    x: int = Field(..., description="Top-left X coordinate", ge=0)
    y: int = Field(..., description="Top-left Y coordinate", ge=0)
    width: int = Field(..., description="Box width in pixels", gt=0)
    height: int = Field(..., description="Box height in pixels", gt=0)

    class Config:
        json_schema_extra = {
            "example": {"x": 120, "y": 50, "width": 180, "height": 320}
        }


class DetectedObject(BaseModel):
    """Object detected by CoreML within a frame."""

    label: str = Field(
        ...,
        description="Object class label",
        example="person"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence score",
        example=0.92
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
                "bbox": {"x": 120, "y": 50, "width": 180, "height": 320}
            }
        }
```

## Relationships
- **Belongs to** Event (N:1 relationship)

---
