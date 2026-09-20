"""
AquaGuard AI - YOLOv8 Person Detector
Wraps Ultralytics YOLOv8 for person detection (class 0).
"""
from typing import List
from loguru import logger

class PersonDetection:
    def __init__(self, bbox_x1: float, bbox_y1: float, bbox_x2: float, bbox_y2: float, confidence: float, class_id: int = 0):
        self.bbox_x1 = bbox_x1
        self.bbox_y1 = bbox_y1
        self.bbox_x2 = bbox_x2
        self.bbox_y2 = bbox_y2
        self.confidence = confidence
        self.class_id = class_id

    @property
    def box(self):
        return [self.bbox_x1, self.bbox_y1, self.bbox_x2, self.bbox_y2]

class YOLODetector:
    def __init__(self, model_path: str = "yolov8n.pt", conf_threshold: float = 0.35, device: str = "cpu"):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.device = device
        self._model = None
        self._is_loaded = False
        self.load_model()

    def load_model(self) -> bool:
        try:
            from ultralytics import YOLO
            self._model = YOLO(self.model_path)
            self._model.to(self.device)
            self._is_loaded = True
            logger.info(f"YOLO detector loaded: {self.model_path}")
            return True
        except Exception as e:
            logger.warning(f"Could not load YOLO model ({e}), using fallback detector mode.")
            self._is_loaded = False
            return False

    def detect(self, frame) -> List[PersonDetection]:
        if not self._is_loaded or self._model is None:
            return []
        try:
            results = self._model(frame, conf=self.conf_threshold, classes=[0], verbose=False)
            detections = []
            if results and results[0].boxes is not None:
                for box in results[0].boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    detections.append(PersonDetection(x1, y1, x2, y2, conf, cls_id))
            return detections
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []