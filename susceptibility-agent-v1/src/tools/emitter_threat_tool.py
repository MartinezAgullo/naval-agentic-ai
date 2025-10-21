"""
Emitter Threat Lookup Tool
Queries threat database to assess risk level of detected electromagnetic emitters.
"""

import os
import json
from typing import Type, Optional, Dict
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)


class EmitterThreatInput(BaseModel):
    """Input schema for emitter threat lookup"""
    emitter_type: str = Field(..., description="Type of emitter (e.g., 'Early Warning Radar', 'Fire Control Radar')")
    context: Optional[str] = Field(None, description="Additional context about the detection")


class EmitterThreatLookupTool(BaseTool):
    """Looks up threat level and recommended response for detected emitters"""
    name: str = "Emitter Threat Lookup Tool"
    description: str = (
        "Queries the threat database to determine the risk level of a detected electromagnetic emitter. "
        "Returns threat score (0-100), category, detection probability, and recommended action. "
        "Input: emitter_type (string - type of emitter), context (optional string - additional info)"
    )
    args_schema: Type[BaseModel] = EmitterThreatInput
    
    threat_database: Optional[Dict] = None
    
    def _load_threat_database(self) -> Dict:
        """Load threat database from JSON file"""
        if self.threat_database is None:
            db_path = Path("config/threat_database.json")
            
            if not db_path.exists():
                logger.warning(f"Threat database not found at {db_path}, using defaults")
                return self._get_default_database()
            
            try:
                with open(db_path, 'r') as f:
                    self.threat_database = json.load(f)
                logger.info(f"Loaded threat database with {len(self.threat_database.get('emitters', {}))} emitter types")
            except Exception as e:
                logger.error(f"Failed to load threat database: {e}")
                return self._get_default_database()
        
        return self.threat_database
    
    def _get_default_database(self) -> Dict:
        """Fallback threat database"""
        return {
            "emitters": {
                "early_warning_radar": {
                    "threat_score": 85,
                    "category": "high",
                    "detection_probability": 0.9,
                    "recommended_action": "Immediate emission control - reduce radar cross-section",
                    "description": "Long-range surveillance radar capable of detecting ships at extended ranges"
                },
                "fire_control_radar": {
                    "threat_score": 95,
                    "category": "critical",
                    "detection_probability": 0.95,
                    "recommended_action": "Emergency stealth mode - prepare defensive countermeasures",
                    "description": "Targeting radar indicating imminent weapon engagement"
                },
                "navigation_radar": {
                    "threat_score": 40,
                    "category": "low",
                    "detection_probability": 0.5,
                    "recommended_action": "Continue monitoring - no immediate action required",
                    "description": "Standard maritime navigation radar"
                },
                "communication": {
                    "threat_score": 30,
                    "category": "low",
                    "detection_probability": 0.3,
                    "recommended_action": "Monitor communications - assess intent",
                    "description": "Radio communication signals"
                },
                "jammer": {
                    "threat_score": 90,
                    "category": "critical",
                    "detection_probability": 0.85,
                    "recommended_action": "Activate counter-jamming - switch to backup frequencies",
                    "description": "Active jamming system targeting our communications/sensors"
                },
                "unknown": {
                    "threat_score": 60,
                    "category": "medium",
                    "detection_probability": 0.6,
                    "recommended_action": "Increase vigilance - gather more intelligence",
                    "description": "Unidentified emitter requiring further analysis"
                }
            }
        }
    
    def _run(self, emitter_type: str, context: Optional[str] = None) -> str:
        try:
            logger.info(f"Looking up threat level for emitter: {emitter_type}")
            
            # Load database
            db = self._load_threat_database()
            emitters = db.get('emitters', {})
            
            # Normalize emitter type for lookup
            normalized_type = emitter_type.lower().replace(' ', '_').replace('-', '_')
            
            # Search for match
            threat_info = None
            for key, value in emitters.items():
                if key in normalized_type or normalized_type in key:
                    threat_info = value
                    break
            
            # Default to unknown if no match
            if not threat_info:
                logger.warning(f"No database entry for '{emitter_type}', using 'unknown' category")
                threat_info = emitters.get('unknown', {
                    "threat_score": 60,
                    "category": "medium",
                    "detection_probability": 0.6,
                    "recommended_action": "Increase vigilance - gather more intelligence",
                    "description": "Unidentified emitter"
                })
            
            logger.debug(f"Threat assessment: {threat_info['category']} (score: {threat_info['threat_score']})")
            
            # Build response
            response = self._format_threat_response(emitter_type, threat_info, context)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in threat lookup: {e}", exc_info=True)
            return f"ERROR: Could not assess threat level - {str(e)}"
    
    def _format_threat_response(self, emitter_type: str, threat_info: Dict, context: Optional[str]) -> str:
        """Format threat assessment response"""
        
        threat_score = threat_info.get('threat_score', 50)
        category = threat_info.get('category', 'medium').upper()
        detection_prob = threat_info.get('detection_probability', 0.5)
        action = threat_info.get('recommended_action', 'Monitor situation')
        description = threat_info.get('description', 'No description available')
        
        # Color-code threat level (for terminal display)
        category_indicator = {
            'LOW': '🟢',
            'MEDIUM': '🟡',
            'HIGH': '🟠',
            'CRITICAL': '🔴'
        }.get(category, '⚪')
        
        response_lines = [
            "=" * 70,
            "EMITTER THREAT ASSESSMENT",
            "=" * 70,
            f"Emitter Type: {emitter_type}",
            f"Description: {description}",
            "",
            f"{category_indicator} THREAT LEVEL: {category}",
            f"Threat Score: {threat_score}/100",
            f"Detection Probability: {detection_prob * 100:.1f}%",
            "",
            "RECOMMENDED ACTION:",
            f"  → {action}",
        ]
        
        if context:
            response_lines.extend([
                "",
                f"Additional Context: {context}"
            ])
        
        response_lines.extend([
            "",
            "TACTICAL IMPLICATIONS:",
            f"  • If detected by this emitter, expect engagement within detection range",
            f"  • Higher threat scores indicate need for immediate electronic countermeasures",
            f"  • Detection probability reflects likelihood of our ship being tracked",
            "=" * 70
        ])
        
        return "\n".join(response_lines)