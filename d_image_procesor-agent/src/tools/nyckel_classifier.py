"""
Nyckel Drone Classification Tool.
Uses Nyckel's pretrained drone types classifier for accurate drone identification.
"""

import os
import requests
from typing import Dict, Any, Optional
import json
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from src.utils.logger import get_logger

logger = get_logger(__name__)


class NyckelDroneClassificationInput(BaseModel):
    """Input schema for Nyckel drone classification."""
    image_path: str = Field(
        description="Path to image file containing drone"
    )
    bounding_box: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional bounding box to crop drone region: {x, y, width, height}"
    )


class NyckelDroneClassifier(BaseTool):
    """
    Nyckel-based drone type classifier.
    
    Uses Nyckel's commercial pretrained model to classify specific drone types
    including: Agricultural Drone, Delivery Drone, Industrial Drone, Camera Drone,
    FPV Drone, Inspection Drone, Cinematography Drone, Fixed-Wing, Mapping Drone,
    Monitoring Drone, Military Drone.
    
    Docs: https://www.nyckel.com/pretrained-classifiers/drone-types/
    """
    
    name: str = "Nyckel Drone Type Classifier"
    description: str = (
        "Classifies specific drone types using Nyckel's commercial AI model. "
        "Input: Image path and optional bounding box. "
        "Output: Drone type classification (Agricultural, Delivery, Industrial, Camera, "
        "FPV, Inspection, Cinematography, Fixed-Wing, Mapping, Monitoring, Military) "
        "with confidence score. Requires NYCKEL_CLIENT_ID and NYCKEL_CLIENT_SECRET."
    )
    args_schema: type[BaseModel] = NyckelDroneClassificationInput
    
    # Private attributes
    _access_token: Optional[str] = PrivateAttr(default=None)
    _function_id: str = PrivateAttr(default="pj6sxi7xzlj2n85x")  # Nyckel drone-types function
    
    def __init__(self):
        super().__init__()
        self._access_token = None
        self._function_id = "pj6sxi7xzlj2n85x"
    
    def _get_access_token(self) -> str:
        """
        Authenticate with Nyckel and get access token.
        
        Returns:
            Access token string
        """
        if self._access_token:
            return self._access_token
        
        # Get credentials from environment
        client_id = os.getenv("NYCKEL_CLIENT_ID")
        client_secret = os.getenv("NYCKEL_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            raise ValueError(
                "Nyckel credentials not found. Set NYCKEL_CLIENT_ID and "
                "NYCKEL_CLIENT_SECRET in your .env file. "
                "Get credentials from: https://www.nyckel.com/console"
            )
        
        # Request access token
        token_url = "https://www.nyckel.com/connect/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        try:
            response = requests.post(token_url, data=data, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            self._access_token = token_data.get("access_token")
            
            if not self._access_token:
                raise ValueError("No access token in Nyckel response")
            
            logger.info("✓ Nyckel authentication successful")
            return self._access_token
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Nyckel authentication failed: {e}")
            raise RuntimeError(f"Failed to authenticate with Nyckel: {e}")
    
    def _run(self, image_path: str, bounding_box: Optional[Dict] = None) -> str:
        """
        Classify drone type using Nyckel API.
        
        Args:
            image_path: Path to image file
            bounding_box: Optional crop region
            
        Returns:
            JSON string with classification results
        """
        logger.info(f"Classifying drone type with Nyckel: {image_path}")
        
        # Validate image exists
        if not Path(image_path).exists():
            error = f"Image file not found: {image_path}"
            logger.error(error)
            return json.dumps({"error": error})
        
        try:
            # Get access token
            token = self._get_access_token()
            
            # Prepare image data
            # Nyckel accepts image URL or base64 data
            # For local files, we'll use base64
            import base64
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Call Nyckel API
            url = f"https://www.nyckel.com/v1/functions/{self._function_id}/invoke"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Nyckel expects data field with image
            payload = {
                "data": f"data:image/jpeg;base64,{image_data}"
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Parse Nyckel response
            # Format: {"labelName": "Delivery Drone", "labelId": "...", "confidence": 0.76}
            classification = {
                "drone_type": result.get("labelName", "Unknown"),
                "label_id": result.get("labelId"),
                "confidence": result.get("confidence", 0.0),
                "image_path": image_path,
                "classifier": "nyckel",
                "function_id": self._function_id
            }
            
            logger.info(
                f"✓ Nyckel classification: {classification['drone_type']} "
                f"({classification['confidence']:.2%} confidence)"
            )
            
            return json.dumps(classification, indent=2)
        
        except Exception as e:
            logger.error(f"Nyckel classification failed: {e}")
            return json.dumps({
                "error": str(e),
                "classifier": "nyckel",
                "image_path": image_path
            })


# Map Nyckel drone types to tactical categories
NYCKEL_TO_TACTICAL_MAPPING = {
    "Agricultural Drone": {
        "category": "commercial",
        "threat_level": "LOW",
        "size_class": "medium",
        "typical_use": "Agriculture, crop monitoring",
        "countermeasure": "monitoring"
    },
    "Delivery Drone": {
        "category": "commercial",
        "threat_level": "LOW-MEDIUM",
        "size_class": "small-medium",
        "typical_use": "Package delivery",
        "countermeasure": "intercept_inspect"
    },
    "Industrial Drone": {
        "category": "commercial",
        "threat_level": "MEDIUM",
        "size_class": "medium-large",
        "typical_use": "Industrial inspection, heavy lift",
        "countermeasure": "directed_energy"
    },
    "Camera Drone": {
        "category": "commercial",
        "threat_level": "LOW",
        "size_class": "small",
        "typical_use": "Photography, videography",
        "countermeasure": "monitoring"
    },
    "FPV Drone": {
        "category": "recreational",
        "threat_level": "MEDIUM",
        "size_class": "small",
        "typical_use": "Racing, FPV flight (potential ISR)",
        "countermeasure": "jamming"
    },
    "Inspection Drone": {
        "category": "commercial",
        "threat_level": "LOW-MEDIUM",
        "size_class": "small-medium",
        "typical_use": "Infrastructure inspection",
        "countermeasure": "monitoring"
    },
    "Cinematography Drone": {
        "category": "commercial",
        "threat_level": "LOW",
        "size_class": "medium",
        "typical_use": "Professional filming",
        "countermeasure": "monitoring"
    },
    "Fixed-Wing": {
        "category": "tactical",
        "threat_level": "HIGH",
        "size_class": "large",
        "typical_use": "Long-range ISR, strike",
        "countermeasure": "ciws_sam"
    },
    "Mapping Drone": {
        "category": "commercial",
        "threat_level": "MEDIUM",
        "size_class": "medium",
        "typical_use": "Surveying, mapping (potential ISR)",
        "countermeasure": "monitoring"
    },
    "Monitoring Drone": {
        "category": "commercial",
        "threat_level": "MEDIUM",
        "size_class": "small-medium",
        "typical_use": "Security monitoring (ISR capability)",
        "countermeasure": "jamming"
    },
    "Military Drone": {
        "category": "military",
        "threat_level": "CRITICAL",
        "size_class": "varies",
        "typical_use": "Military operations, combat",
        "countermeasure": "immediate_neutralization"
    }
}
