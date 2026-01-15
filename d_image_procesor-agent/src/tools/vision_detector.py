"""
Vision-based threat detection using YOLOv8.
Detects objects in images and classifies potential threats.
"""

from typing import Any, Dict, List
from pathlib import Path
import json

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from src.utils.logger import get_logger

logger = get_logger(__name__)


class YOLODetectionInput(BaseModel):
    """Input schema for YOLO detection tool."""
    image_paths: list[str] = Field(
        description="List of image file paths to analyze for threats"
    )
    confidence_threshold: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for detections"
    )


class YOLODetectionTool(BaseTool):
    """
    Tool for detecting objects in images using YOLOv8.
    
    This tool processes visual inputs from ship cameras to detect potential threats
    including drones, vessels, aircraft, and missiles.
    """
    
    name: str = "YOLO Threat Detector"
    description: str = (
        "Analyzes images to detect potential threats using computer vision. "
        "Input: List of image paths and confidence threshold. "
        "Output: Detected objects with type, confidence, and bounding boxes. "
        "Detects: drones, aircraft, vessels, missiles, and other objects."
    )
    args_schema: type[BaseModel] = YOLODetectionInput
    
    # Use PrivateAttr for model instance (not a Pydantic field)
    _model: Any = PrivateAttr(default=None)
    
    def __init__(self):
        super().__init__()
        self._model = None
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """
        Initialize YOLOv8 model (lazy loading).
        In production, this would load a fine-tuned model for naval threats.
        """
        try:
            from ultralytics import YOLO
            
            # Use pretrained COCO model for POC
            # In production: Use fine-tuned model for drones, missiles, vessels
            self._model = YOLO('yolov8n.pt')  # Nano model for speed
            logger.info("YOLOv8 model initialized successfully")
            
        except ImportError:
            logger.warning("ultralytics not installed, using mock detection")
            self._model = None
        except Exception as e:
            logger.error(f"Failed to initialize YOLO model: {e}")
            self._model = None
    
    def _run(self, image_paths: List[str], confidence_threshold: float = 0.35) -> str:
        """
        Run YOLO detection on provided images.
        
        Args:
            image_paths: List of paths to images
            confidence_threshold: Minimum confidence for detections
            
        Returns:
            JSON string with detection results
        """
        logger.info(f"Running YOLO detection on {len(image_paths)} image(s)")
        
        all_detections = []
        
        for image_path in image_paths:
            try:
                detections = self._detect_in_image(image_path, confidence_threshold)
                all_detections.extend(detections)
            except Exception as e:
                logger.error(f"Detection failed for {image_path}: {e}")
                all_detections.append({
                    "error": str(e),
                    "image_path": image_path
                })
        
        result = {
            "total_detections": len([d for d in all_detections if "error" not in d]),
            "images_processed": len(image_paths),
            "detections": all_detections
        }
        
        logger.info(f"Detection complete: {result['total_detections']} objects detected")
        return json.dumps(result, indent=2)
    
    def _detect_in_image(self, image_path: str, confidence_threshold: float) -> list[Dict]:
        """
        Detect objects in a single image.
        
        Args:
            image_path: Path to image file
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List of detection dictionaries
        """
        if not Path(image_path).exists():
            logger.error(f"Image not found: {image_path}")
            return [{"error": "Image file not found", "image_path": image_path}]
        
        if self._model is None:
            # Mock detection for testing without YOLO
            return self._mock_detection(image_path)
        
        # Run YOLO inference
        results = self._model(image_path, conf=confidence_threshold, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                detection = {
                    "image_path": image_path,
                    "object_type": self._map_class_to_threat(int(box.cls[0])),
                    "class_id": int(box.cls[0]),
                    "class_name": result.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "bounding_box": {
                        "x": float(box.xywh[0][0]),
                        "y": float(box.xywh[0][1]),
                        "width": float(box.xywh[0][2]),
                        "height": float(box.xywh[0][3])
                    }
                }
                detections.append(detection)
        
        return detections
    
    def _map_class_to_threat(self, class_id: int) -> str:
        """
        Map YOLO COCO class to threat category.
        
        In production, this would use a fine-tuned model with naval threat classes.
        For POC, we map relevant COCO classes to threat types.
        """
        # COCO class mappings (approximations for POC)
        threat_mapping = {
            0: "unknown",     # person (ignore)
            2: "vehicle",     # car
            3: "vehicle",     # motorcycle
            4: "aircraft",    # airplane
            5: "vessel",      # bus (proxy for ship)
            6: "vehicle",     # train
            7: "vessel",      # truck (proxy for ship)
            8: "vessel",      # boat
            14: "drone",      # bird (proxy for drone in POC)
            15: "animal",     # cat (ignore)
            16: "animal",     # dog (ignore)
            33: "drone",      # kite (flying object - treat as drone)
        }
        
        return threat_mapping.get(class_id, "unknown")
    
    def _mock_detection(self, image_path: str) -> list[Dict]:
        """
        Mock detection for testing without YOLO installed.
        """
        logger.warning(f"Using mock detection for {image_path}")
        
        # Return plausible mock detections based on filename
        filename = Path(image_path).stem.lower()
        
        if "drone" in filename or "uav" in filename:
            return [{
                "image_path": image_path,
                "object_type": "drone",
                "class_id": 999,
                "class_name": "drone_mock",
                "confidence": 0.87,
                "bounding_box": {"x": 320, "y": 240, "width": 150, "height": 120}
            }]
        elif "ship" in filename or "vessel" in filename:
            return [{
                "image_path": image_path,
                "object_type": "vessel",
                "class_id": 998,
                "class_name": "vessel_mock",
                "confidence": 0.92,
                "bounding_box": {"x": 400, "y": 300, "width": 250, "height": 180}
            }]
        elif "missile" in filename:
            return [{
                "image_path": image_path,
                "object_type": "missile",
                "class_id": 997,
                "class_name": "missile_mock",
                "confidence": 0.78,
                "bounding_box": {"x": 350, "y": 200, "width": 80, "height": 40}
            }]
        else:
            return [{
                "image_path": image_path,
                "object_type": "unknown",
                "class_id": 0,
                "class_name": "unknown_object",
                "confidence": 0.45,
                "bounding_box": {"x": 300, "y": 250, "width": 100, "height": 100}
            }]
