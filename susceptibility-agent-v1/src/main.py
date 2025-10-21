"""
Main Crew Orchestration for Susceptibility Agent v1
Naval Electronic Warfare Threat Assessment System
"""

import os
import yaml
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# Import tools
from src.tools.multimodal_tools import (
    InputTypeDeterminerTool,
    RadarSignalProcessor,
    EWSignalProcessor
)
from src.tools.emitter_threat_tool import EmitterThreatLookupTool
from src.tools.em_signature_tool import EMSignatureCalculator
from src.tools.comms_reconfig_tool import CommunicationsReconfigTool

# Import logging
from src.utils.logger import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Setup logging
setup_logging(level="DEBUG", log_file="susceptibility_agent.log")
logger = get_logger(__name__)


@CrewBase
class SusceptibilityCrew:
    """Naval Susceptibility Assessment Crew - Electronic Warfare Threat Analysis"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing Susceptibility Crew")
        
        # Initialize tools
        self.signal_tools = self._setup_signal_tools()
        self.threat_tools = self._setup_threat_tools()
        self.response_tools = self._setup_response_tools()
        
        logger.info(f"Tools initialized: {len(self.signal_tools) + len(self.threat_tools) + len(self.response_tools)} total")
    
    def _setup_signal_tools(self):
        """Initialize signal processing tools"""
        logger.debug("Setting up signal processing tools")
        return [
            InputTypeDeterminerTool(),
            RadarSignalProcessor(),
            EWSignalProcessor()
        ]
    
    def _setup_threat_tools(self):
        """Initialize threat assessment tools"""
        logger.debug("Setting up threat assessment tools")
        return [
            EmitterThreatLookupTool(),
            EMSignatureCalculator()
        ]
    
    def _setup_response_tools(self):
        """Initialize response tools"""
        logger.debug("Setting up response tools")
        return [
            CommunicationsReconfigTool()
        ]
    
    @agent
    def signal_intelligence_agent(self) -> Agent:
        """
        Agent to process electromagnetic signal data from sensors.
        Identifies and classifies emitters with technical parameters.
        """
        logger.debug("Creating Signal Intelligence Agent")
        agent_config = dict(self.agents_config['signal_intelligence_agent'])
        
        # Add signal processing tools
        if 'tools' not in agent_config:
            agent_config['tools'] = []
        agent_config['tools'].extend(self.signal_tools)
        
        return Agent(
            config=agent_config,
            verbose=True,
            allow_delegation=False
        )
    
    @agent
    def threat_assessment_agent(self) -> Agent:
        """
        Agent to assess threat level of detected emitters.
        Calculates detection probability and risk scores.
        """
        logger.debug("Creating Threat Assessment Agent")
        agent_config = dict(self.agents_config['threat_assessment_agent'])
        
        # Add threat assessment tools
        if 'tools' not in agent_config:
            agent_config['tools'] = []
        agent_config['tools'].extend(self.threat_tools)
        
        return Agent(
            config=agent_config,
            verbose=True,
            allow_delegation=False
        )
    
    @agent
    def electronic_warfare_advisor_agent(self) -> Agent:
        """
        Agent to recommend EW tactical responses.
        Advises on stealth mode and countermeasures.
        """
        logger.debug("Creating Electronic Warfare Advisor Agent")
        agent_config = dict(self.agents_config['electronic_warfare_advisor_agent'])
        
        return Agent(
            config=agent_config,
            verbose=True,
            allow_delegation=False
        )
    
    @agent
    def communication_coordinator_agent(self) -> Agent:
        """
        Agent to execute communication reconfigurations.
        Manages EMCON and stealth communications.
        """
        logger.debug("Creating Communication Coordinator Agent")
        agent_config = dict(self.agents_config['communication_coordinator_agent'])
        
        # Add communication tools
        if 'tools' not in agent_config:
            agent_config['tools'] = []
        agent_config['tools'].extend(self.response_tools)
        
        return Agent(
            config=agent_config,
            verbose=True,
            allow_delegation=False
        )
    
    @task
    def signal_processing_task(self) -> Task:
        """Task to process incoming signal data"""
        logger.debug("Creating signal processing task")
        return Task(
            config=self.tasks_config['signal_processing_task'],
            agent=self.signal_intelligence_agent()
        )
    
    @task
    def threat_assessment_task(self) -> Task:
        """Task to assess threats from detected emitters"""
        logger.debug("Creating threat assessment task")
        return Task(
            config=self.tasks_config['threat_assessment_task'],
            agent=self.threat_assessment_agent(),
            context=[self.signal_processing_task()]
        )
    
    @task
    def ew_response_task(self) -> Task:
        """Task to recommend EW response"""
        logger.debug("Creating EW response task")
        return Task(
            config=self.tasks_config['ew_response_task'],
            agent=self.electronic_warfare_advisor_agent(),
            context=[self.threat_assessment_task()]
        )
    
    @task
    def communication_reconfig_task(self) -> Task:
        """Task to reconfigure communications if needed"""
        logger.debug("Creating communication reconfiguration task")
        return Task(
            config=self.tasks_config['communication_reconfig_task'],
            agent=self.communication_coordinator_agent(),
            context=[self.threat_assessment_task(), self.ew_response_task()]
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Susceptibility Assessment Crew"""
        try:
            logger.info("Assembling Susceptibility Crew")
            
            crew = Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                verbose=True,
                full_output=True,
                output_folder='output'
            )
            
            logger.info("✓ Susceptibility Crew assembled successfully")
            logger.info(f"  Agents: {len(self.agents)}")
            logger.info(f"  Tasks: {len(self.tasks)}")
            
            return crew
            
        except Exception as e:
            logger.error(f"Failed to create crew: {e}", exc_info=True)
            raise RuntimeError(f"Cannot create crew: {e}")


def run_susceptibility_assessment(signal_input: str, active_systems: list = None) -> Dict[str, Any]:
    """
    Run the susceptibility assessment workflow.
    
    Args:
        signal_input: Signal data (JSON file path, JSON string, or text description)
        active_systems: List of currently active ship systems (optional)
    
    Returns:
        Dictionary with crew results and output files
    """
    logger.info("=" * 70)
    logger.info("STARTING SUSCEPTIBILITY ASSESSMENT")
    logger.info("=" * 70)
    
    try:
        # Initialize crew
        susceptibility_crew = SusceptibilityCrew()
        crew_instance = susceptibility_crew.crew()
        
        # Prepare inputs
        inputs = {
            'signal_input': signal_input
        }
        
        if active_systems:
            inputs['active_systems'] = active_systems
            logger.info(f"Active systems: {active_systems}")
        
        logger.info(f"Processing signal input: {signal_input[:100]}...")
        
        # Execute crew
        logger.info("Executing crew workflow...")
        result = crew_instance.kickoff(inputs=inputs)
        
        logger.info("=" * 70)
        logger.info("SUSCEPTIBILITY ASSESSMENT COMPLETE")
        logger.info("=" * 70)
        
        return {
            'success': True,
            'result': result,
            'output_files': {
                'signal_processing': 'output/signal_processing_task.md',
                'threat_assessment': 'output/threat_assessment_task.md',
                'ew_response': 'output/ew_response_task.md',
                'communication_reconfig': 'output/communication_reconfig_task.md'
            }
        }
        
    except Exception as e:
        logger.error(f"Susceptibility assessment failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def test_with_sample_data():
    """Test the crew with sample signal data"""
    logger.info("Running test with sample data")
    
    # Sample signal data
    sample_signal = {
        "sensor_type": "radar",
        "operational_mode": "normal",
        "detections": [
            {
                "emitter_id": "E-001",
                "emitter_type": "radar",
                "frequency_mhz": 2850.0,
                "power_dbm": 62.5,
                "bearing_degrees": 45.0,
                "range_km": 85.0,
                "classification": "Early Warning Radar"
            },
            {
                "emitter_id": "E-002",
                "emitter_type": "radar",
                "frequency_mhz": 9500.0,
                "power_dbm": 68.0,
                "bearing_degrees": 132.0,
                "range_km": 42.0,
                "classification": "Fire Control Radar"
            }
        ]
    }
    
    import json
    signal_json = json.dumps(sample_signal)
    
    # Active ship systems
    active_systems = [
        "radar",
        "communications",
        "navigation_radar",
        "datalink",
        "iff"
    ]
    
    # Run assessment
    result = run_susceptibility_assessment(
        signal_input=signal_json,
        active_systems=active_systems
    )
    
    if result['success']:
        logger.info("✓ Test completed successfully")
        logger.info(f"Output files generated in: output/")
    else:
        logger.error(f"✗ Test failed: {result.get('error')}")
    
    return result


if __name__ == "__main__":
    logger.info("Susceptibility Agent v1 - Main Module")
    logger.info("Running test scenario...")
    
    # Create output directory
    Path("output").mkdir(exist_ok=True)
    
    # Run test
    test_with_sample_data()