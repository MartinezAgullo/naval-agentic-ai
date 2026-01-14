"""
Electromagnetic Signature Calculator Tool
Calculates the ship's current EM signature and detectability based on active systems.
"""

from typing import Type, List, Dict, ClassVar
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.logger import get_logger

logger = get_logger(__name__)


class EMSignatureInput(BaseModel):
    """Input schema for EM signature calculation"""
    active_systems: List[str] = Field(
        ..., 
        description="List of currently active emitting systems (e.g., ['radar', 'communications', 'navigation'])"
    )
    power_levels: List[float] = Field(
        default_factory=list,
        description="Optional power levels for each system (in dBm)"
    )


class EMSignatureCalculator(BaseTool):
    """Calculates electromagnetic signature and detectability of own ship"""
    name: str = "EM Signature Calculator"
    description: str = (
        "Calculates the ship's current electromagnetic signature based on active emitting systems. "
        "Provides detectability range estimate and signature strength assessment. "
        "Input: active_systems (list of strings - active emitters), power_levels (optional list of floats)"
    )
    args_schema: Type[BaseModel] = EMSignatureInput
    
    # System power baseline (dBm) - ClassVar to avoid Pydantic validation
    SYSTEM_POWER_BASELINE: ClassVar[Dict[str, float]] = {
        'radar': 60.0,
        'navigation_radar': 50.0,
        'fire_control_radar': 65.0,
        'communications': 45.0,
        'datalink': 48.0,
        'satellite_comms': 55.0,
        'iff': 40.0,
        'tacan': 43.0,
        'ais': 35.0
    }
    
    def _run(self, active_systems: List[str], power_levels: List[float] = None) -> str:
        try:
            logger.info(f"Calculating EM signature for {len(active_systems)} active systems")
            
            if not active_systems:
                logger.warning("No active systems provided")
                return self._format_minimal_signature()
            
            # Use provided power levels or defaults
            if power_levels and len(power_levels) == len(active_systems):
                powers = power_levels
            else:
                powers = [self._get_system_power(sys) for sys in active_systems]
            
            logger.debug(f"System powers: {powers}")
            
            # Calculate aggregate signature
            total_power = sum(powers)
            avg_power = total_power / len(active_systems) if active_systems else 0
            
            # Determine signature strength category
            signature_strength = self._categorize_signature(total_power, len(active_systems))
            
            # Calculate detectability range (simplified model)
            detectability_range = self._calculate_detection_range(total_power, len(active_systems))
            
            # Extract primary frequencies
            primary_frequencies = self._get_primary_frequencies(active_systems)
            
            logger.info(f"EM Signature calculated: {signature_strength} strength, {detectability_range:.1f} km range")
            
            # Build response
            response = self._format_signature_report(
                active_systems=active_systems,
                total_emissions=len(active_systems),
                signature_strength=signature_strength,
                detectability_range=detectability_range,
                primary_frequencies=primary_frequencies,
                avg_power=avg_power
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error calculating EM signature: {e}", exc_info=True)
            return f"ERROR: Could not calculate EM signature - {str(e)}"
    
    def _get_system_power(self, system_name: str) -> float:
        """Get baseline power for a system type"""
        normalized = system_name.lower().replace(' ', '_')
        
        # Try exact match first
        if normalized in self.SYSTEM_POWER_BASELINE:
            return self.SYSTEM_POWER_BASELINE[normalized]
        
        # Try partial match
        for key, power in self.SYSTEM_POWER_BASELINE.items():
            if key in normalized or normalized in key:
                return power
        
        # Default for unknown systems
        logger.warning(f"Unknown system '{system_name}', using default power")
        return 45.0
    
    def _categorize_signature(self, total_power: float, num_systems: int) -> str:
        """Categorize signature strength"""
        if num_systems == 0:
            return "minimal"
        
        avg_power = total_power / num_systems
        
        if avg_power < 40:
            return "minimal"
        elif avg_power < 50:
            return "low"
        elif avg_power < 58:
            return "medium"
        elif avg_power < 65:
            return "high"
        else:
            return "maximum"
    
    def _calculate_detection_range(self, total_power: float, num_systems: int) -> float:
        """
        Simplified detection range calculation.
        Real-world would use radar equation with atmospheric losses.
        """
        if num_systems == 0:
            return 0.0
        
        avg_power = total_power / num_systems
        
        # Simplified model: Range ≈ k * sqrt(Power) * num_systems^0.3
        # This gives ranges roughly 20-200 km based on emissions
        base_range = 10 * (10 ** (avg_power / 40))  # Exponential with power
        system_factor = num_systems ** 0.3  # Multiple emitters increase detectability
        
        detection_range = base_range * system_factor
        
        # Cap at reasonable naval radar ranges
        return min(detection_range, 250.0)
    
    def _get_primary_frequencies(self, active_systems: List[str]) -> List[float]:
        """Get representative frequencies for active systems (MHz)"""
        frequency_map = {
            'radar': 3000.0,
            'navigation_radar': 9400.0,
            'fire_control_radar': 10000.0,
            'communications': 150.0,
            'satellite_comms': 7500.0,
            'datalink': 1200.0,
            'iff': 1030.0,
            'tacan': 1025.0,
            'ais': 162.0
        }
        
        frequencies = []
        for system in active_systems:
            normalized = system.lower().replace(' ', '_')
            for key, freq in frequency_map.items():
                if key in normalized or normalized in key:
                    frequencies.append(freq)
                    break
        
        # Return unique frequencies
        return list(set(frequencies))
    
    def _format_minimal_signature(self) -> str:
        """Format response for minimal emissions"""
        return """
=" * 70
ELECTROMAGNETIC SIGNATURE REPORT
=" * 70

Status: EMISSION CONTROL MODE (EMCON)
Active Systems: 0
Signature Strength: MINIMAL
Detectability Range: <5 km (ambient noise level)

All electromagnetic emissions secured
Ship operating in full stealth mode

=" * 70
"""
    
    def _format_signature_report(
        self,
        active_systems: List[str],
        total_emissions: int,
        signature_strength: str,
        detectability_range: float,
        primary_frequencies: List[float],
        avg_power: float
    ) -> str:
        """Format EM signature report"""
        
        # Threat indicator based on signature
        threat_indicators = {
            'minimal': 'LOW DETECTABILITY',
            'low': 'REDUCED DETECTABILITY', 
            'medium': 'MODERATE DETECTABILITY',
            'high': 'HIGH DETECTABILITY',
            'maximum': 'CRITICAL - HIGHLY DETECTABLE'
        }
        
        threat_msg = threat_indicators.get(signature_strength, 'UNKNOWN')
        
        freq_str = ", ".join([f"{f:.1f} MHz" for f in sorted(primary_frequencies)[:5]])
        
        response_lines = [
            "=" * 70,
            "ELECTROMAGNETIC SIGNATURE REPORT",
            "=" * 70,
            f"Total Active Emitters: {total_emissions}",
            f"Average Power Level: {avg_power:.1f} dBm",
            "",
            f"Signature Strength: {signature_strength.upper()}",
            f"Estimated Detection Range: {detectability_range:.1f} km",
            "",
            f"Status: {threat_msg}",
            "",
            "ACTIVE SYSTEMS:",
            "-" * 70
        ]
        
        for system in active_systems:
            power = self._get_system_power(system)
            response_lines.append(f"  • {system}: {power:.1f} dBm")
        
        response_lines.extend([
            "",
            "PRIMARY EMISSION FREQUENCIES:",
            f"  {freq_str}",
            "",
            "TACTICAL ASSESSMENT:",
            "-" * 70
        ])
        
        if signature_strength in ['high', 'maximum']:
            response_lines.extend([
                "  CAUTION: High electromagnetic signature detected",
                "  → Recommend reducing non-essential emissions",
                "  → Consider emission control (EMCON) procedures",
                f"  → Hostile sensors can detect at ~{detectability_range:.0f} km"
            ])
        elif signature_strength == 'medium':
            response_lines.extend([
                "  NOTICE: Moderate electromagnetic signature",
                "  → Ship is detectable by advanced sensors",
                "  → Consider situational EMCON if threat increases"
            ])
        else:
            response_lines.extend([
                "  GOOD: Low electromagnetic signature",
                "  → Reduced detectability to hostile sensors",
                "  → Maintain current emission profile if tactical situation allows"
            ])
        
        response_lines.extend([
            "",
            "=" * 70
        ])
        
        return "\n".join(response_lines)