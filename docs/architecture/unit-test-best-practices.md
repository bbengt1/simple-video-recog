# Unit Test Best Practices

**1. Use pytest fixtures for common test data:**

```python
# tests/conftest.py
"""Shared pytest fixtures for all tests."""
import pytest
from datetime import datetime
from core.models import Event, DetectedObject, BoundingBox


@pytest.fixture
def sample_event():
    """Create sample Event object for testing."""
    return Event(
        event_id="evt_test_12345",
        timestamp=datetime.utcnow(),
        camera_id="test_camera",
        motion_confidence=0.87,
        detected_objects=[
            DetectedObject(
                label="person",
                confidence=0.92,
                bbox=BoundingBox(x=120, y=50, width=180, height=320)
            )
        ],
        llm_description="Test person approaching",
        image_path="data/test/evt_test_12345.jpg",
        json_log_path="data/test/events.json"
    )


@pytest.fixture
def mock_frame():
    """Create mock OpenCV frame (numpy array)."""
    import numpy as np
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def temp_database(tmp_path):
    """Create temporary SQLite database for testing."""
    from core.database import DatabaseManager
    db_path = tmp_path / "test.db"
    db = DatabaseManager(str(db_path))
    db.init_database()
    return db
```

**2. Mock external dependencies:**

```python
# tests/unit/test_event_manager.py
"""Unit tests for EventManager."""
import pytest
from unittest.mock import Mock, patch
from core.event_manager import EventManager


def test_create_event_success(sample_event, mock_frame):
    """Test event creation with valid inputs."""
    # Mock dependencies
    mock_db = Mock()
    mock_json_logger = Mock()
    mock_txt_logger = Mock()

    event_manager = EventManager(
        db_manager=mock_db,
        json_logger=mock_json_logger,
        txt_logger=mock_txt_logger
    )

    # Create event
    event = event_manager.create_event(
        frame=mock_frame,
        objects=sample_event.detected_objects,
        description=sample_event.llm_description,
        motion_confidence=0.87
    )

    # Verify event created
    assert event is not None
    assert event.llm_description == sample_event.llm_description

    # Verify persistence methods called
    mock_db.insert_event.assert_called_once()
    mock_json_logger.log_event.assert_called_once()
    mock_txt_logger.log_event.assert_called_once()


def test_event_suppression(sample_event):
    """Test event de-duplication logic."""
    event_manager = EventManager(
        db_manager=Mock(),
        json_logger=Mock(),
        txt_logger=Mock()
    )

    # Create first event
    event1 = event_manager.create_event(
        frame=Mock(),
        objects=sample_event.detected_objects,
        description="Person detected",
        motion_confidence=0.87
    )
    assert event1 is not None

    # Create duplicate event (same objects)
    event2 = event_manager.create_event(
        frame=Mock(),
        objects=sample_event.detected_objects,
        description="Person detected again",
        motion_confidence=0.88
    )
    assert event2 is None  # Suppressed due to overlap
```

**3. Test edge cases and error conditions:**

```python
# tests/unit/test_storage_monitor.py
"""Unit tests for StorageMonitor."""
import pytest
from core.storage_monitor import StorageMonitor


def test_storage_within_limit(tmp_path):
    """Test storage check when under limit."""
    monitor = StorageMonitor(max_storage_gb=1.0)
    stats = monitor.check_usage()

    assert stats.is_over_limit is False
    assert 0 <= stats.percentage_used <= 100


def test_storage_over_limit(tmp_path):
    """Test storage check when over limit."""
    # Create large file to exceed limit
    large_file = tmp_path / "data/events/large.dat"
    large_file.parent.mkdir(parents=True, exist_ok=True)

    # Write 1.1GB file (exceeds 1GB limit)
    with open(large_file, 'wb') as f:
        f.write(b'0' * (1100 * 1024 * 1024))

    monitor = StorageMonitor(max_storage_gb=1.0, data_dir=str(tmp_path / "data"))
    stats = monitor.check_usage()

    assert stats.is_over_limit is True
    assert stats.percentage_used > 100


def test_storage_calculation_empty_directory(tmp_path):
    """Test storage calculation with empty directory."""
    monitor = StorageMonitor(max_storage_gb=1.0, data_dir=str(tmp_path))
    stats = monitor.check_usage()

    assert stats.total_bytes == 0
    assert stats.percentage_used == 0.0
```

**4. Parametrize tests for multiple scenarios:**

```python
# tests/unit/test_motion_detector.py
"""Unit tests for MotionDetector."""
import pytest
import numpy as np
from core.motion_detector import MotionDetector


@pytest.mark.parametrize("threshold,expected_motion", [
    (0.1, True),   # Low threshold, should detect motion
    (0.5, True),   # Medium threshold, should detect motion
    (0.9, False),  # High threshold, might not detect motion
])
def test_motion_detection_thresholds(threshold, expected_motion, mock_frame):
    """Test motion detection with different thresholds."""
    detector = MotionDetector(motion_threshold=threshold)

    # Build background model
    for _ in range(100):
        detector.detect_motion(mock_frame)

    # Create frame with slight change
    changed_frame = mock_frame.copy()
    changed_frame[100:200, 100:200] = 255  # White square

    has_motion, confidence = detector.detect_motion(changed_frame)

    assert isinstance(has_motion, bool)
    assert 0.0 <= confidence <= 1.0
```

---
