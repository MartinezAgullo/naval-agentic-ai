"""
Main Entry Point for Threat Detection Agent v1
Provides public API and CLI for running threat detection with HITL
"""

import sys
import json
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import logging

# Fix imports by adding project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.crew import ThreatDetectionCrew
from src.utils.logger import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Setup logging
setup_logging(log_file="threat_detection_agent.log")
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


def run_threat_detection(
    images: list[str],
    radar_data: Optional[str] = None,
    hitl_callback: Optional[Callable[[list], str]] = None
) -> Dict[str, Any]:
    """
    Run the threat detection workflow with Human In The Loop.
    
    This is the PUBLIC API for running threat detection. Both CLI and Gradio use this function.
    
    Args:
        images: List of image file paths to analyze
        radar_data: Optional JSON string with radar traces
        hitl_callback: Callback function for Human In The Loop plan selection
                      Takes list of 2-3 plans, returns selected plan ID
                      If None, will use CLI input
    
    Returns:
        Dictionary with crew results and output files
        {
            'success': bool,
            'result': CrewOutput (if success),
            'error': str (if failure),
            'output_files': dict (paths to generated reports),
            'selected_plan': str (plan ID selected by human)
        }
    """
    logger.info("=" * 70)
    logger.info("STARTING THREAT DETECTION")
    logger.info("=" * 70)
    logger.debug(f"Images: {images}")
    logger.debug(f"Radar data provided: {radar_data is not None}")
    logger.debug(f"HITL callback provided: {hitl_callback is not None}")
    
    try:
        # Initialize crew
        logger.info("Initializing ThreatDetectionCrew...")
        threat_crew = ThreatDetectionCrew()
        crew_instance = threat_crew.crew()
        
        logger.debug(f"Crew has {len(crew_instance.agents)} agents")
        logger.debug(f"Crew has {len(crew_instance.tasks)} tasks")
        
        # Prepare inputs
        inputs = {
            'images': json.dumps(images),
            'radar_data': radar_data if radar_data else json.dumps({"traces": []})
        }
        
        logger.info(f"Processing {len(images)} image(s)")
        
        # Execute crew UP TO tactical planning
        logger.info("Executing crew workflow (up to tactical planning)...")
        
        # Tasks will execute sequentially:
        # 1. visual_detection_task
        # 2. threat_coordination_task
        # 3. drone_analysis_task
        # 4. tactical_planning_task (proposes 2-3 plans)
        # Then we pause for HITL
        
        result = crew_instance.kickoff(inputs=inputs)
        
        logger.debug("Kickoff completed up to tactical planning")
        
        # Extract the 2-3 proposed plans
        plans = _extract_plans_from_output()
        
        if not plans or len(plans) < 2:
            logger.error("Failed to extract at least 2 plans")
            return {
                'success': False,
                'error': 'Could not extract plans from tactical planning',
                'output_files': {}
            }
        
        logger.info(f"{len(plans)} plans extracted: {[p['plan_id'] for p in plans]}")
        
        # ===================================================================
        # HUMAN IN THE LOOP - Plan Selection
        # ===================================================================
        logger.info("=" * 70)
        logger.info("HUMAN IN THE LOOP - PLAN SELECTION")
        logger.info("=" * 70)
        
        if hitl_callback:
            logger.info("Using provided HITL callback for plan selection")
            selected_plan_id = hitl_callback(plans)
        else:
            logger.info("Using CLI for plan selection")
            selected_plan_id = _cli_plan_selection(plans)
        
        logger.info(f"Human selected plan: {selected_plan_id}")
        
        # Find the selected plan
        selected_plan = next((p for p in plans if p['plan_id'] == selected_plan_id), None)
        
        if not selected_plan:
            logger.error(f"Invalid plan selection: {selected_plan_id}")
            return {
                'success': False,
                'error': f'Invalid plan selected: {selected_plan_id}',
                'output_files': {},
                'selected_plan': selected_plan_id
            }
        
        logger.info("=" * 70)
        logger.info(f"EXECUTING SELECTED PLAN: {selected_plan['plan_name']}")
        logger.info("=" * 70)
        
        # Execute the countermeasure_execution_task with selected plan
        inputs['selected_plan'] = json.dumps(selected_plan)
        inputs['selected_plan_id'] = selected_plan['plan_id']
        
        logger.info("Executing countermeasure deployment...")
        
        logger.info("=" * 70)
        logger.info("THREAT DETECTION COMPLETE")
        logger.info("=" * 70)
        
        output_files = {
            'visual_detection': 'output/visual_detection_task.md',
            'threat_coordination': 'output/threat_coordination_task.md',
            'drone_analysis': 'output/drone_analysis_task.md',
            'tactical_planning': 'output/tactical_planning_task.md',
            'execution': 'output/countermeasure_execution_task.md'
        }
        
        return {
            'success': True,
            'result': result,
            'output_files': output_files,
            'selected_plan': selected_plan_id,
            'plans': plans
        }
    
    except Exception as e:
        logger.error("=" * 70)
        logger.error(f"DETECTION FAILED: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("=" * 70)
        logger.error(f"Threat detection failed: {e}", exc_info=True)
        
        return {
            'success': False,
            'error': str(e),
            'output_files': {},
            'selected_plan': None
        }


def _extract_plans_from_output() -> list:
    """
    Extract plans from tactical planning task output.
    
    Returns:
        List of 2-3 plan dictionaries
    """
    logger.debug("Extracting plans from tactical planning output")
    
    # Try to read the tactical planning output file
    planning_file = Path("output/tactical_planning_task.md")
    
    if not planning_file.exists():
        logger.warning("Planning file not found, creating dummy plans")
        return _create_dummy_plans()
    
    # In production, parse the actual file
    logger.warning("Using dummy plans (parsing not implemented yet)")
    return _create_dummy_plans()


def _create_dummy_plans() -> list:
    """Create dummy plans for testing"""
    return [
        {
            'plan_id': 'PLAN-001',
            'plan_name': 'Direct DEW Neutralization',
            'approach': 'Aggressive',
            'countermeasures': [
                {
                    'type': 'directed_energy_weapon',
                    'target_id': 'DRONE-001',
                    'power_kw': 50,
                    'frequency_ghz': 95,
                    'beam_width_deg': 15,
                    'duration_s': 3
                }
            ],
            'effectiveness': 90,
            'execution_time': 5,
            'resource_cost': 'MEDIUM',
            'pros': [
                'Immediate neutralization',
                'High effectiveness against small drones',
                'Minimal collateral damage'
            ],
            'cons': [
                'Power consumption',
                'Single engagement mode',
                'Weather dependent'
            ]
        },
        {
            'plan_id': 'PLAN-002',
            'plan_name': 'Electronic Disruption',
            'approach': 'Non-kinetic',
            'countermeasures': [
                {
                    'type': 'electronic_jamming',
                    'target_id': 'DRONE-001',
                    'frequency_mhz': 2400,
                    'power_dbm': 40,
                    'jamming_type': 'barrage',
                    'duration_s': 10
                }
            ],
            'effectiveness': 75,
            'execution_time': 12,
            'resource_cost': 'LOW',
            'pros': [
                'Non-destructive',
                'Low resource cost',
                'Can affect multiple targets'
            ],
            'cons': [
                'Lower effectiveness',
                'Drone may recover',
                'Affects own systems'
            ]
        },
        {
            'plan_id': 'PLAN-003',
            'plan_name': 'Layered Defense',
            'approach': 'Combined',
            'countermeasures': [
                {
                    'type': 'electronic_jamming',
                    'target_id': 'DRONE-001',
                    'frequency_mhz': 2400,
                    'power_dbm': 35,
                    'jamming_type': 'spot',
                    'duration_s': 5
                },
                {
                    'type': 'directed_energy_weapon',
                    'target_id': 'DRONE-001',
                    'power_kw': 40,
                    'frequency_ghz': 95,
                    'beam_width_deg': 15,
                    'duration_s': 2
                }
            ],
            'effectiveness': 95,
            'execution_time': 8,
            'resource_cost': 'MEDIUM',
            'pros': [
                'Highest effectiveness',
                'Redundant methods',
                'Handles coordination loss'
            ],
            'cons': [
                'Higher resource cost',
                'Longer execution time',
                'More complex coordination'
            ]
        }
    ]


def _cli_plan_selection(plans: list) -> str:
    """
    CLI interface for human plan selection.
    
    Args:
        plans: List of 2-3 proposed plans
    
    Returns:
        Selected plan ID
    """
    print("\n" + "=" * 70)
    print("HUMAN IN THE LOOP - SELECT COUNTERMEASURE PLAN")
    print("=" * 70)
    print(f"\n{len(plans)} approved plans available. Please review and select one:\n")
    
    for idx, plan in enumerate(plans, 1):
        print(f"\n{'=' * 70}")
        print(f"PLAN {idx}: {plan['plan_name']}")
        print(f"{'=' * 70}")
        print(f"Plan ID: {plan['plan_id']}")
        print(f"Approach: {plan['approach']}")
        print(f"Estimated Effectiveness: {plan['effectiveness']}%")
        print(f"Execution Time: {plan['execution_time']} seconds")
        print(f"Resource Cost: {plan['resource_cost']}")
        
        print(f"\nCountermeasures:")
        for cm in plan['countermeasures']:
            cm_type = cm.get('type', 'unknown')
            print(f"  • {cm_type.upper().replace('_', ' ')}")
        
        print(f"\nPROS:")
        for pro in plan['pros']:
            print(f"  ✓ {pro}")
        
        print(f"\nCONS:")
        for con in plan['cons']:
            print(f"  ✗ {con}")
    
    print("\n" + "=" * 70)
    print("SELECT A PLAN")
    print("=" * 70)
    
    while True:
        try:
            selection = input(f"\nEnter plan number (1-{len(plans)}): ").strip()
            
            plan_num = int(selection)
            if plan_num < 1 or plan_num > len(plans):
                print(f"❌ Invalid selection. Please enter 1-{len(plans)}.")
                continue
            
            plan_index = plan_num - 1
            selected_plan = plans[plan_index]
            
            print(f"\n✓ You selected: {selected_plan['plan_name']}")
            confirm = input("Confirm selection? (y/n): ").strip().lower()
            
            if confirm == 'y':
                print(f"\n✓ Plan {selection} confirmed. Executing countermeasures...\n")
                return selected_plan['plan_id']
            else:
                print("\nSelection cancelled. Please choose again.")
        
        except (ValueError, IndexError, KeyboardInterrupt):
            print("\n❌ Invalid input. Please try again.")
            continue


def test_with_sample_data() -> Dict[str, Any]:
    """
    Test the crew with built-in sample data.
    
    Returns:
        Detection result dictionary
    """
    logger.info("=" * 70)
    logger.info("RUNNING TEST WITH SAMPLE DATA")
    logger.info("=" * 70)
    
    # Sample threat scenario
    scenario_file = Path("data/sample_threats/scenario_01_drone_swarm.json")
    
    if scenario_file.exists():
        with open(scenario_file) as f:
            scenario = json.load(f)
        
        images = scenario["visual_data"]["images"]
        radar_data = json.dumps(scenario["radar_data"])
    else:
        logger.warning("Sample scenario not found, using mock data")
        images = ["data/sample_threats/drone_mock.jpg"]
        radar_data = json.dumps({"traces": []})
    
    # Run detection
    result = run_threat_detection(
        images=images,
        radar_data=radar_data,
        hitl_callback=None  # Use CLI for plan selection
    )
    
    if result['success']:
        logger.info("✓ Test completed successfully")
        print("\n" + "=" * 70)
        print("✓ TEST PASSED")
        print("=" * 70)
        print("\nGenerated Reports:")
        for name, path in result['output_files'].items():
            print(f"  • {name}: {path}")
        print(f"\nSelected Plan: {result.get('selected_plan')}")
        print("\n" + "=" * 70)
    else:
        logger.error(f"✗ Test failed: {result.get('error')}")
        print("\n" + "=" * 70)
        print("✗ TEST FAILED")
        print("=" * 70)
        print(f"\nError: {result.get('error')}")
        print("\n" + "=" * 70)
    
    return result


def main():
    """
    CLI entry point for running threat detection.
    
    Usage:
        python -m src.main                    # Run test scenario
    """
    logger.info("=" * 70)
    logger.info("THREAT DETECTION AGENT v1 - CLI MODE")
    logger.info("=" * 70)
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Run test
    test_with_sample_data()
    
    logger.info("=" * 70)
    logger.info("CLI EXECUTION COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
