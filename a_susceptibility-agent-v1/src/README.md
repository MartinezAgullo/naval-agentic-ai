## Susceptibility Agent v1: Naval Electronic Warfare Susceptibility Analysis

An agentic AI system that analyzes electromagnetic signals from naval sensors, assesses threat levels, and recommends tactical responses to minimize detection risk. This project focuses on **Susceptibility**—avoiding being attacked or detected.

-----

## Project Overview

This system processes radar and Electronic Warfare (EW) sensor data to help ships prevent detection by hostile forces.

```bash
susceptibility-agent-v1/
├── config/
│   ├── agents.yaml              # 4 agent definitions (signal, threat, EW, comms)
│   ├── tasks.yaml               # 4 sequential task definitions
│   └── threat_database.json     # 13 emitter types with threat scores
│
├── data/
│   └── sample_signals/          # Test signal data (JSON format)
│
├── logs/                        # Application logs (auto-generated)
│
├── output/                      # Generated assessment reports (auto-generated)
│
├── src/
│   ├── crew.py                  # CrewAI crew definition (@CrewBase)
│   ├── main.py                  # Public API and CLI entry point
│   │
│   ├── models/
│   │   └── signal_data.py       # Pydantic models for signal data
│   │
│   ├── tools/                   # Agent tools (8 total)
│   │   ├── multimodal_tools.py  # Signal processors + legacy tools
│   │   ├── emitter_threat_tool.py    # Threat database lookup
│   │   ├── em_signature_tool.py      # EM signature calculator
│   │   ├── comms_reconfig_tool.py    # Communication reconfiguration
│   │   ├── exif_tools.py        # EXIF metadata extraction (preserved)
│   │   └── location_tools.py    # Geographic context (preserved)
│   │
│   └── utils/
│       └── logger.py            # Centralized logging (Python stdlib)
│
├── gradio_susceptibility_v1_app.py   # Web interface (uses main.py API)
│
├── pyproject.toml               # UV dependencies and project metadata
└── README.md                    # This file
```

-----

## AI Agents

The system uses 4 specialized agents working sequentially to perform the analysis:

1.  **Signal Intelligence Agent**
      * Processes radar/ESM/ELINT sensor data.
      * Classifies detected electromagnetic emitters and extracts technical parameters (frequency, power, bearing, range).
2.  **Threat Assessment Agent**
      * Queries a threat database for emitter capabilities.
      * Calculates detection probability, assigns threat scores (0-100), and categorizes threats (LOW/MEDIUM/HIGH/CRITICAL).
3.  **Electronic Warfare Advisor Agent**
      * Recommends tactical EW responses based on the threat level.
      * Advises on stealth mode activation and suggests Emission Control (EMCON) procedures and countermeasures.
4.  **Communication Coordinator Agent**
      * Executes communication system reconfigurations and implements EMCON procedures when stealth mode is activated.
      * Manages frequency hopping and encryption upgrades to maintain critical command/control connectivity.

-----

## Tools & Framework

This project leverages the **CrewAI framework** and reuses components from the [`agents-crewai-tactical-multimodal`](https://github.com/MartinezAgullo/agents-crewai-tactical-multimodal/tree/main/src/tactical/tools) project, while introducing specialized tools for naval EW analysis.

**Reused & Upgraded Tools (from `agents-crewai-tactical-multimodal`):**

  * `multimodal_tools.py`: Methods have been **upgraded** to process radar and electronic-warfare inputs.
  * `exif_tools.py`
  * `location_tools.py`

**New Specific Tools:**
  * `comms_reconfig_tool.py`: Used to simulate communication system changes.
  * `em_signature_tool.py`: Used to calculate the ship's electromagnetic (EM) signature.
  * `emitter_threat_tool`: Queries threat database to assess risk level of detected electromagnetic emitters.

-----

## Installation

### Prerequisites

  * Python 3.9+
  * [UV](https://github.com/astral-sh/uv) package manager

### Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/MartinezAgullo/naval-agentic-ai/
    cd naval-agentic-ai/susceptibility-agent-v1
    ```

2.  **Install dependencies**
    ```bash
    uv sync
    ```

3.  **Configure API keys**
    
    Create a `.env` file in the project root directory:
    
    ```bash
    touch .env
    ```
    
    Add your API key to the `.env` file (choose one):
    
    ```bash
    # For OpenAI (GPT models)
    OPENAI_API_KEY=sk-proj-your_openai_key_here
    
    # OR for Anthropic (Claude models)
    ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here
    ```
    
    **Note**: At least one API key is required. The system will use whichever key is provided.

-----

## Usage

The assessment can be run via an interactive web interface or the command line.

### Method 1: Gradio Web Interface (Recommended for Demos)

Launch the [gradio](https://www.gradio.app/) interface with:

```bash
uv run python gradio_susceptibility_v1_app.py
```

Open your browser to **http://localhost:7860**

#### Quick Start Guide

**1. Load a Predefined Scenario**

- Select **"Scenario 3: High Threat - Fire Control Radar"** from the dropdown
- Click **"📥 Load Scenario"**
- Click **"🚀 Run Assessment"**
- Wait approximately 30 seconds for processing
- Review the 4 tabs with detailed reports

**2. Available Scenarios**

- **Scenario 1**: Low Threat (civilian vessels)
- **Scenario 2**: Medium Threat (distant military radar)
- **Scenario 3**: High Threat (fire control radar) ← **Recommended for first test**
- **Scenario 4**: Critical Threat (active jamming attack)

**3. Custom Input (Advanced)**

You can manually edit the JSON in the signal input area to create custom scenarios with your own:
- Emitter types
- Frequencies
- Power levels
- Bearings and ranges

#### Expected Interface

The Gradio interface provides:

- **Inputs Section**
  - Scenario dropdown selector
  - Load button to populate fields
  - Signal data text area (JSON format)
  - Active systems input (comma-separated)

- **Run Button**
  - Large "🚀 Run Assessment" button
  - Status indicator during processing

- **Output Tabs** (4 reports)
  1. **📡 Signal Intelligence**: Raw emitter detections and classifications
  2. **⚠️ Threat Assessment**: Risk scores and detection probabilities
  3. **🛡️ EW Response**: Tactical recommendations and stealth mode decisions
  4. **📞 Communications**: Communication reconfiguration details

### Method 2: Command Line

Run the built-in test scenario:

```bash
uv run python -m src.main
```

This executes a predefined test with sample radar detections and generates reports in `output/`.

<!-- ### Method 3: Programmatic API
❌ NO es una API REST
El código actual NO expone una API HTTP/REST. Es solo una función Python que puedes llamar dentro del mismo proceso Python.

Use the public API in your own code:

```python
from src.main import run_susceptibility_assessment
import json

# Prepare signal data
signal_data = {
    "sensor_type": "radar",
    "detections": [
        {
            "emitter_id": "E-001",
            "emitter_type": "radar",
            "frequency_mhz": 9500.0,
            "power_dbm": 68.0,
            "classification": "Fire Control Radar"
        }
    ]
}

# Run assessment
result = run_susceptibility_assessment(
    signal_input=json.dumps(signal_data),
    active_systems=["radar", "communications"]
)

# Check results
if result['success']:
    print(f"Reports generated: {result['output_files']}") -->
```

-----

## Output Files

All assessments generate 4 markdown reports in the `output/` directory:

1. `signal_processing_task.md` - Signal intelligence report
2. `threat_assessment_task.md` - Threat analysis with risk scores
3. `ew_response_task.md` - Tactical recommendations
4. `communication_reconfig_task.md` - Communication changes (if stealth mode activated)

-----

## Logging

Application logs are written to:
- **Console**: INFO level (color-coded)
- **File**: `logs/susceptibility_agent.log` (DEBUG level with full details)

-----

## Signal Data Format

Input signal data must be in JSON format:

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

-----

## Troubleshooting

**Port already in use (Gradio)**
```bash
# Use a different port
uv run python gradio_susceptibility_v1_app.py
# Edit the file and change server_port=7860 to server_port=7861
```

**API Key not found**
- Ensure `.env` file exists in project root
- Verify the API key format (starts with `sk-ant-` for Anthropic or `sk-proj-` for OpenAI)

**Import errors**
```bash
# Run as module
uv run python -m src.main
```

-----

## Development

### Project Structure

- `src/crew.py` - Defines the CrewAI crew structure (agents, tasks, tools)
- `src/main.py` - Public API and CLI entry point
- `gradio_susceptibility_v1_app.py` - Web interface (uses main.py API)

### Adding New Emitter Types

Edit `config/threat_database.json` and add entries with:
- `threat_score` (0-100)
- `category` (low/medium/high/critical)
- `detection_probability` (0.0-1.0)
- `recommended_action` (text)

-----

## References

- **CrewAI Framework**: https://docs.crewai.com/
- **Original Multimodal Project**: https://github.com/MartinezAgullo/agents-crewai-tactical-multimodal

-----

## License

[Your License Here]

-----

## Author

Created as part of naval agentic AI demonstration for EW applications.