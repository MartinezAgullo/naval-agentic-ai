"""
Radar-Vision Fusion Tool.
Combines visual detections with radar traces to improve threat assessment.
"""

from typing import List, Dict, Any
import json
import math

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.logger import get_logger

logger = get_logger(__name__)


class RadarFusionInput(BaseModel):
    """Input schema for radar fusion tool."""
    visual_detections: str = Field(
        description="JSON string of visual detections from YOLO tool"
    )
    radar_data: str = Field(
        description="JSON string of radar traces with range, bearing, velocity, Doppler"
    )
    fusion_threshold_m: float = Field(
        default=100.0,
        description="Maximum distance (meters) for correlating radar and vision"
    )


class RadarFusionTool(BaseTool):
    """
    Tool for fusing visual and radar data to improve threat assessment.
    
    Correlates visual detections with radar traces using spatial proximity
    and validates detections with Doppler data (e.g., propeller signatures).
    """
    
    name: str = "Radar Vision Fusion"
    description: str = (
        "Fuses visual detections with radar traces to validate and enhance threat assessment. "
        "Input: Visual detections JSON, radar traces JSON, fusion threshold. "
        "Output: Fused detections with correlated radar data including Doppler signatures. "
        "Helps identify drone propeller signatures (Ku-band Doppler) and validate targets."
    )
    args_schema: type[BaseModel] = RadarFusionInput
    
    def _run(
        self,
        visual_detections: str,
        radar_data: str,
        fusion_threshold_m: float = 100.0
    ) -> str:
        """
        Fuse visual and radar data.
        
        Args:
            visual_detections: JSON string of YOLO detections
            radar_data: JSON string of radar traces
            fusion_threshold_m: Correlation threshold in meters
            
        Returns:
            JSON string with fused threat assessments
        """
        logger.info("Starting radar-vision fusion")
        
        try:
            detections = json.loads(visual_detections)
            radar_traces = json.loads(radar_data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return json.dumps({"error": "Invalid JSON input"})
        
        # Extract detection list
        detection_list = detections.get("detections", [])
        if not detection_list:
            logger.warning("No visual detections provided")
            return json.dumps({"fused_threats": [], "total_fused": 0})
        
        # Extract radar traces list
        trace_list = radar_traces.get("traces", [])
        if not trace_list:
            logger.warning("No radar traces provided, returning visual-only detections")
            return self._visual_only_output(detection_list)
        
        # Perform fusion
        fused_threats = self._correlate_detections(
            detection_list,
            trace_list,
            fusion_threshold_m
        )
        
        result = {
            "fused_threats": fused_threats,
            "total_fused": len(fused_threats),
            "fusion_method": "spatial_proximity_doppler"
        }
        
        logger.info(f"Fusion complete: {len(fused_threats)} threats correlated")
        return json.dumps(result, indent=2)
    
    def _correlate_detections(
        self,
        detections: List[Dict],
        radar_traces: List[Dict],
        threshold_m: float
    ) -> List[Dict]:
        """
        Correlate visual detections with radar traces.
        
        Uses spatial proximity and, when available, Doppler signatures to validate
        detections and identify threat characteristics.
        """
        fused = []
        used_traces = set()
        
        for detection in detections:
            if "error" in detection:
                continue
            
            best_match = None
            best_distance = float('inf')
            
            # Find closest radar trace
            for idx, trace in enumerate(radar_traces):
                if idx in used_traces:
                    continue
                
                # Calculate spatial proximity (simplified - assumes bearing alignment)
                # In production, use proper geospatial calculations
                distance = abs(trace.get("range_km", 999) * 1000 - threshold_m)
                
                if distance < best_distance and distance < threshold_m:
                    best_distance = distance
                    best_match = (idx, trace)
            
            if best_match:
                trace_idx, trace = best_match
                used_traces.add(trace_idx)
                
                # Fuse detection with radar trace
                fused_threat = {
                    **detection,
                    "radar_correlation": True,
                    "range_km": trace.get("range_km"),
                    "bearing_degrees": trace.get("bearing_degrees"),
                    "velocity_mps": trace.get("velocity_mps"),
                    "rcs_dbsm": trace.get("rcs_dbsm"),
                    "doppler_hz": trace.get("doppler_frequency_hz"),
                    "radar_band": trace.get("band"),
                    "fusion_confidence": self._calculate_fusion_confidence(
                        detection,
                        trace
                    )
                }
                
                # Enhanced assessment based on Doppler
                fused_threat = self._enhance_with_doppler(fused_threat)
                
            else:
                # No radar correlation
                fused_threat = {
                    **detection,
                    "radar_correlation": False,
                    "fusion_confidence": detection.get("confidence", 0.5)
                }
            
            fused.append(fused_threat)
        
        return fused
    
    def _calculate_fusion_confidence(
        self,
        detection: Dict,
        trace: Dict
    ) -> float:
        """
        Calculate fusion confidence based on visual and radar agreement.
        """
        visual_conf = detection.get("confidence", 0.5)
        
        # Bonus for radar correlation
        radar_bonus = 0.2
        
        # Bonus for Doppler signature (indicates moving propellers/rotors)
        doppler = trace.get("doppler_frequency_hz")
        doppler_bonus = 0.15 if doppler and abs(doppler) > 10 else 0
        
        fusion_conf = min(1.0, visual_conf + radar_bonus + doppler_bonus)
        return round(fusion_conf, 3)
    
    def _enhance_with_doppler(self, threat: Dict) -> Dict:
        """
        Enhance threat assessment using Doppler radar data.
        
        Ku-band Doppler can detect micro-Doppler signatures from rotating
        propellers, which is a strong indicator of drones (especially multi-rotors).
        """
        doppler = threat.get("doppler_hz")
        band = threat.get("radar_band")
        object_type = threat.get("object_type")
        
        if not doppler or not band:
            return threat
        
        # Ku-band (12-18 GHz) is good for detecting propeller micro-Doppler
        if band == "Ku" and abs(doppler) > 20:
            # Strong Doppler signature suggests rotating blades
            threat["doppler_signature"] = "strong_rotational"
            
            if object_type == "drone" or object_type == "aircraft":
                threat["enhanced_assessment"] = (
                    "Ku-band Doppler signature confirms rotating propellers/rotors. "
                    "Consistent with multi-rotor drone (quadcopter/hexacopter)."
                )
                
                # Estimate rotor count from Doppler modulation (simplified)
                if abs(doppler) > 50:
                    threat["estimated_rotor_count"] = "6-8 (hexacopter/octocopter)"
                elif abs(doppler) > 30:
                    threat["estimated_rotor_count"] = "4-6 (quadcopter/hexacopter)"
                else:
                    threat["estimated_rotor_count"] = "2-4 (small multirotor)"
        
        return threat
    
    def _visual_only_output(self, detections: List[Dict]) -> str:
        """
        Return visual-only detections when no radar data available.
        """
        fused = []
        for detection in detections:
            if "error" not in detection:
                fused.append({
                    **detection,
                    "radar_correlation": False,
                    "fusion_confidence": detection.get("confidence", 0.5)
                })
        
        result = {
            "fused_threats": fused,
            "total_fused": len(fused),
            "fusion_method": "visual_only"
        }
        
        return json.dumps(result, indent=2)
