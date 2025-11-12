"""CoreML object detection module for Apple Neural Engine.

This module provides the CoreMLDetector class for loading and managing
CoreML object detection models optimized for Apple Silicon hardware.
"""

import logging
import re
from typing import List, Optional

import coremltools
import cv2
import numpy as np

from core.config import SystemConfig
from core.exceptions import CoreMLLoadError
from core.models import BoundingBox, DetectedObject


class CoreMLDetector:
    """CoreML object detector for Apple Neural Engine.

    Handles loading, validation, and management of CoreML object detection models
    with Apple Neural Engine compatibility checking and performance optimization.
    """

    def __init__(self, config: SystemConfig) -> None:
        """Initialize CoreML detector.

        Args:
            config: System configuration containing model path and settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model: Optional[coremltools.models.MLModel] = None
        self.model_metadata: Optional[dict] = None
        self.is_loaded = False

    def load_model(self, model_path: str) -> None:
        """Load CoreML model from file path.

        Args:
            model_path: Path to .mlmodel file

        Raises:
            CoreMLLoadError: If model loading fails
        """
        try:
            # Load the CoreML model
            self.model = coremltools.models.MLModel(model_path)
            self.is_loaded = True

            # Check Apple Neural Engine compatibility
            compute_unit = getattr(self.model, 'compute_unit', None)
            if compute_unit == 'CPU_AND_GPU':
                self.logger.warning(
                    "Model will run on CPU/GPU (slower), consider using ANE-optimized model"
                )
                ane_compatible = False
            else:
                ane_compatible = True

            # Extract model metadata
            model_name = getattr(self.model, 'model_name', 'Unknown')
            input_description = self.model.input_description
            output_description = self.model.output_description

            # Get input shape if available
            input_shape = None
            if input_description:
                input_names = list(input_description)
                if input_names:
                    first_input = input_description[input_names[0]]
                    if hasattr(first_input, 'type') and hasattr(first_input.type, 'multiArrayType'):
                        shape = first_input.type.multiArrayType.shape
                        if shape:
                            input_shape = tuple(shape)

            # Store metadata
            self.model_metadata = {
                'ane_compatible': ane_compatible,
                'compute_unit': compute_unit,
                'model_name': model_name,
                'input_shape': input_shape,
                'input_description': input_description,
                'output_description': output_description,
            }

            # Log model details
            ane_status = "(ANE-compatible)" if ane_compatible else "(CPU/GPU)"
            self.logger.info(f"✓ CoreML model loaded: {model_name} {ane_status}")

            if input_shape:
                self.logger.info(f"Model input shape: {input_shape}")
            if input_shape:
                input_names = list(input_description)
                self.logger.debug(f"Model inputs: {input_names}")
            if output_description:
                output_names = list(output_description)
                self.logger.debug(f"Model outputs: {output_names}")

            # Model warm-up: Run inference on dummy frame
            import time
            start_time = time.time()

            # Create dummy frame based on input shape
            if input_shape and len(input_shape) >= 3:
                # Assume shape is (channels, height, width) as expected by CoreML
                if len(input_shape) == 3:
                    # Use CHW format
                    dummy_frame = np.random.rand(*input_shape).astype(np.float32)
                else:
                    # Fallback to common shape in CHW format
                    dummy_frame = np.random.rand(3, 416, 416).astype(np.float32)
            else:
                # Default dummy frame for common object detection models (CHW format)
                dummy_frame = np.random.rand(3, 416, 416).astype(np.float32)

            # Run warm-up inference (skip if CoreML framework unavailable)
            try:
                # Test if CoreML framework is available by attempting a minimal prediction
                _ = self.model.predict({
                    'image': dummy_frame,
                    'confidenceThreshold': self.config.min_object_confidence,
                    'iouThreshold': 0.5
                })
                warmup_time = time.time() - start_time
                self.logger.info(f"Model warm-up completed in {warmup_time:.3f}s")
                self.model_metadata['warmup_time'] = warmup_time
                self.model_metadata['coreml_available'] = True
            except Exception as e:
                error_msg = str(e)
                if "CoreML.framework" in error_msg or "Cannot make predictions" in error_msg:
                    self.logger.warning(f"CoreML framework unavailable (expected in non-Apple Silicon environments): {error_msg}")
                    self.model_metadata['coreml_available'] = False
                else:
                    self.logger.warning(f"Model warm-up failed: {error_msg}")
                    self.model_metadata['coreml_available'] = False
                warmup_time = time.time() - start_time
                self.model_metadata['warmup_time'] = warmup_time

        except FileNotFoundError:
            error_msg = f"CoreML model file not found: {model_path}"
            self.logger.error(error_msg)
            raise CoreMLLoadError(error_msg)

        except Exception as e:
            error_msg = f"Failed to load CoreML model from {model_path}: {str(e)}"
            self.logger.error(error_msg)
            raise CoreMLLoadError(error_msg)

    def detect_objects(self, frame: np.ndarray) -> List[DetectedObject]:
        """Run object detection inference on a frame.

        Args:
            frame: Input frame as numpy array (BGR format from OpenCV)

        Returns:
            List of detected objects with labels, confidence scores, and bounding boxes

        Raises:
            RuntimeError: If model is not loaded or CoreML is unavailable
        """
        if not self.is_loaded or self.model is None:
            raise RuntimeError("CoreML model not loaded. Call load_model() first.")

        # Check if CoreML framework is available
        if self.model_metadata and not self.model_metadata.get('coreml_available', True):
            raise RuntimeError("CoreML framework unavailable. System will use motion-only detection fallback.")

        import time
        start_time = time.time()

        try:
            # Preprocess frame
            processed_frame = self._preprocess_frame(frame)

            # Run inference with correct input names
            # YOLOv3-tiny model expects: image, confidenceThreshold, iouThreshold
            raw_outputs = self.model.predict({
                'image': processed_frame,
                'confidenceThreshold': self.config.min_object_confidence,
                'iouThreshold': 0.5  # Standard IoU threshold
            })

            # Post-process results
            detections = self._postprocess_detections(raw_outputs, frame.shape)

            # Apply confidence filtering
            confidence_filtered = [
                det for det in detections
                if det.confidence >= self.config.min_object_confidence
            ]

            # Apply blacklist filtering
            filtered_detections = self._filter_blacklisted_objects(confidence_filtered)

            # Log performance
            inference_time = time.time() - start_time
            self.logger.info(f"Object detection completed in {inference_time:.3f}s "
                           f"({len(filtered_detections)} objects detected)")

            if inference_time > 0.1:  # 100ms threshold
                self.logger.warning(f"Inference time {inference_time:.3f}s exceeds 100ms target")

            return filtered_detections

        except Exception as e:
            error_msg = str(e)
            # Don't log errors for expected CoreML unavailability
            if "CoreML.framework" in error_msg or "Cannot make predictions" in error_msg:
                # This is expected on non-Apple Silicon hardware, let pipeline handle gracefully
                pass
            else:
                self.logger.error(f"Object detection failed: {error_msg}")
            raise

    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for CoreML inference.

        Args:
            frame: Input frame (BGR format)

        Returns:
            Preprocessed frame ready for inference
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Get target input shape from model metadata
        target_shape = self.model_metadata.get('input_shape') if self.model_metadata else None
        if target_shape and len(target_shape) >= 3:
            # Assume shape is (height, width, channels) or (channels, height, width)
            if len(target_shape) == 3:
                target_height, target_width = target_shape[0], target_shape[1]
            else:
                # Handle other formats, default to 416x416
                target_height, target_width = 416, 416
        else:
            # Default to common object detection size
            target_height, target_width = 416, 416

        # Resize frame
        resized_frame = cv2.resize(rgb_frame, (target_width, target_height))

        # Convert to float32 and normalize to [0, 1]
        normalized_frame = resized_frame.astype(np.float32) / 255.0

        # Transpose to CHW format (channels, height, width) as expected by CoreML
        chw_frame = np.transpose(normalized_frame, (2, 0, 1))

        return chw_frame

    def _postprocess_detections(self, raw_outputs: dict, original_frame_shape: tuple) -> List[DetectedObject]:
        """Post-process raw model outputs into DetectedObject instances.

        Args:
            raw_outputs: Raw outputs from CoreML model
            original_frame_shape: Shape of original input frame (height, width, channels)

        Returns:
            List of detected objects
        """
        detections = []

        # Parse model outputs - this is model-specific, using common YOLO-style format
        # Assume outputs contain 'coordinates' and 'confidence' or similar
        # This is a simplified implementation - real models may have different output formats

        # For now, create mock detections for testing
        # In real implementation, this would parse actual model outputs
        if 'coordinates' in raw_outputs and 'confidence' in raw_outputs:
            coords = raw_outputs['coordinates']
            confs = raw_outputs['confidence']

            # Apply Non-Maximum Suppression (simplified)
            # In real implementation, would use proper NMS algorithm
            nms_detections = self._apply_nms(coords, confs)

            for detection in nms_detections:
                # Convert normalized coordinates back to original frame coordinates
                bbox = self._convert_bbox_to_original(
                    detection['bbox'],
                    original_frame_shape
                )

                detected_obj = DetectedObject(
                    label=detection['label'],
                    confidence=detection['confidence'],
                    bbox=bbox
                )
                detections.append(detected_obj)

        return detections

    def _apply_nms(self, coordinates: np.ndarray, confidences: np.ndarray,
                   iou_threshold: float = 0.5) -> List[dict]:
        """Apply Non-Maximum Suppression to filter overlapping detections.

        Args:
            coordinates: Bounding box coordinates [x, y, w, h] format
            confidences: Confidence scores
            iou_threshold: IoU threshold for suppression

        Returns:
            Filtered detections
        """
        # Simplified NMS implementation
        detections = []

        # Sort by confidence (descending)
        indices = np.argsort(confidences)[::-1]

        while len(indices) > 0:
            # Pick the detection with highest confidence
            best_idx = indices[0]
            best_coord = coordinates[best_idx]

            # Convert [x, y, w, h] to [x1, y1, x2, y2] for IoU calculation
            best_bbox = [
                best_coord[0], best_coord[1],  # x1, y1
                best_coord[0] + best_coord[2], best_coord[1] + best_coord[3]  # x2, y2
            ]

            best_detection = {
                'bbox': best_coord,
                'confidence': confidences[best_idx],
                'label': 'person'  # Mock label - would come from model
            }
            detections.append(best_detection)

            # Remove overlapping detections
            remaining_indices = []
            for idx in indices[1:]:
                coord = coordinates[idx]
                # Convert to [x1, y1, x2, y2] format
                bbox = [
                    coord[0], coord[1],  # x1, y1
                    coord[0] + coord[2], coord[1] + coord[3]  # x2, y2
                ]

                # Calculate IoU
                iou = self._calculate_iou(np.array(best_bbox), np.array(bbox))
                if iou < iou_threshold:
                    remaining_indices.append(idx)

            indices = np.array(remaining_indices)

        return detections

    def _calculate_iou(self, bbox1: np.ndarray, bbox2: np.ndarray) -> float:
        """Calculate Intersection over Union of two bounding boxes.

        Args:
            bbox1: First bounding box [x1, y1, x2, y2]
            bbox2: Second bounding box [x1, y1, x2, y2]

        Returns:
            IoU value between 0 and 1
        """
        # Convert to x1, y1, x2, y2 format if needed
        if len(bbox1) == 4:
            x1_1, y1_1, x2_1, y2_1 = bbox1
            x1_2, y1_2, x2_2, y2_2 = bbox2
        else:
            # Handle other formats
            return 0.0

        # Calculate intersection
        x1_inter = max(x1_1, x1_2)
        y1_inter = max(y1_1, y1_2)
        x2_inter = min(x2_1, x2_2)
        y2_inter = min(y2_1, y2_2)

        if x2_inter <= x1_inter or y2_inter <= y1_inter:
            return 0.0

        inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)

        # Calculate union
        bbox1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        bbox2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = bbox1_area + bbox2_area - inter_area

        return inter_area / union_area if union_area > 0 else 0.0

    def _convert_bbox_to_original(self, bbox: np.ndarray, original_shape: tuple) -> BoundingBox:
        """Convert normalized bounding box coordinates to original frame coordinates.

        Args:
            bbox: Normalized bounding box [x, y, width, height] or [x1, y1, x2, y2]
            original_shape: Original frame shape (height, width, channels)

        Returns:
            BoundingBox in original coordinates
        """
        height, width = original_shape[:2]

        if len(bbox) == 4:
            # Assume [x, y, width, height] format (normalized)
            x_norm, y_norm, w_norm, h_norm = bbox

            x = int(x_norm * width)
            y = int(y_norm * height)
            w = int(w_norm * width)
            h = int(h_norm * height)
        else:
            # Handle other formats, default to center of frame
            x, y, w, h = width // 4, height // 4, width // 2, height // 2

        return BoundingBox(x=x, y=y, width=w, height=h)

    def _filter_blacklisted_objects(self, detections: List[DetectedObject]) -> List[DetectedObject]:
        """Filter out detected objects that match the blacklist.

        Args:
            detections: List of detected objects to filter

        Returns:
            Filtered list of detected objects
        """
        if not self.config.blacklist_objects:
            return detections

        filtered_detections = []
        blacklisted_labels = []

        for detection in detections:
            # Case-insensitive exact word matching
            detection_label_lower = detection.label.lower()

            is_blacklisted = False
            for blacklist_item in self.config.blacklist_objects:
                blacklist_item_lower = blacklist_item.lower()

                # Exact word boundary matching (not substring)
                # Use word boundaries to prevent "cat" matching "cattle"
                if re.search(r'\b' + re.escape(blacklist_item_lower) + r'\b', detection_label_lower):
                    is_blacklisted = True
                    blacklisted_labels.append(detection.label)
                    break

            if not is_blacklisted:
                filtered_detections.append(detection)

        # Log filtered objects at DEBUG level
        if blacklisted_labels:
            unique_labels = list(set(blacklisted_labels))
            self.logger.debug(f"Filtered {len(blacklisted_labels)} blacklisted objects: {unique_labels}")

        return filtered_detections
