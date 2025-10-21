"""
Gradio Interface for Susceptibility Agent v1
Interactive web interface for naval electromagnetic threat assessment

This module ONLY handles the UI. All assessment logic is in src/main.py
"""

import gradio as gr
import json
from pathlib import Path
from typing import List, Tuple
import os

# Import the PUBLIC API from main.py (NO logic duplication)
from src.main import run_susceptibility_assessment
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(level="INFO", log_file="gradio_susceptibility.log", console_level="INFO")
logger = get_logger(__name__)


# Predefined scenarios for quick testing
SCENARIOS = {
    "Scenario 1: Low Threat - Civilian Traffic": {
        "description": "Routine maritime environment with civilian vessels",
        "signal_data": {
            "sensor_type": "radar",
            "operational_mode": "normal",
            "detections": [
                {
                    "emitter_id": "E-001",
                    "emitter_type": "radar",
                    "frequency_mhz": 9400.0,
                    "power_dbm": 45.0,
                    "bearing_degrees": 180.0,
                    "range_km": 25.0,
                    "classification": "Navigation Radar"
                },
                {
                    "emitter_id": "E-002",
                    "emitter_type": "communication",
                    "frequency_mhz": 156.0,
                    "power_dbm": 40.0,
                    "bearing_degrees": 225.0,
                    "range_km": 18.0,
                    "classification": "VHF Marine Radio"
                }
            ]
        },
        "active_systems": ["navigation_radar", "communications", "ais"]
    },
    
    "Scenario 2: Medium Threat - Military Presence": {
        "description": "Military vessel detected, maintaining distance",
        "signal_data": {
            "sensor_type": "esm",
            "operational_mode": "normal",
            "detections": [
                {
                    "emitter_id": "E-001",
                    "emitter_type": "radar",
                    "frequency_mhz": 2850.0,
                    "power_dbm": 62.5,
                    "bearing_degrees": 45.0,
                    "range_km": 95.0,
                    "classification": "Early Warning Radar"
                },
                {
                    "emitter_id": "E-002",
                    "emitter_type": "radar",
                    "frequency_mhz": 8500.0,
                    "power_dbm": 58.0,
                    "bearing_degrees": 48.0,
                    "range_km": 92.0,
                    "classification": "Surface Search Radar"
                }
            ]
        },
        "active_systems": ["radar", "communications", "navigation_radar", "datalink", "iff"]
    },
    
    "Scenario 3: High Threat - Fire Control Radar": {
        "description": "Active targeting radar detected at medium range",
        "signal_data": {
            "sensor_type": "esm",
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
        },
        "active_systems": ["radar", "communications", "navigation_radar", "datalink", "iff"]
    },
    
    "Scenario 4: Critical Threat - Active Jamming": {
        "description": "Electronic warfare attack with jamming detected",
        "signal_data": {
            "sensor_type": "esm",
            "operational_mode": "normal",
            "detections": [
                {
                    "emitter_id": "E-001",
                    "emitter_type": "radar",
                    "frequency_mhz": 10000.0,
                    "power_dbm": 70.0,
                    "bearing_degrees": 15.0,
                    "range_km": 28.0,
                    "classification": "Fire Control Radar"
                },
                {
                    "emitter_id": "E-002",
                    "emitter_type": "jammer",
                    "frequency_mhz": 9400.0,
                    "power_dbm": 65.0,
                    "bearing_degrees": 18.0,
                    "range_km": 30.0,
                    "classification": "Jammer"
                }
            ]
        },
        "active_systems": ["radar", "communications", "navigation_radar", "datalink", "iff", "fire_control_radar"]
    }
}


def load_scenario(scenario_name: str) -> Tuple[str, str]:
    """Load a predefined scenario"""
    logger.info(f"Loading scenario: {scenario_name}")
    
    if scenario_name not in SCENARIOS:
        return "", ""
    
    scenario = SCENARIOS[scenario_name]
    signal_json = json.dumps(scenario["signal_data"], indent=2)
    systems = ", ".join(scenario["active_systems"])
    
    return signal_json, systems


def parse_active_systems(systems_text: str) -> List[str]:
    """Parse comma-separated active systems"""
    if not systems_text or systems_text.strip() == "":
        return []
    
    systems = [s.strip() for s in systems_text.split(",")]
    return [s for s in systems if s]  # Remove empty strings


def run_assessment(signal_input: str, active_systems_text: str, progress=gr.Progress()) -> Tuple[str, str, str, str, str]:
    """
    Run susceptibility assessment and return results
    
    Returns:
        Tuple of (status, signal_report, threat_report, ew_report, comm_report)
    """
    logger.info("Starting assessment from Gradio interface")
    
    try:
        # Validate inputs
        if not signal_input or signal_input.strip() == "":
            error_msg = "❌ ERROR: No signal data provided"
            logger.error(error_msg)
            return error_msg, "", "", "", ""
        
        # Parse active systems
        active_systems = parse_active_systems(active_systems_text) if active_systems_text else None
        
        logger.info(f"Signal input length: {len(signal_input)} chars")
        logger.info(f"Active systems: {active_systems}")
        
        # Update progress
        progress(0.1, desc="Initializing crew...")
        
        # Run assessment
        result = run_susceptibility_assessment(
            signal_input=signal_input,
            active_systems=active_systems
        )
        
        progress(0.9, desc="Generating reports...")
        
        if not result['success']:
            error_msg = f"❌ ASSESSMENT FAILED\n\nError: {result.get('error', 'Unknown error')}"
            logger.error(error_msg)
            return error_msg, "", "", "", ""
        
        # Read output files
        output_files = result['output_files']
        
        signal_report = read_output_file(output_files['signal_processing'])
        threat_report = read_output_file(output_files['threat_assessment'])
        ew_report = read_output_file(output_files['ew_response'])
        comm_report = read_output_file(output_files['communication_reconfig'])
        
        status_msg = "✅ ASSESSMENT COMPLETED SUCCESSFULLY\n\nAll reports generated. Review each tab for detailed analysis."
        
        progress(1.0, desc="Complete!")
        logger.info("Assessment completed successfully")
        
        return status_msg, signal_report, threat_report, ew_report, comm_report
        
    except Exception as e:
        error_msg = f"❌ UNEXPECTED ERROR\n\n{str(e)}"
        logger.error(f"Assessment error: {e}", exc_info=True)
        return error_msg, "", "", "", ""


def read_output_file(file_path: str) -> str:
    """Read output file content"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return f"⚠️ Output file not found: {file_path}"
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return f"❌ Error reading file: {str(e)}"


def create_gradio_interface():
    """Create the Gradio interface"""
    
    # Create output directory
    Path("output").mkdir(exist_ok=True)
    
    with gr.Blocks(title="Susceptibility Agent v1", theme=gr.themes.Soft()) as demo:
        
        gr.Markdown("""
        # 🛥️ Naval Susceptibility Agent v1
        ## Electromagnetic Warfare Threat Assessment System
        
        This system analyzes electromagnetic signals detected by ship sensors and assesses the threat level to own ship.
        It provides recommendations for emission control and communication reconfiguration.
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🎯 Quick Start")
                
                scenario_dropdown = gr.Dropdown(
                    choices=list(SCENARIOS.keys()),
                    label="Select Scenario",
                    info="Choose a predefined scenario or enter custom data below"
                )
                
                load_btn = gr.Button("📥 Load Scenario", variant="secondary")
                
                gr.Markdown("---")
                
                with gr.Accordion("📋 Scenario Descriptions", open=False):
                    for name, scenario in SCENARIOS.items():
                        gr.Markdown(f"**{name}**\n\n{scenario['description']}")
            
            with gr.Column(scale=2):
                gr.Markdown("### 📡 Signal Input")
                
                signal_input = gr.TextArea(
                    label="Signal Data (JSON)",
                    placeholder='Enter JSON signal data or load a scenario...\n\nExample:\n{\n  "sensor_type": "radar",\n  "detections": [...]\n}',
                    lines=12,
                    max_lines=20
                )
                
                active_systems_input = gr.Textbox(
                    label="Active Ship Systems (comma-separated)",
                    placeholder="radar, communications, navigation_radar, datalink, iff",
                    info="List your currently emitting systems"
                )
                
                run_btn = gr.Button("🚀 Run Assessment", variant="primary", size="lg")
        
        gr.Markdown("---")
        
        status_output = gr.Textbox(
            label="Status",
            lines=3,
            interactive=False
        )
        
        gr.Markdown("### 📊 Assessment Reports")
        
        with gr.Tabs():
            with gr.Tab("📡 Signal Intelligence"):
                signal_output = gr.Textbox(
                    label="Signal Processing Report",
                    lines=20,
                    max_lines=40,
                    interactive=False
                )
            
            with gr.Tab("⚠️ Threat Assessment"):
                threat_output = gr.Textbox(
                    label="Threat Assessment Report",
                    lines=20,
                    max_lines=40,
                    interactive=False
                )
            
            with gr.Tab("🛡️ EW Response"):
                ew_output = gr.Textbox(
                    label="Electronic Warfare Response",
                    lines=20,
                    max_lines=40,
                    interactive=False
                )
            
            with gr.Tab("📞 Communications"):
                comm_output = gr.Textbox(
                    label="Communication Reconfiguration",
                    lines=20,
                    max_lines=40,
                    interactive=False
                )
        
        gr.Markdown("""
        ---
        ### 📖 Usage Instructions
        
        1. **Select a Scenario** or enter custom signal data in JSON format
        2. **Specify Active Systems** currently emitting from your ship
        3. **Click Run Assessment** to process the electromagnetic environment
        4. **Review Reports** in each tab for detailed analysis and recommendations
        
        ### 🔧 Signal Data Format
        
        ```json
        {
          "sensor_type": "radar" | "esm" | "elint",
          "operational_mode": "normal" | "emission_control" | "stealth",
          "detections": [
            {
              "emitter_id": "E-001",
              "emitter_type": "radar" | "communication" | "jammer",
              "frequency_mhz": 9500.0,
              "power_dbm": 68.0,
              "bearing_degrees": 45.0,
              "range_km": 85.0,
              "classification": "Fire Control Radar"
            }
          ]
        }
        ```
        """)
        
        # Event handlers
        load_btn.click(
            fn=load_scenario,
            inputs=[scenario_dropdown],
            outputs=[signal_input, active_systems_input]
        )
        
        run_btn.click(
            fn=run_assessment,
            inputs=[signal_input, active_systems_input],
            outputs=[status_output, signal_output, threat_output, ew_output, comm_output]
        )
    
    return demo


if __name__ == "__main__":
    logger.info("Starting Gradio Susceptibility Agent v1 Interface")
    
    demo = create_gradio_interface()
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
    
    logger.info("Gradio interface stopped")