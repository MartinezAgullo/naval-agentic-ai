"""
Gradio Interface for Threat Detection Agent v1
Provides web UI for uploading images, viewing results, and selecting countermeasure plans
"""

import gradio as gr
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import run_threat_detection
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(log_file="gradio_threat_detection.log")
logger = get_logger(__name__)


# Global state for storing plans
current_plans = []
current_result = None


def process_threat_detection(images, radar_json):
    """
    Process threat detection from uploaded images and radar data.
    
    Args:
        images: List of uploaded image files from Gradio
        radar_json: Optional JSON string with radar traces
    
    Returns:
        Status message, plan options HTML, execution results
    """
    global current_plans, current_result
    
    try:
        logger.info("Processing threat detection via Gradio")
        
        # Check inputs
        if not images or len(images) == 0:
            return "❌ Error: No images uploaded", "", "", "", gr.update(visible=False)
        
        # Save uploaded images temporarily
        image_paths = []
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        for idx, img in enumerate(images):
            if isinstance(img, str):
                # Already a path
                image_paths.append(img)
            else:
                # Gradio file object
                temp_path = temp_dir / f"image_{idx}.jpg"
                # Save the image
                if hasattr(img, 'name'):
                    import shutil
                    shutil.copy(img.name, temp_path)
                    image_paths.append(str(temp_path))
        
        logger.info(f"Processing {len(image_paths)} images")
        
        # Parse radar data if provided
        radar_data = None
        if radar_json and radar_json.strip():
            try:
                json.loads(radar_json)  # Validate JSON
                radar_data = radar_json
            except json.JSONDecodeError:
                return "❌ Error: Invalid radar JSON format", "", "", "", gr.update(visible=False)
        
        # Run threat detection WITHOUT execution (skip HITL, just get plans)
        result = run_threat_detection(
            images=image_paths,
            radar_data=radar_data,
            hitl_callback=None,
            skip_execution=True  # Stop at tactical planning, return plans
        )
        
        if not result['success']:
            error_msg = result.get('error', 'Unknown error')
            return f"❌ Detection failed: {error_msg}", "", "", "", gr.update(visible=False)
        
        # Store plans globally for later selection
        current_plans = result.get('plans', [])
        current_result = result
        
        # Format detection results
        status_html = _format_status(result)
        
        # Format plans for selection
        plans_html = _format_plans(current_plans)
        
        # Extract drone analysis report separately
        drone_analysis_md = _read_drone_analysis(result.get('output_files', {}))
        
        # Read all reports
        reports_text = _read_reports(result.get('output_files', {}))
        
        logger.info(f"Detection complete: {len(current_plans)} plans generated")
        
        return status_html, plans_html, drone_analysis_md, reports_text, gr.update(visible=True)
    
    except Exception as e:
        logger.error(f"Gradio processing error: {e}", exc_info=True)
        return f"❌ Error: {str(e)}", "", "", "", gr.update(visible=False)


def select_plan(plan_number):
    """
    Execute selected countermeasure plan WITH REAL ACTUATORS.
    
    Args:
        plan_number: Plan number (1, 2, or 3)
    
    Returns:
        Execution result HTML
    """
    global current_plans, current_result
    
    try:
        if not current_plans:
            return "<p style='color: #721c24;'>❌ Error: No plans available. Run detection first.</p>"
        
        plan_idx = plan_number - 1
        if plan_idx < 0 or plan_idx >= len(current_plans):
            return f"<p style='color: #721c24;'>❌ Error: Invalid plan number {plan_number}</p>"
        
        selected_plan = current_plans[plan_idx]
        logger.info(f"User selected plan: {selected_plan['plan_id']}")
        
        # REAL EXECUTION: Run the crew's actuator agent
        from src.crew import ThreatDetectionCrew
        from src.tools.actuators import DEWActuator, CIWSActuator, ElectronicJammingActuator
        
        execution_results = []
        overall_success = True
        
        # Execute each countermeasure using actual actuator tools
        for idx, cm in enumerate(selected_plan['countermeasures'], 1):
            cm_type = cm.get('type', 'unknown')
            
            logger.info(f"Executing countermeasure {idx}: {cm_type}")
            
            # Select and call appropriate actuator
            if cm_type == 'directed_energy_weapon':
                actuator = DEWActuator()
                result_json = actuator._run(
                    target_id=cm.get('target_id', 'DRONE-001'),
                    power_kw=cm.get('power_kw', 50),
                    frequency_ghz=cm.get('frequency_ghz', 95),
                    beam_width_deg=cm.get('beam_width_deg', 15),
                    duration_s=cm.get('duration_s', 3)
                )
            elif cm_type == 'ciws_engagement':
                actuator = CIWSActuator()
                result_json = actuator._run(
                    target_id=cm.get('target_id', 'DRONE-001'),
                    weapon_type=cm.get('weapon', 'RAM'),
                    rounds=cm.get('rounds', 2),
                    engagement_range_km=cm.get('engagement_range_km', 3)
                )
            elif cm_type == 'electronic_jamming':
                actuator = ElectronicJammingActuator()
                result_json = actuator._run(
                    target_id=cm.get('target_id', 'DRONE-001'),
                    frequency_mhz=cm.get('frequency_mhz', 2400),
                    power_dbm=cm.get('power_dbm', 40),
                    jamming_type=cm.get('jamming_type', 'barrage'),
                    duration_s=cm.get('duration_s', 10)
                )
            else:
                result_json = json.dumps({
                    "actuator": cm_type,
                    "status": "UNKNOWN",
                    "error": f"Unknown countermeasure type: {cm_type}"
                })
                overall_success = False
            
            result = json.loads(result_json)
            execution_results.append({
                "number": idx,
                "type": cm_type,
                "result": result
            })
            
            if result.get("status") != "SUCCESS":
                overall_success = False
        
        # Format execution results as HTML
        execution_html = f"""
        <div style='padding: 20px; border: 2px solid {"#28a745" if overall_success else "#ffc107"}; border-radius: 5px; background-color: {"#d4edda" if overall_success else "#fff3cd"};'>
            <h3 style='color: {"#155724" if overall_success else "#856404"}; margin-top: 0;'>{'✓' if overall_success else '⚠'} Plan Executed: {selected_plan['plan_name']}</h3>
            <p style='color: #003d7a; margin: 5px 0;'><strong>Plan ID:</strong> {selected_plan['plan_id']}</p>
            <p style='color: #003d7a; margin: 5px 0;'><strong>Approach:</strong> {selected_plan['approach']}</p>
            
            <h4 style='color: #003d7a; margin-top: 15px;'>Execution Log:</h4>
        """
        
        for exec_result in execution_results:
            result_data = exec_result['result']
            status = result_data.get('status', 'UNKNOWN')
            effectiveness = result_data.get('effectiveness', 0)
            
            status_color = '#155724' if status == 'SUCCESS' else '#856404' if status == 'PARTIAL' else '#721c24'
            
            execution_html += f"""
            <div style='margin: 10px 0; padding: 10px; border-left: 3px solid {status_color}; background-color: white;'>
                <p style='color: {status_color}; margin: 5px 0; font-weight: bold;'>
                    [{exec_result['number']}] {exec_result['type'].replace('_', ' ').title()}
                </p>
                <p style='color: #003d7a; margin: 5px 0;'><strong>Status:</strong> {status}</p>
                <p style='color: #003d7a; margin: 5px 0;'><strong>Effectiveness:</strong> {effectiveness}%</p>
                <p style='color: #003d7a; margin: 5px 0;'><strong>Details:</strong> {result_data.get('effects', 'N/A')}</p>
            </div>
            """
        
        execution_html += f"""
            <h4 style='color: #003d7a; margin-top: 15px;'>Mission Result:</h4>
            <p style='color: {"#155724" if overall_success else "#856404"}; font-weight: bold; margin: 5px 0;'>
                {'SUCCESS - All countermeasures executed successfully' if overall_success else 'PARTIAL - Some countermeasures had issues'}
            </p>
        </div>
        """
        
        return execution_html
    
    except Exception as e:
        logger.error(f"Plan execution error: {e}", exc_info=True)
        return f"<p style='color: #721c24;'>❌ Error executing plan: {str(e)}</p>"


def _format_status(result):
    """Format detection status as HTML"""
    html = """
    <div style='padding: 15px; border: 2px solid #28a745; border-radius: 5px; background-color: #d4edda;'>
        <h3 style='color: #155724; margin-top: 0;'>✓ Threat Detection Complete</h3>
    """
    
    if 'plans' in result and result['plans']:
        html += f"<p style='color: #155724; margin-bottom: 0;'><strong>Plans Generated:</strong> {len(result['plans'])}</p>"
    
    html += "<p style='color: #155724; margin-bottom: 0;'>Review the tactical plans below and select one for execution.</p>"
    html += "</div>"
    
    return html


def _format_plans(plans):
    """Format plans as HTML for selection with military styling"""
    if not plans:
        return "<p style='color: #721c24;'>No plans available</p>"
    
    html = "<div style='margin-top: 20px;'>"
    
    for idx, plan in enumerate(plans, 1):
        html += f"""
        <div style='padding: 20px; margin-bottom: 15px; border: 2px solid #1b5e20; border-radius: 5px; background-color: #1b4d1b; color: #e8f5e9;'>
            <h4 style='color: #a5d6a7; margin-top: 0; border-bottom: 2px solid #2e7d32; padding-bottom: 10px;'>Plan {idx}: {plan['plan_name']}</h4>
            <p style='color: #c8e6c9; margin: 8px 0;'><strong style='color: #81c784;'>Plan ID:</strong> {plan['plan_id']}</p>
            <p style='color: #c8e6c9; margin: 8px 0;'><strong style='color: #81c784;'>Approach:</strong> {plan['approach']}</p>
            <p style='color: #c8e6c9; margin: 8px 0;'><strong style='color: #81c784;'>Effectiveness:</strong> {plan['effectiveness']}%</p>
            <p style='color: #c8e6c9; margin: 8px 0;'><strong style='color: #81c784;'>Execution Time:</strong> {plan['execution_time']} seconds</p>
            <p style='color: #c8e6c9; margin: 8px 0;'><strong style='color: #81c784;'>Resource Cost:</strong> {plan['resource_cost']}</p>
            
            <details style='margin-top: 10px;'>
                <summary style='color: #a5d6a7; font-weight: bold; cursor: pointer; padding: 5px; background-color: #2e4d2e; border-radius: 3px;'>▸ Countermeasures</summary>
                <ul style='color: #c8e6c9; margin-top: 10px; background-color: #1a3a1a; padding: 15px; border-radius: 3px;'>
        """
        
        for cm in plan['countermeasures']:
            cm_type = cm.get('type', 'unknown').replace('_', ' ').title()
            html += f"<li style='margin: 5px 0;'>⚡ {cm_type}</li>"
        
        html += """
                </ul>
            </details>
            
            <details style='margin-top: 10px;'>
                <summary style='color: #a5d6a7; font-weight: bold; cursor: pointer; padding: 5px; background-color: #2e4d2e; border-radius: 3px;'>▸ PROS</summary>
                <ul style='color: #a5d6a7; margin-top: 10px; background-color: #1a3a1a; padding: 15px; border-radius: 3px;'>
        """
        
        for pro in plan['pros']:
            html += f"<li style='margin: 5px 0;'>✓ {pro}</li>"
        
        html += """
                </ul>
            </details>
            
            <details style='margin-top: 10px;'>
                <summary style='color: #ffab91; font-weight: bold; cursor: pointer; padding: 5px; background-color: #4d2e2e; border-radius: 3px;'>▸ CONS</summary>
                <ul style='color: #ffccbc; margin-top: 10px; background-color: #3a1a1a; padding: 15px; border-radius: 3px;'>
        """
        
        for con in plan['cons']:
            html += f"<li style='margin: 5px 0;'>✗ {con}</li>"
        
        html += """
                </ul>
            </details>
        </div>
        """
    
    html += "</div>"
    return html


def _read_reports(output_files):
    """Read generated report files"""
    reports_text = ""
    
    for name, path in output_files.items():
        if Path(path).exists():
            with open(path) as f:
                content = f.read()
            reports_text += f"\n\n{'='*70}\n{name.upper()}\n{'='*70}\n\n{content}"
    
    return reports_text if reports_text else "No reports generated yet"


def _read_drone_analysis(output_files):
    """Read drone analysis report specifically for drone analysis tab"""
    drone_path = output_files.get('drone_analysis')
    
    if drone_path and Path(drone_path).exists():
        with open(drone_path) as f:
            return f.read()
    
    return "No drone analysis available yet. Run detection first."

naval_theme = gr.themes.Default(primary_hue="green")

# Build Gradio interface
with gr.Blocks(
    theme=naval_theme,  # 2. Pass the theme here
    title="Naval Threat Detection System",
    css="""
    .dark-green-btn {
        background-color: #1b5e20 !important;
        border-color: #1b5e20 !important;
    }
    .dark-green-btn:hover {
        background-color: #2e7d32 !important;
        border-color: #2e7d32 !important;
    }
    """
) as app:
    gr.Markdown("""
    # 🚢 Naval Threat Detection System v1
    
    Upload images from ship cameras and optional radar traces to detect and respond to threats.
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Input")
            
            image_input = gr.File(
                label="Upload Images",
                file_count="multiple",
                file_types=["image"]
            )
            
            # Image preview
            with gr.Accordion("📸 Image Preview", open=True):
                image_preview = gr.Gallery(
                    label="Uploaded Images",
                    show_label=False,
                    elem_id="gallery",
                    columns=2,
                    rows=2,
                    height="auto",
                    object_fit="contain"
                )
            
            radar_input = gr.Textbox(
                label="Radar Data (Optional JSON)",
                placeholder='{"traces": [...]}',
                lines=5
            )
            
            detect_btn = gr.Button("🔍 Detect Threats", variant="primary", elem_classes="dark-green-btn")
        
        with gr.Column(scale=2):
            gr.Markdown("### Detection Results")
            
            status_output = gr.HTML(label="Status")
            
            # Tabbed interface for different report types
            with gr.Tabs():
                with gr.Tab("📋 Tactical Plans"):
                    plans_output = gr.HTML(label="Available Plans")
                
                with gr.Tab("🚁 Drone Analysis"):
                    drone_analysis_output = gr.Textbox(
                        label="Drone Threat Analysis Report",
                        lines=25,
                        max_lines=40
                    )
                
                with gr.Tab("📊 All Reports"):
                    reports_output = gr.Textbox(
                        label="Detailed Analysis Reports",
                        lines=20,
                        max_lines=50
                    )
    
    with gr.Row(visible=False) as plan_selection_row:
        gr.Markdown("### Select Countermeasure Plan")
        with gr.Row():
            plan1_btn = gr.Button("Execute Plan 1", variant="primary", elem_classes="dark-green-btn")
            plan2_btn = gr.Button("Execute Plan 2", variant="primary", elem_classes="dark-green-btn")
            plan3_btn = gr.Button("Execute Plan 3", variant="primary", elem_classes="dark-green-btn")
    
    execution_output = gr.HTML(label="Execution Results")
    
    # Connect events
    
    # Update image preview when images are uploaded
    def update_image_preview(files):
        """Update gallery when images are uploaded"""
        if not files:
            return []
        
        # Extract file paths
        image_paths = []
        for file in files:
            if hasattr(file, 'name'):
                image_paths.append(file.name)
            elif isinstance(file, str):
                image_paths.append(file)
        
        return image_paths
    
    image_input.change(
        fn=update_image_preview,
        inputs=[image_input],
        outputs=[image_preview]
    )
    
    detect_btn.click(
        fn=process_threat_detection,
        inputs=[image_input, radar_input],
        outputs=[status_output, plans_output, drone_analysis_output, reports_output, plan_selection_row]
    )
    
    plan1_btn.click(
        fn=lambda: select_plan(1),
        outputs=execution_output
    )
    
    plan2_btn.click(
        fn=lambda: select_plan(2),
        outputs=execution_output
    )
    
    plan3_btn.click(
        fn=lambda: select_plan(3),
        outputs=execution_output
    )
    
    gr.Markdown("""
    ---
    ### Instructions
    
    1. **Upload Images**: Select one or more images from ship cameras
    2. **Optional Radar Data**: Provide radar traces in JSON format to enable sensor fusion
    3. **Detect Threats**: Click to run AI analysis
    4. **Review Plans**: Examine the 2-3 generated countermeasure plans
    5. **Select Plan**: Choose and execute a plan
    
    ### Sample Radar JSON Format
    ```json
    {
      "traces": [
        {
          "range_km": 2.5,
          "bearing_degrees": 45,
          "velocity_mps": 12,
          "doppler_frequency_hz": 45,
          "band": "Ku"
        }
      ]
    }
    ```
    """)


if __name__ == "__main__":
    try:
        logger.info("Starting Gradio interface on port 7862")
        app.launch(
            server_name="0.0.0.0",
            server_port=7862,
            share=False
        )
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("="*50)
        logger.info(" Naval Threat Detection Agent stopped gracefully")
        logger.info("="*50)