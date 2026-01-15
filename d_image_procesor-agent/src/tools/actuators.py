"""
Actuator tools for executing countermeasures against threats.
Simulates real weapon systems and electronic warfare equipment.
"""

from typing import Dict, Any
import json
import time

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Directed Energy Weapon (DEW) Actuator
# ============================================================================

class DEWActuatorInput(BaseModel):
    """Input schema for DEW actuator."""
    target_id: str = Field(description="ID of target threat")
    power_kw: float = Field(ge=10, le=100, description="DEW power in kilowatts")
    frequency_ghz: float = Field(ge=30, le=100, description="Frequency in GHz")
    beam_width_deg: float = Field(ge=5, le=30, description="Beam width in degrees")
    duration_s: float = Field(ge=0.5, le=10, description="Engagement duration in seconds")


class DEWActuator(BaseTool):
    """
    Directed Energy Weapon actuator.
    
    Simulates high-power microwave or laser system for neutralizing
    small drones and disrupting electronics.
    """
    
    name: str = "Directed Energy Weapon Actuator"
    description: str = (
        "Deploys directed energy weapon (DEW) against drone or small threat. "
        "Input: target ID, power (kW), frequency (GHz), beam width, duration. "
        "Output: Engagement result with effectiveness assessment. "
        "Optimal for small drones and swarms. Minimal collateral damage."
    )
    args_schema: type[BaseModel] = DEWActuatorInput
    
    def _run(
        self,
        target_id: str,
        power_kw: float,
        frequency_ghz: float,
        beam_width_deg: float,
        duration_s: float
    ) -> str:
        """Execute DEW engagement."""
        logger.info(f"DEW engagement: target={target_id}, power={power_kw}kW")
        
        # Simulate engagement
        time.sleep(0.1)  # Simulate processing time
        
        # Calculate effectiveness based on parameters
        effectiveness = self._calculate_dew_effectiveness(
            power_kw, frequency_ghz, beam_width_deg, duration_s
        )
        
        result = {
            "actuator": "directed_energy_weapon",
            "target_id": target_id,
            "status": "SUCCESS" if effectiveness > 70 else "PARTIAL",
            "effectiveness": effectiveness,
            "parameters": {
                "power_kw": power_kw,
                "frequency_ghz": frequency_ghz,
                "beam_width_deg": beam_width_deg,
                "duration_s": duration_s
            },
            "effects": self._describe_dew_effects(effectiveness),
            "execution_time_s": duration_s + 0.5,
            "timestamp": "2025-01-15T10:30:00Z"
        }
        
        logger.info(f"DEW engagement complete: {effectiveness}% effective")
        return json.dumps(result, indent=2)
    
    def _calculate_dew_effectiveness(
        self,
        power_kw: float,
        frequency_ghz: float,
        beam_width_deg: float,
        duration_s: float
    ) -> float:
        """Calculate DEW effectiveness based on parameters."""
        # Base effectiveness from power
        power_factor = min(100, (power_kw / 50) * 70)
        
        # Frequency bonus (95 GHz optimal for drones)
        freq_factor = 100 if 90 <= frequency_ghz <= 100 else 80
        
        # Beam width factor (narrow is better)
        beam_factor = 100 if beam_width_deg <= 15 else 85
        
        # Duration factor
        duration_factor = min(100, (duration_s / 3) * 100)
        
        # Combined effectiveness
        effectiveness = (
            power_factor * 0.4 +
            freq_factor * 0.2 +
            beam_factor * 0.2 +
            duration_factor * 0.2
        )
        
        return round(min(100, effectiveness), 1)
    
    def _describe_dew_effects(self, effectiveness: float) -> str:
        """Describe effects based on effectiveness."""
        if effectiveness >= 90:
            return "Target electronics destroyed. Drone neutralized immediately."
        elif effectiveness >= 70:
            return "Target electronics damaged. Drone lost control and crashed."
        elif effectiveness >= 50:
            return "Target partially affected. Drone experiencing control issues."
        else:
            return "Minimal effect on target. Target remains operational."


# ============================================================================
# CIWS (Close-In Weapon System) Actuator
# ============================================================================

class CIWSActuatorInput(BaseModel):
    """Input schema for CIWS actuator."""
    target_id: str = Field(description="ID of target threat")
    weapon_type: str = Field(
        description="CIWS weapon type: RAM, SeaRAM, Phalanx"
    )
    rounds: int = Field(ge=1, le=10, description="Number of rounds/missiles to fire")
    engagement_range_km: float = Field(ge=0.5, le=10, description="Engagement range")


class CIWSActuator(BaseTool):
    """
    Close-In Weapon System actuator.
    
    Simulates kinetic point defense systems (missiles or guns) for
    engaging larger drones, missiles, and aircraft.
    """
    
    name: str = "CIWS Actuator"
    description: str = (
        "Deploys Close-In Weapon System (CIWS) against threat. "
        "Input: target ID, weapon type (RAM/SeaRAM/Phalanx), rounds, range. "
        "Output: Engagement result with kill probability. "
        "Optimal for large drones, missiles, and aircraft. High effectiveness but consumes ammunition."
    )
    args_schema: type[BaseModel] = CIWSActuatorInput
    
    def _run(
        self,
        target_id: str,
        weapon_type: str,
        rounds: int,
        engagement_range_km: float
    ) -> str:
        """Execute CIWS engagement."""
        logger.info(f"CIWS engagement: target={target_id}, weapon={weapon_type}")
        
        # Simulate engagement time
        time.sleep(0.2)
        
        # Calculate effectiveness
        effectiveness = self._calculate_ciws_effectiveness(
            weapon_type, rounds, engagement_range_km
        )
        
        result = {
            "actuator": "ciws",
            "target_id": target_id,
            "status": "SUCCESS" if effectiveness > 80 else "PARTIAL",
            "effectiveness": effectiveness,
            "parameters": {
                "weapon_type": weapon_type,
                "rounds_fired": rounds,
                "engagement_range_km": engagement_range_km
            },
            "ammunition_expended": rounds,
            "effects": self._describe_ciws_effects(effectiveness, weapon_type),
            "execution_time_s": 2 + (rounds * 0.5),
            "timestamp": "2025-01-15T10:30:00Z"
        }
        
        logger.info(f"CIWS engagement complete: {effectiveness}% effective")
        return json.dumps(result, indent=2)
    
    def _calculate_ciws_effectiveness(
        self,
        weapon_type: str,
        rounds: int,
        range_km: float
    ) -> float:
        """Calculate CIWS effectiveness."""
        # Base effectiveness by weapon type
        weapon_effectiveness = {
            "RAM": 95,
            "SeaRAM": 90,
            "Phalanx": 85
        }
        base = weapon_effectiveness.get(weapon_type, 80)
        
        # Range factor (closer is better)
        range_factor = 100 if range_km < 3 else 85
        
        # Multiple rounds increase probability
        rounds_factor = min(100, 70 + (rounds * 10))
        
        effectiveness = (
            base * 0.5 +
            range_factor * 0.3 +
            rounds_factor * 0.2
        )
        
        return round(min(100, effectiveness), 1)
    
    def _describe_ciws_effects(self, effectiveness: float, weapon: str) -> str:
        """Describe CIWS effects."""
        if effectiveness >= 90:
            return f"{weapon} direct hit. Target destroyed."
        elif effectiveness >= 70:
            return f"{weapon} engaged successfully. Target critically damaged."
        elif effectiveness >= 50:
            return f"{weapon} near miss. Target damaged but operational."
        else:
            return f"{weapon} engagement unsuccessful. Target avoided or survived."


# ============================================================================
# Electronic Jamming Actuator
# ============================================================================

class JammingActuatorInput(BaseModel):
    """Input schema for jamming actuator."""
    target_id: str = Field(description="ID of target threat")
    frequency_mhz: float = Field(ge=400, le=6000, description="Jamming frequency MHz")
    power_dbm: float = Field(ge=20, le=60, description="Jamming power dBm")
    jamming_type: str = Field(
        description="Jamming type: barrage, spot, sweep"
    )
    duration_s: float = Field(ge=1, le=60, description="Jamming duration seconds")


class ElectronicJammingActuator(BaseTool):
    """
    Electronic jamming actuator.
    
    Disrupts drone control links and coordination.
    """
    
    name: str = "Electronic Jamming Actuator"
    description: str = (
        "Deploys electronic jamming against drone C2 links. "
        "Input: target ID, frequency (MHz), power (dBm), jamming type, duration. "
        "Output: Jamming effectiveness and target status. "
        "Disrupts control, navigation, and swarm coordination."
    )
    args_schema: type[BaseModel] = JammingActuatorInput
    
    def _run(
        self,
        target_id: str,
        frequency_mhz: float,
        power_dbm: float,
        jamming_type: str,
        duration_s: float
    ) -> str:
        """Execute jamming."""
        logger.info(f"Jamming: target={target_id}, freq={frequency_mhz}MHz")
        
        time.sleep(0.1)
        
        effectiveness = self._calculate_jamming_effectiveness(
            frequency_mhz, power_dbm, jamming_type
        )
        
        result = {
            "actuator": "electronic_jamming",
            "target_id": target_id,
            "status": "SUCCESS" if effectiveness > 60 else "PARTIAL",
            "effectiveness": effectiveness,
            "parameters": {
                "frequency_mhz": frequency_mhz,
                "power_dbm": power_dbm,
                "jamming_type": jamming_type,
                "duration_s": duration_s
            },
            "effects": self._describe_jamming_effects(effectiveness),
            "execution_time_s": duration_s,
            "timestamp": "2025-01-15T10:30:00Z"
        }
        
        logger.info(f"Jamming complete: {effectiveness}% effective")
        return json.dumps(result, indent=2)
    
    def _calculate_jamming_effectiveness(
        self,
        frequency_mhz: float,
        power_dbm: float,
        jamming_type: str
    ) -> float:
        """Calculate jamming effectiveness."""
        # Common drone frequencies: 900 MHz, 2.4 GHz, 5.8 GHz
        common_freqs = [900, 2400, 5800]
        
        # Frequency match bonus
        freq_match = any(abs(frequency_mhz - f) < 100 for f in common_freqs)
        freq_factor = 100 if freq_match else 70
        
        # Power factor
        power_factor = min(100, (power_dbm / 40) * 100)
        
        # Jamming type factor
        type_effectiveness = {
            "barrage": 90,
            "spot": 95,
            "sweep": 85
        }
        type_factor = type_effectiveness.get(jamming_type, 80)
        
        effectiveness = (
            freq_factor * 0.4 +
            power_factor * 0.3 +
            type_factor * 0.3
        )
        
        return round(min(100, effectiveness), 1)
    
    def _describe_jamming_effects(self, effectiveness: float) -> str:
        """Describe jamming effects."""
        if effectiveness >= 80:
            return "C2 link completely jammed. Drone lost control."
        elif effectiveness >= 60:
            return "C2 link severely degraded. Drone operating erratically."
        elif effectiveness >= 40:
            return "C2 link partially jammed. Drone still functional."
        else:
            return "Minimal jamming effect. Drone maintains control."
