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
        logger.error("Scenario not found in SCENARIOS")
        return "", ""
    
    logger.info(f"load_scenario name={scenario_name!r} keys={list(SCENARIOS.keys())}")
    scenario = SCENARIOS[scenario_name]
    signal_json = json.dumps(scenario["signal_data"], indent=2)
    logger.info(f"Loaded signal_json len={len(signal_json)} head={signal_json[:30]!r}")
    systems = ", ".join(scenario["active_systems"])
    
    return signal_json, systems


def parse_active_systems(systems_text: str) -> List[str]:
    """Parse comma-separated active systems"""
    if not systems_text or systems_text.strip() == "":
        return []
    
    systems = [s.strip() for s in systems_text.split(",")]
    return [s for s in systems if s]  # Remove empty strings


def convert_to_markdown(text: str) -> str:
    """
    Convert plain text report to clean, structured Markdown format.
    
    Handles the specific format from CrewAI agent outputs:
    - === HEADER === lines → ## Headers
    - [SECTION NAME] lines → ### Sections  
    - Key: Value pairs → **Key:** Value
    - Indented data blocks → Proper formatting
    - Checkboxes and bullets → Clean lists
    """
    if not text or text.strip() == "":
        return "*No data available*"
    
    lines = text.split('\n')
    markdown_lines = []
    in_emitter_block = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip pure separator lines (only = or -)
        if stripped and all(c == '=' for c in stripped):
            continue
        if stripped and all(c == '-' for c in stripped):
            markdown_lines.append("")  # Add spacing instead
            continue
        
        # Empty lines - preserve for spacing
        if not stripped:
            markdown_lines.append("")
            continue
        
        # Main headers: === TITLE === or lines with title wrapped in ===
        if '===' in stripped:
            # Extract text between === markers
            title = stripped.replace('=', '').strip()
            if title:
                markdown_lines.append(f"\n## {title}\n")
                in_emitter_block = False
            continue
        
        # Section headers: [SECTION NAME] or [SECTION NAME] ----
        if stripped.startswith('[') and ']' in stripped:
            # Extract section name
            section_end = stripped.index(']')
            section_name = stripped[1:section_end]
            remainder = stripped[section_end + 1:].replace('-', '').strip()
            
            markdown_lines.append(f"\n### {section_name}\n")
            if remainder and remainder not in ['...', '[None detected...]']:
                markdown_lines.append(remainder)
            in_emitter_block = True
            continue
        
        # Skip [None detected...] type messages but show them nicely
        if stripped in ['[None detected...]', '[None]', '[None identified as critical]']:
            markdown_lines.append(f"*{stripped[1:-1] if stripped.startswith('[') else stripped}*")
            continue
        
        # Emitter ID lines - make them stand out
        if stripped.startswith('Emitter ID:'):
            emitter_id = stripped.split(':', 1)[1].strip()
            markdown_lines.append(f"\n**🎯 Emitter {emitter_id}**\n")
            continue
        
        # Checkboxes: ☐ or ✓
        if stripped.startswith('☐ '):
            markdown_lines.append(f"- [ ] {stripped[2:]}")
            continue
        if stripped.startswith('✓ '):
            markdown_lines.append(f"- [x] {stripped[2:]}")
            continue
        
        # Bullet points with various markers
        if stripped.startswith('• '):
            markdown_lines.append(f"- {stripped[2:]}")
            continue
        
        # Indented key-value pairs (emitter details)
        if line.startswith('  ') and ':' in stripped:
            parts = stripped.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                if value:
                    markdown_lines.append(f"  - **{key}:** {value}")
                else:
                    markdown_lines.append(f"  - **{key}**")
                continue
        
        # Top-level key-value pairs
        if ':' in stripped and not stripped.startswith(' '):
            parts = stripped.split(':', 1)
            if len(parts) == 2 and len(parts[0]) < 40:
                key = parts[0].strip()
                value = parts[1].strip()
                # Special formatting for status values
                if value.upper() in ['ACTIVE', 'OPERATIONAL', 'MAINTAINED', 'EXCELLENT']:
                    markdown_lines.append(f"**{key}:** `{value}` ✅")
                elif value.upper() in ['SECURED', 'REDUCED', 'LIMITED']:
                    markdown_lines.append(f"**{key}:** `{value}` 🔒")
                elif value.upper() in ['HIGH', 'CRITICAL']:
                    markdown_lines.append(f"**{key}:** `{value}` ⚠️")
                elif value.upper() in ['MEDIUM']:
                    markdown_lines.append(f"**{key}:** `{value}` 🟡")
                elif value.upper() in ['LOW']:
                    markdown_lines.append(f"**{key}:** `{value}` 🟢")
                elif value:
                    markdown_lines.append(f"**{key}:** {value}")
                else:
                    markdown_lines.append(f"**{key}**")
                continue
        
        # Regular text - just add it
        markdown_lines.append(stripped)
    
    # Clean up excessive blank lines
    result = '\n'.join(markdown_lines)
    while '\n\n\n' in result:
        result = result.replace('\n\n\n', '\n\n')
    
    return result.strip()


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
        
        # Read output files and convert to Markdown
        output_files = result['output_files']
        
        signal_report = convert_to_markdown(read_output_file(output_files['signal_processing']))
        threat_report = convert_to_markdown(read_output_file(output_files['threat_assessment']))
        ew_report = convert_to_markdown(read_output_file(output_files['ew_response']))
        comm_report = convert_to_markdown(read_output_file(output_files['communication_reconfig']))
        
        status_msg = "✅ ASSESSMENT COMPLETED SUCCESSFULLY\n\nAll reports generated. Review each tab for detailed analysis."
        
        progress(1.0, desc="Complete!")
        logger.info("Assessment completed successfully")
        
        return status_msg, signal_report, threat_report, ew_report, comm_report
        
    except Exception as e:
        error_msg = f"❌ UNEXPECTED ERROR\n\n{str(e)}"
        logger.error(f"Assessment error: {e}", exc_info=True)
        return error_msg, "", "", "", ""


def create_gradio_interface():
    """Create the Gradio interface"""
    
    # Create output directory
    Path("output").mkdir(exist_ok=True)
    
    # Custom CSS for military-modern aesthetic
    custom_css = """
    /* Main container styling */
    .gradio-container {
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
    }
    
    /* Report container styling */
    .report-container {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460;
        border-radius: 8px;
        padding: 20px;
        margin: 10px 0;
    }
    
    /* Markdown content in tabs */
    .prose {
        max-width: none !important;
    }
    
    .prose h2 {
        color: #00d4ff !important;
        border-bottom: 2px solid #0f3460;
        padding-bottom: 8px;
        margin-top: 24px !important;
        font-size: 1.4em !important;
        font-weight: 600 !important;
    }
    
    .prose h3 {
        color: #7dd3fc !important;
        margin-top: 20px !important;
        font-size: 1.15em !important;
        font-weight: 500 !important;
    }
    
    .prose strong {
        color: #e0f2fe !important;
    }
    
    .prose code {
        background: #1e3a5f !important;
        color: #4ade80 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-size: 0.9em !important;
    }
    
    .prose ul {
        margin-left: 16px !important;
    }
    
    .prose li {
        margin: 4px 0 !important;
    }
    
    /* Tab styling */
    .tab-nav button {
        font-weight: 500 !important;
    }
    
    .tab-nav button.selected {
        border-bottom: 3px solid #00d4ff !important;
    }
    
    /* Status box styling */
    #status-box textarea {
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    }
    """
    
    with gr.Blocks(
        title="Susceptibility Agent", 
        theme=gr.themes.Base(
            primary_hue="cyan",
            secondary_hue="slate",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("Inter")
        ).set(
            body_background_fill="#0f172a",
            body_background_fill_dark="#0f172a",
            body_text_color="#e2e8f0",
            body_text_color_dark="#e2e8f0",
            block_background_fill="#1e293b",
            block_background_fill_dark="#1e293b",
            block_border_color="#334155",
            block_border_color_dark="#334155",
            block_label_text_color="#94a3b8",
            block_label_text_color_dark="#94a3b8",
            input_background_fill="#0f172a",
            input_background_fill_dark="#0f172a",
            input_border_color="#334155",
            input_border_color_dark="#334155",
            button_primary_background_fill="#0891b2",
            button_primary_background_fill_dark="#0891b2",
            button_primary_background_fill_hover="#06b6d4",
            button_primary_background_fill_hover_dark="#06b6d4",
        ),
        css=custom_css
    ) as demo:
        
        gr.Markdown("""
        # 🛥️ Naval Susceptibility Agent
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
            interactive=False,
            elem_id="status-box"
        )
        
        gr.Markdown("### 📊 Assessment Reports")
        
        with gr.Tabs() as tabs:
            with gr.Tab("📡 Signal Intelligence", id="signal"):
                signal_output = gr.Markdown(
                    value="*Run an assessment to see results...*",
                    elem_classes=["report-content"]
                )
            
            with gr.Tab("⚠️ Threat Assessment", id="threat"):
                threat_output = gr.Markdown(
                    value="*Run an assessment to see results...*",
                    elem_classes=["report-content"]
                )
            
            with gr.Tab("🛡️ EW Response", id="ew"):
                ew_output = gr.Markdown(
                    value="*Run an assessment to see results...*",
                    elem_classes=["report-content"]
                )
            
            with gr.Tab("📞 Communications", id="comms"):
                comm_output = gr.Markdown(
                    value="*Run an assessment to see results...*",
                    elem_classes=["report-content"]
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
    
    try:
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True
        )
    except KeyboardInterrupt:
        pass  # Silently handle Ctrl+C
    finally:
        logger.info("="*50)
        logger.info("🛥️  Susceptibility Agent stopped gracefully")
        logger.info("="*50)