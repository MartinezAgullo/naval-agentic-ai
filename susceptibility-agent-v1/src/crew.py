"""
Susceptibility Crew Definition
Defines the AI agents and tasks for naval electromagnetic threat assessment
"""

from typing import List
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
from src.utils.logger import get_logger

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
    
    def _setup_signal_tools(self) -> List:
        """Initialize signal processing tools"""
        logger.debug("Setting up signal processing tools")
        return [
            InputTypeDeterminerTool(),
            RadarSignalProcessor(),
            EWSignalProcessor()
        ]
    
    def _setup_threat_tools(self) -> List:
        """Initialize threat assessment tools"""
        logger.debug("Setting up threat assessment tools")
        return [
            EmitterThreatLookupTool(),
            EMSignatureCalculator()
        ]
    
    def _setup_response_tools(self) -> List:
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
            
            crew_instance = Crew(
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
            
            return crew_instance
            
        except Exception as e:
            logger.error(f"Failed to create crew: {e}", exc_info=True)
            raise RuntimeError(f"Cannot create crew: {e}")