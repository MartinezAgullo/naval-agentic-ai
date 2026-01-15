"""
Data models for threat detection system.
Defines structured data types for visual inputs, radar data, and threat assessments.
"""

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class RadarTrace(BaseModel):
    """
    Radar data trace for target correlation.
    """
    timestamp: datetime
    range_km: float = Field(ge=0, description="Range to target in kilometers")
    bearing_degrees: float = Field(ge=0, le=360, description="Bearing to target")
    elevation_degrees: Optional[float] = Field(default=None, ge=-90, le=90)
    velocity_mps: Optional[float] = Field(default=None, description="Velocity in meters per second")
    rcs_dbsm: Optional[float] = Field(default=None, description="Radar cross-section in dBsm")
    doppler_frequency_hz: Optional[float] = Field(default=None, description="Doppler frequency shift")
    band: Optional[Literal["X", "Ku", "Ka", "L", "S"]] = Field(default=None)


class ThreatImage(BaseModel):
    """
    Visual threat data from camera/sensor.
    """
    image_path: str
    timestamp: datetime
    camera_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude_m: Optional[float] = None


class ThreatInput(BaseModel):
    """
    Complete threat detection input combining visual and radar data.
    """
    images: list[ThreatImage]
    radar_traces: Optional[list[RadarTrace]] = Field(default_factory=list)
    scenario_description: Optional[str] = None


class DetectedObject(BaseModel):
    """
    Object detected by vision system.
    """
    object_type: str = Field(description="Type of detected object (drone, vessel, aircraft, missile)")
    confidence: float = Field(ge=0, le=1, description="Detection confidence score")
    bounding_box: Dict[str, float] = Field(description="x, y, width, height")
    class_id: int
    image_path: str


class ThreatAssessment(BaseModel):
    """
    Threat assessment result from specialist agent.
    """
    threat_id: str
    threat_type: Literal["drone", "missile", "vessel", "aircraft", "unknown"]
    threat_subtype: Optional[str] = None  # e.g., "hexacopter", "cruise_missile"
    threat_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    confidence: float = Field(ge=0, le=1)
    
    # Characteristics
    estimated_range_km: Optional[float] = None
    estimated_velocity_mps: Optional[float] = None
    estimated_size_m: Optional[float] = None
    
    # Swarm assessment (for drones)
    swarm_detected: bool = False
    swarm_size: Optional[int] = None
    
    # Recommended countermeasure
    recommended_countermeasure: str
    countermeasure_parameters: Dict[str, any] = Field(default_factory=dict)
    
    # Supporting data
    radar_correlation: bool = False
    detection_method: str  # "vision", "radar", "fusion"


class CountermeasurePlan(BaseModel):
    """
    Tactical countermeasure plan.
    """
    plan_id: str
    plan_name: str
    target_threats: List[str]  # threat_ids
    countermeasures: List[Dict[str, any]]
    estimated_effectiveness: float = Field(ge=0, le=100)
    execution_time_s: float
    resource_cost: Literal["LOW", "MEDIUM", "HIGH"]
    pros: List[str]
    cons: List[str]


class ExecutionResult(BaseModel):
    """
    Result of countermeasure execution.
    """
    plan_id: str
    success: bool
    executed_countermeasures: List[Dict[str, any]]
    threats_neutralized: List[str]
    threats_remaining: List[str]
    overall_effectiveness: float = Field(ge=0, le=100)
    execution_time_s: float
    final_status: str
