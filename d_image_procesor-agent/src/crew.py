"""
Threat Detection Crew Definition
Defines the AI agents and tasks for naval visual threat detection and response
"""

from pathlib import Path
from typing import List
import yaml

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# Import tools
from src.tools.vision_detector import YOLODetectionTool
from src.tools.radar_fusion import RadarFusionTool
from src.tools.drone_analyzer import DroneAnalysisTool
from src.tools.actuators import (
    DEWActuator,
    CIWSActuator,
    ElectronicJammingActuator
)

# Import logging
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Get absolute path to config directory
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = PROJECT_ROOT / 'config'

logger.debug(f"Config directory resolved to: {CONFIG_DIR}")


@CrewBase
class ThreatDetectionCrew:
    """Naval Threat Detection and Response Crew"""
    
    # Paths to config files
    agents_config = str((CONFIG_DIR / "agents.yaml").resolve())
    tasks_config = str((CONFIG_DIR / "tasks.yaml").resolve())
    
    def __init__(self):
        logger.info("Initializing Threat Detection Crew")
        
        logger.debug(f"Loading agents config from: {self.agents_config}")
        logger.debug(f"Loading tasks config from: {self.tasks_config}")
        
        # Load YAML configs
        try:
            with open(self.agents_config, "r") as f:
                self.agents_config = yaml.safe_load(f)
            
            with open(self.tasks_config, "r") as f:
                self.tasks_config = yaml.safe_load(f)
            
            logger.info(
                f"✓ Agents config loaded: {list(self.agents_config.keys())}"
            )
            logger.info(
                f"✓ Tasks config loaded: {list(self.tasks_config.keys())}"
            )
        
        except Exception as e:
            logger.error(f"Failed to load YAML configs: {e}", exc_info=True)
            raise RuntimeError(f"Error loading YAML configs: {e}")
        
        # Initialize tools
        self.vision_tools = self._setup_vision_tools()
        self.drone_tools = self._setup_drone_tools()
        self.actuator_tools = self._setup_actuator_tools()
        
        logger.info(f"Tools initialized: {len(self.vision_tools) + len(self.drone_tools) + len(self.actuator_tools)} total")
    
    def _setup_vision_tools(self) -> List:
        """Initialize vision and fusion tools"""
        logger.debug("Setting up vision tools")
        return [
            YOLODetectionTool(),
            RadarFusionTool()
        ]
    
    def _setup_drone_tools(self) -> List:
        """Initialize drone analysis tools"""
        logger.debug("Setting up drone analysis tools")
        return [
            DroneAnalysisTool()
        ]
    
    def _setup_actuator_tools(self) -> List:
        """Initialize actuator tools"""
        logger.debug("Setting up actuator tools")
        return [
            DEWActuator(),
            CIWSActuator(),
            ElectronicJammingActuator()
        ]
    
    @agent
    def vision_analyst_agent(self) -> Agent:
        """
        Agent to detect threats in images and fuse with radar data.
        """
        logger.debug("Creating Vision Analyst Agent")
        
        return Agent(
            config=self.agents_config['vision_analyst_agent'],
            tools=self.vision_tools,
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )
    
    @agent
    def coordinator_agent(self) -> Agent:
        """
        Agent to coordinate threat analysis and delegate to specialists.
        """
        logger.debug("Creating Coordinator Agent")
        
        return Agent(
            config=self.agents_config['coordinator_agent'],
            tools=[],  # Coordinator doesn't use tools directly
            verbose=True,
            allow_delegation=True,  # KEY: Coordinator can delegate
            max_iter=5
        )
    
    @agent
    def drone_specialist_agent(self) -> Agent:
        """
        Agent to analyze drone threats in detail.
        """
        logger.debug("Creating Drone Specialist Agent")
        
        return Agent(
            config=self.agents_config['drone_specialist_agent'],
            tools=self.drone_tools,
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )
    
    @agent
    def tactical_response_agent(self) -> Agent:
        """
        Agent to develop tactical countermeasure plans.
        """
        logger.debug("Creating Tactical Response Agent")
        
        return Agent(
            config=self.agents_config['tactical_response_agent'],
            tools=[],  # Planning agent doesn't need tools
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    @agent
    def actuator_agent(self) -> Agent:
        """
        Agent to execute countermeasure plans.
        """
        logger.debug("Creating Actuator Agent")
        
        return Agent(
            config=self.agents_config['actuator_agent'],
            tools=self.actuator_tools,
            verbose=True,
            allow_delegation=False,
            max_iter=15  # May need multiple tool calls for complex plans
        )
    
    @task
    def visual_detection_task(self) -> Task:
        """Task to detect and classify visual threats"""
        logger.debug("Creating visual detection task")
        return Task(
            config=self.tasks_config['visual_detection_task']
        )
    
    @task
    def threat_coordination_task(self) -> Task:
        """Task to coordinate and prioritize threats"""
        logger.debug("Creating threat coordination task")
        return Task(
            config=self.tasks_config['threat_coordination_task']
        )
    
    @task
    def drone_analysis_task(self) -> Task:
        """Task to analyze drone threats"""
        logger.debug("Creating drone analysis task")
        return Task(
            config=self.tasks_config['drone_analysis_task']
        )
    
    @task
    def tactical_planning_task(self) -> Task:
        """Task to develop countermeasure plans"""
        logger.debug("Creating tactical planning task")
        return Task(
            config=self.tasks_config['tactical_planning_task']
        )
    
    @task
    def countermeasure_execution_task(self) -> Task:
        """Task to execute countermeasures"""
        logger.debug("Creating countermeasure execution task")
        return Task(
            config=self.tasks_config['countermeasure_execution_task']
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Threat Detection Crew"""
        try:
            logger.info("Assembling Threat Detection Crew")
            
            crew_instance = Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                verbose=True,
                full_output=True,
                output_folder='output',
                max_rpm=20
            )
            
            logger.info("✓ Threat Detection Crew assembled successfully")
            logger.info(f"  Agents: {len(self.agents)}")
            logger.info(f"  Tasks: {len(self.tasks)}")
            logger.info("  Configuration: Coordinator can delegate to specialists")
            
            return crew_instance
        
        except Exception as e:
            logger.error(f"Failed to create crew: {e}", exc_info=True)
            raise RuntimeError(f"Cannot create crew: {e}")
