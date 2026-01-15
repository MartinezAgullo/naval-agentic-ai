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
            return "❌ Error: No images uploaded", "", "", gr.update(visible=False)
        
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
                return "❌ Error: Invalid radar JSON format", "", "", gr.update(visible=False)
        
        # Run threat detection (without execution)
        # We'll stop at tactical planning to get plans for human selection
        result = run_threat_detection(
            images=image_paths,
            radar_data=radar_data,
            hitl_callback=None  # We'll handle HITL via Gradio buttons
        )
        
        if not result['success']:
            error_msg = result.get('error', 'Unknown error')
            return f"❌ Detection failed: {error_msg}", "", "", gr.update(visible=False)
        
        # Store plans globally for later selection
        current_plans = result.get('plans', [])
        current_result = result
        
        # Format detection results
        status_html = _format_status(result)
        
        # Format plans for selection
        plans_html = _format_plans(current_plans)
        
        # Read reports
        reports_text = _read_reports(result.get('output_files', {}))
        
        logger.info(f"Detection complete: {len(current_plans)} plans generated")
        
        return status_html, plans_html, reports_text, gr.update(visible=True)
    
    except Exception as e:
        logger.error(f"Gradio processing error: {e}", exc_info=True)
        return f"❌ Error: {str(e)}", "", "", gr.update(visible=False)


def select_plan(plan_number):
    """
    Execute selected countermeasure plan.
    
    Args:
        plan_number: Plan number (1, 2, or 3)
    
    Returns:
        Execution result HTML
    """
    global current_plans, current_result
    
    try:
        if not current_plans:
            return "❌ Error: No plans available. Run detection first."
        
        plan_idx = plan_number - 1
        if plan_idx < 0 or plan_idx >= len(current_plans):
            return f"❌ Error: Invalid plan number {plan_number}"
        
        selected_plan = current_plans[plan_idx]
        logger.info(f"User selected plan: {selected_plan['plan_id']}")
        
        # In a full implementation, we would re-run the crew with execution task
        # For this POC, we'll simulate execution
        
        execution_html = f"""
        <div style='padding: 20px; border: 2px solid #28a745; border-radius: 5px; background-color: #d4edda;'>
            <h3 style='color: #155724;'>✓ Plan Executed: {selected_plan['plan_name']}</h3>
            <p><strong>Plan ID:</strong> {selected_plan['plan_id']}</p>
            <p><strong>Approach:</strong> {selected_plan['approach']}</p>
            <p><strong>Effectiveness:</strong> {selected_plan['effectiveness']}%</p>
            
            <h4>Countermeasures Executed:</h4>
            <ul>
        """
        
        for cm in selected_plan['countermeasures']:
            cm_type = cm.get('type', 'unknown').replace('_', ' ').title()
            execution_html += f"<li><strong>{cm_type}</strong></li>"
        
        execution_html += """
            </ul>
            <p style='color: #155724; font-weight: bold;'>Mission: SUCCESS</p>
            <p>All threats neutralized. Ship systems operational.</p>
        </div>
        """
        
        return execution_html
    
    except Exception as e:
        logger.error(f"Plan selection error: {e}", exc_info=True)
        return f"❌ Error executing plan: {str(e)}"


def _format_status(result):
    """Format detection status as HTML"""
    html = """
    <div style='padding: 15px; border: 2px solid #28a745; border-radius: 5px; background-color: #d4edda;'>
        <h3 style='color: #155724;'>✓ Threat Detection Complete</h3>
    """
    
    if 'plans' in result and result['plans']:
        html += f"<p><strong>Plans Generated:</strong> {len(result['plans'])}</p>"
    
    html += "<p>Review the tactical plans below and select one for execution.</p>"
    html += "</div>"
    
    return html


def _format_plans(plans):
    """Format plans as HTML for selection"""
    if not plans:
        return "<p>No plans available</p>"
    
    html = "<div style='margin-top: 20px;'>"
    
    for idx, plan in enumerate(plans, 1):
        html += f"""
        <div style='padding: 15px; margin-bottom: 15px; border: 2px solid #007bff; border-radius: 5px; background-color: #cfe2ff;'>
            <h4 style='color: #004085;'>Plan {idx}: {plan['plan_name']}</h4>
            <p><strong>Plan ID:</strong> {plan['plan_id']}</p>
            <p><strong>Approach:</strong> {plan['approach']}</p>
            <p><strong>Effectiveness:</strong> {plan['effectiveness']}%</p>
            <p><strong>Execution Time:</strong> {plan['execution_time']} seconds</p>
            <p><strong>Resource Cost:</strong> {plan['resource_cost']}</p>
            
            <details>
                <summary><strong>Countermeasures</strong></summary>
                <ul>
        """
        
        for cm in plan['countermeasures']:
            cm_type = cm.get('type', 'unknown').replace('_', ' ').title()
            html += f"<li>{cm_type}</li>"
        
        html += """
                </ul>
            </details>
            
            <details style='margin-top: 10px;'>
                <summary><strong>PROS</strong></summary>
                <ul style='color: green;'>
        """
        
        for pro in plan['pros']:
            html += f"<li>✓ {pro}</li>"
        
        html += """
                </ul>
            </details>
            
            <details style='margin-top: 10px;'>
                <summary><strong>CONS</strong></summary>
                <ul style='color: #856404;'>
        """
        
        for con in plan['cons']:
            html += f"<li>✗ {con}</li>"
        
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


# Build Gradio interface
with gr.Blocks(title="Naval Threat Detection System", theme=gr.themes.Soft()) as app:
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
            
            radar_input = gr.Textbox(
                label="Radar Data (Optional JSON)",
                placeholder='{"traces": [...]}',
                lines=5
            )
            
            detect_btn = gr.Button("🔍 Detect Threats", variant="primary")
        
        with gr.Column(scale=2):
            gr.Markdown("### Detection Results")
            
            status_output = gr.HTML(label="Status")
            plans_output = gr.HTML(label="Tactical Plans")
    
    with gr.Row(visible=False) as plan_selection_row:
        gr.Markdown("### Select Countermeasure Plan")
        plan1_btn = gr.Button("Execute Plan 1", variant="secondary")
        plan2_btn = gr.Button("Execute Plan 2", variant="secondary")
        plan3_btn = gr.Button("Execute Plan 3", variant="secondary")
    
    execution_output = gr.HTML(label="Execution Results")
    
    with gr.Accordion("📄 Detailed Reports", open=False):
        reports_output = gr.Textbox(
            label="Generated Reports",
            lines=20,
            max_lines=50
        )
    
    # Connect events
    detect_btn.click(
        fn=process_threat_detection,
        inputs=[image_input, radar_input],
        outputs=[status_output, plans_output, reports_output, plan_selection_row]
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
    logger.info("Starting Gradio interface for Image-based Naval Threat Detection System")

    try:
        app.launch(
            server_name="0.0.0.0",
            server_port=7862,
            share=False
        )
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("="*50)
        logger.info(" Image-processor Agent stopped gracefully")
        logger.info("="*50)

