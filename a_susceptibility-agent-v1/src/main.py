"""
Main Entry Point for Susceptibility Agent v1
Provides public API and CLI for running assessments
"""

import sys
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging


# Fix imports by adding project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("DEBUG: main.py - Initial Setup")
print("=" * 70)
print(f"__file__: {__file__}")
print(f"project_root: {project_root}")
print(f"sys.path[0]: {sys.path[0]}")
print("=" * 70)

from dotenv import load_dotenv
from src.crew import SusceptibilityCrew
from src.utils.logger import setup_logging, get_logger

# Load environment variables
load_dotenv()
print("DEBUG: .env loaded")

# Setup logging - reads LOG_LEVEL from environment
setup_logging(level="INFO", log_file="susceptibility_agent.log")
logger = get_logger(__name__)

# Silence noisy third-party loggers
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger.debug("="*70)
logger.debug("main.py loaded successfully")
logger.debug(f"Module name: {__name__}")
logger.debug(f"Project root: {project_root}")
logger.debug("="*70)


def run_susceptibility_assessment(
    signal_input: str, 
    active_systems: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run the susceptibility assessment workflow.
    
    This is the PUBLIC API for running assessments. Both CLI and Gradio use this function.
    
    Args:
        signal_input: Signal data (JSON file path, JSON string, or text description)
        active_systems: List of currently active ship systems (optional)
    
    Returns:
        Dictionary with crew results and output files
        {
            'success': bool,
            'result': CrewOutput (if success),
            'error': str (if failure),
            'output_files': dict (paths to generated reports)
        }
    """
    logger.info("=" * 70)
    logger.info("STARTING SUSCEPTIBILITY ASSESSMENT")
    logger.info("=" * 70)
    logger.debug(f"Function: run_susceptibility_assessment()")
    logger.debug(f"Signal input length: {len(signal_input)} chars")
    logger.debug(f"Active systems: {active_systems}")
    
    try:
        # Initialize crew
        logger.info("Initializing SusceptibilityCrew...")
        logger.debug("About to instantiate SusceptibilityCrew class")
        
        susceptibility_crew = SusceptibilityCrew()
        
        logger.debug("SusceptibilityCrew instantiated successfully")
        logger.info("Getting crew instance...")
        
        crew_instance = susceptibility_crew.crew()
        
        logger.debug(f"Crew instance type: {type(crew_instance)}")
        logger.debug(f"Crew has {len(crew_instance.agents)} agents")
        logger.debug(f"Crew has {len(crew_instance.tasks)} tasks")
        
        # Prepare inputs
        inputs = {
            'signal_input': signal_input
        }
        
        if active_systems:
            inputs['active_systems'] = active_systems
            logger.info(f"Active systems: {active_systems}")
        
        logger.info(f"Processing signal input: {signal_input[:100]}...")
        logger.debug(f"Full inputs dict: {inputs}")
        
        # Execute crew
        logger.info("Executing crew workflow...")
        logger.debug("Calling crew_instance.kickoff()")
        
        result = crew_instance.kickoff(inputs=inputs)
        
        logger.debug(f"Kickoff completed, result type: {type(result)}")
        logger.info("=" * 70)
        logger.info("SUSCEPTIBILITY ASSESSMENT COMPLETE")
        logger.info("=" * 70)
        
        output_files = {
            'signal_processing': 'output/signal_processing_task.md',
            'threat_assessment': 'output/threat_assessment_task.md',
            'ew_response': 'output/ew_response_task.md',
            'communication_reconfig': 'output/communication_reconfig_task.md'
        }
        
        logger.debug(f"Output files: {output_files}")
        
        return {
            'success': True,
            'result': result,
            'output_files': output_files
        }
        
    except Exception as e:
        logger.error("=" * 70)
        logger.error(f"ASSESSMENT FAILED: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("=" * 70)
        logger.error(f"Susceptibility assessment failed: {e}", exc_info=True)
        
        return {
            'success': False,
            'error': str(e),
            'output_files': {}
        }


def create_sample_signal_data() -> Dict:
    """
    Create sample signal data for testing.
    
    Returns:
        Dictionary with sample radar detections
    """
    logger.debug("Creating sample signal data")
    
    data = {
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
    
    logger.debug(f"Sample data created with {len(data['detections'])} detections")
    return data


def test_with_sample_data() -> Dict[str, Any]:
    """
    Test the crew with built-in sample data.
    
    This is used for CLI testing and validation.
    
    Returns:
        Assessment result dictionary
    """
    logger.info("=" * 70)
    logger.info("RUNNING TEST WITH SAMPLE DATA")
    logger.info("=" * 70)
    logger.debug("Function: test_with_sample_data()")
    
    # Sample signal data
    sample_signal = create_sample_signal_data()
    signal_json = json.dumps(sample_signal)
    
    logger.debug(f"Signal JSON length: {len(signal_json)} chars")
    
    # Active ship systems
    active_systems = [
        "radar",
        "communications",
        "navigation_radar",
        "datalink",
        "iff"
    ]
    
    logger.debug(f"Active systems count: {len(active_systems)}")
    logger.debug(f"Active systems list: {active_systems}")
    
    # Run assessment using public API
    logger.info("Calling run_susceptibility_assessment()...")
    
    result = run_susceptibility_assessment(
        signal_input=signal_json,
        active_systems=active_systems
    )
    
    logger.debug(f"Assessment returned with success={result['success']}")
    
    if result['success']:
        logger.info("✓ Test completed successfully")
        logger.info(f"Output files generated in: output/")
        logger.debug("Printing success message to console")
        
        print("\n" + "=" * 70)
        print("✓ TEST PASSED")
        print("=" * 70)
        print("\nGenerated Reports:")
        for name, path in result['output_files'].items():
            print(f"  • {name}: {path}")
            logger.debug(f"Output file: {name} -> {path}")
        print("\n" + "=" * 70)
    else:
        logger.error(f"✗ Test failed: {result.get('error')}")
        logger.debug("Printing failure message to console")
        
        print("\n" + "=" * 70)
        print("✗ TEST FAILED")
        print("=" * 70)
        print(f"\nError: {result.get('error')}")
        print("\n" + "=" * 70)
    
    logger.debug("test_with_sample_data() returning")
    return result


def main():
    """
    CLI entry point for running assessments.
    
    Usage:
        python -m src.main                    # Run test scenario
        python src/main.py                    # Alternative (requires PYTHONPATH)
    """
    logger.info("=" * 70)
    logger.info("SUSCEPTIBILITY AGENT v1 - CLI MODE")
    logger.info("=" * 70)
    logger.debug(f"Function: main()")
    logger.debug(f"__name__: {__name__}")
    
    logger.info("Running test scenario...")
    
    # Create output directory
    output_dir = Path("output")
    logger.debug(f"Creating output directory: {output_dir}")
    output_dir.mkdir(exist_ok=True)
    logger.debug("Output directory ready")
    
    # Run test
    logger.info("Calling test_with_sample_data()...")
    test_with_sample_data()
    
    logger.info("=" * 70)
    logger.info("CLI EXECUTION COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    logger.debug("Script executed directly (__name__ == '__main__')")
    main()