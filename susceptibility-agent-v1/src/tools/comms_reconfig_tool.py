"""
Communications Reconfiguration Tool
Simulates communication system reconfiguration for stealth mode operations.

Does:
    1 - If stealth_mode=False → Returns "normal mode" message
    2 - If stealth_mode=True → Calls _perform_reconfiguration()
    3 - Returns formatted report
"""

from typing import Type, List, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.logger import get_logger

logger = get_logger(__name__)


class CommsReconfigInput(BaseModel):
    """Input schema for communications reconfiguration"""
    stealth_mode: bool = Field(
        ...,
        description="Whether to activate stealth communications mode"
    )
    priority_channels: Optional[List[str]] = Field(
        default=None,
        description="List of priority communication channels to maintain"
    )
    threat_level: Optional[str] = Field(
        default="medium",
        description="Current threat level (low/medium/high/critical)"
    )


class CommunicationsReconfigTool(BaseTool):
    """Reconfigures communication systems for stealth operations"""
    name: str = "Communications Reconfiguration Tool"
    description: str = (
        "Simulates reconfiguration of ship's communication systems for stealth mode. "
        "Switches frequencies, enables encryption, reduces power, and activates frequency hopping. "
        "Input: stealth_mode (bool), priority_channels (optional list), threat_level (optional string)"
    )
    args_schema: Type[BaseModel] = CommsReconfigInput
    
    # Standard communication channels
    STANDARD_CHANNELS = [
        "VHF_Primary",
        "UHF_Tactical",
        "HF_LongRange",
        "SATCOM_Primary",
        "Datalink_Command",
        "ESM_Coordination"
    ]
    
    # Frequency bands (MHz)
    FREQUENCY_BANDS = {
        "VHF_Primary": (30, 88),
        "UHF_Tactical": (225, 400),
        "HF_LongRange": (2, 30),
        "SATCOM_Primary": (7500, 8500),
        "Datalink_Command": (960, 1215),
        "ESM_Coordination": (225, 400)
    }
    
    def _run(
        self, 
        stealth_mode: bool, 
        priority_channels: Optional[List[str]] = None,
        threat_level: Optional[str] = "medium"
    ) -> str:
        try:
            logger.info(f"Communications reconfiguration requested - Stealth: {stealth_mode}, Threat: {threat_level}")
            
            if not stealth_mode:
                logger.info("Normal communications mode maintained")
                return self._format_normal_mode()
            
            # Determine priority channels
            if priority_channels is None:
                priority_channels = self._get_default_priority_channels(threat_level)
            
            logger.debug(f"Priority channels: {priority_channels}")
            
            # Perform reconfiguration
            reconfig_result = self._perform_reconfiguration(
                priority_channels=priority_channels,
                threat_level=threat_level
            )
            
            logger.info(f"Reconfiguration complete: {len(reconfig_result['channels_changed'])} channels modified")
            
            # Build response
            response = self._format_stealth_config(reconfig_result, threat_level)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in communications reconfiguration: {e}", exc_info=True)
            return f"ERROR: Communications reconfiguration failed - {str(e)}"
    
    def _get_default_priority_channels(self, threat_level: str) -> List[str]:
        """Determine default priority channels based on threat level"""
        if threat_level == "critical":
            # Minimal comms - only essential command channels
            return ["SATCOM_Primary", "Datalink_Command"]
        elif threat_level == "high":
            # Reduced comms - tactical essentials
            return ["UHF_Tactical", "SATCOM_Primary", "Datalink_Command"]
        elif threat_level == "medium":
            # Balanced comms
            return ["VHF_Primary", "UHF_Tactical", "SATCOM_Primary", "Datalink_Command"]
        else:  # low
            # Full comms with stealth enhancements
            return self.STANDARD_CHANNELS
    
    def _perform_reconfiguration(
        self, 
        priority_channels: List[str],
        threat_level: str
    ) -> dict:
        """Simulate communication system reconfiguration"""
        
        # Determine configuration based on threat level
        if threat_level == "critical":
            freq_hop = True
            power_reduced = True
            encryption = "maximum"
        elif threat_level == "high":
            freq_hop = True
            power_reduced = True
            encryption = "enhanced"
        elif threat_level == "medium":
            freq_hop = True
            power_reduced = False
            encryption = "enhanced"
        else:  # low
            freq_hop = False
            power_reduced = False
            encryption = "basic"
        
        # Channels that will be modified
        channels_changed = []
        for channel in priority_channels:
            if channel in self.STANDARD_CHANNELS:
                channels_changed.append(channel)
        
        return {
            "channels_changed": channels_changed,
            "frequency_hop_enabled": freq_hop,
            "power_reduced": power_reduced,
            "encryption_level": encryption,
            "stealth_mode_active": True
        }
    
    def _format_normal_mode(self) -> str:
        """Format response for normal communications mode"""
        return """
        =" * 70
        COMMUNICATIONS STATUS: NORMAL MODE
        =" * 70
        
        All communication channels operating in standard configuration.
        No emission control restrictions active.
        
        Active Channels: 6/6
        Encryption: Basic
        Power Levels: Normal
        Frequency Hopping: Disabled
        
        ⚠️ NOTE: Standard emissions profile maintained
        =" * 70
        """
    
    def _format_stealth_config(self, config: dict, threat_level: str) -> str:
        """Format stealth mode reconfiguration report"""
        
        channels = config['channels_changed']
        freq_hop = config['frequency_hop_enabled']
        power_red = config['power_reduced']
        encryption = config['encryption_level']
        
        # Threat level indicator
        threat_indicators = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }
        threat_icon = threat_indicators.get(threat_level, '⚪')
        
        response_lines = [
            "=" * 70,
            "COMMUNICATIONS RECONFIGURATION - STEALTH MODE ACTIVE",
            "=" * 70,
            f"Threat Level: {threat_icon} {threat_level.upper()}",
            f"Channels Reconfigured: {len(channels)}/{len(self.STANDARD_CHANNELS)}",
            "",
            "STEALTH CONFIGURATION:",
            "-" * 70,
            f"  • Frequency Hopping: {'ENABLED' if freq_hop else 'DISABLED'}",
            f"  • Power Reduction: {'ACTIVE' if power_red else 'NORMAL'}",
            f"  • Encryption Level: {encryption.upper()}",
            f"  • Emission Control: ACTIVE",
            "",
            "ACTIVE PRIORITY CHANNELS:",
            "-" * 70
        ]
        
        for channel in channels:
            freq_range = self.FREQUENCY_BANDS.get(channel, (0, 0))
            response_lines.append(f"  ✓ {channel}: {freq_range[0]}-{freq_range[1]} MHz")
        
        # Add tactical implications
        response_lines.extend([
            "",
            "TACTICAL IMPLICATIONS:",
            "-" * 70
        ])
        
        if threat_level == "critical":
            response_lines.extend([
                "  🔴 CRITICAL THREAT - Minimal emissions authorized",
                "  → Only essential command/control channels active",
                "  → All non-priority communications SECURED",
                "  → Maximum encryption and frequency agility employed",
                "  → Detection risk MINIMIZED"
            ])
        elif threat_level == "high":
            response_lines.extend([
                "  🟠 HIGH THREAT - Tactical communications maintained",
                "  → Non-essential channels SECURED",
                "  → Frequency hopping active on all channels",
                "  → Reduced power to minimize detection",
                "  → Enhanced encryption deployed"
            ])
        elif threat_level == "medium":
            response_lines.extend([
                "  🟡 MEDIUM THREAT - Balanced stealth configuration",
                "  → Primary channels remain operational",
                "  → Frequency hopping provides protection",
                "  → Normal power levels maintained",
                "  → Enhanced encryption active"
            ])
        else:
            response_lines.extend([
                "  🟢 LOW THREAT - Stealth enhancements applied",
                "  → All standard channels operational",
                "  → Basic stealth measures implemented",
                "  → Communications capability maintained"
            ])
        
        response_lines.extend([
            "",
            "OPERATIONAL NOTES:",
            "  • Coordinate frequency changes with task force",
            "  • Monitor for communication degradation",
            "  • Prepare backup channels if primary compromised",
            "  • Update crypto keys per EMCON procedures",
            "",
            "=" * 70,
            "STATUS: Communications reconfigured for stealth operations"
        ])
        
        return "\n".join(response_lines)