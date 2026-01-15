# Threat Detection Agent v1

A multi-agent AI system for visual threat detection and response in naval operations, built with CrewAI.

## Overview

This system processes visual inputs from ship cameras and radar traces to detect, classify, and respond to threats such as drones, missiles, vessels, and aircraft. It features:

- **Computer Vision Detection**: YOLOv8-based object detection
- **Sensor Fusion**: Correlates visual detections with radar traces
- **Specialist Analysis**: Dedicated agents for different threat types
- **Tactical Planning**: Generates countermeasure plans with technical parameters
- **Human-in-the-Loop**: Commander approval before countermeasure execution
- **Realistic Simulation**: Models directed energy weapons, CIWS, and electronic warfare systems

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  COORDINATOR AGENT (Central)                                │
│  - Receives: images + JSON radar (optional)                 │
│  - Delegates to specialists based on threat type            │
│  - Prioritizes multiple threats simultaneously              │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┬──────────────┐
        ▼                 ▼                 ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────┐  ┌─────────────┐
│ VISION       │  │ DRONE        │  │ MISSILE     │  │ VESSEL      │
│ ANALYST      │  │ SPECIALIST   │  │ SPECIALIST  │  │ SPECIALIST  │
│ - YOLO       │  │ - Type       │  │ (future)    │  │ (future)    │
│ - Radar      │  │ - Swarm      │  │             │  │             │
│   Fusion     │  │ - Payload    │  │             │  │             │
└──────────────┘  └──────────────┘  └─────────────┘  └─────────────┘
        │                 │                 
        └─────────────────┴─────────────────────────────────┘
                          ▼
            ┌──────────────────────────────┐
            │  TACTICAL RESPONSE AGENT     │
            │  - Selects actuators         │
            │  - Technical parameters      │
            └──────────────────────────────┘
                          ▼
                   [HUMAN APPROVAL]
                          ▼
            ┌──────────────────────────────┐
            │  ACTUATOR EXECUTION AGENT    │
            │  - DEW (kW, freq, beam)      │
            │  - CIWS (missile type)       │
            │  - Jamming (freq, power)     │
            └──────────────────────────────┘
```

## Agents

1. **Vision Analyst Agent**: Detects objects in images using YOLO, fuses with radar data
2. **Coordinator Agent**: Prioritizes threats and delegates to specialists
3. **Drone Specialist Agent**: Analyzes drones (type, swarm, countermeasures)
4. **Tactical Response Agent**: Generates 2-3 countermeasure plans
5. **Actuator Agent**: Executes selected plan with weapon systems

## Tools

### Detection Tools
- **YOLODetectionTool**: Computer vision object detection (ultralytics YOLOv8)
- **RadarFusionTool**: Fuses visual detections with radar traces, analyzes Doppler signatures
- **NyckelDroneClassifier**: Commercial AI for precise drone type identification (11 types)

### Analysis Tools
- **DroneAnalysisTool**: Specialized drone classification and countermeasure recommendation

### Actuator Tools
- **DEWActuator**: Directed Energy Weapon (10-100 kW, 30-100 GHz)
- **CIWSActuator**: Close-In Weapon System (RAM, SeaRAM, Phalanx)
- **ElectronicJammingActuator**: C2 link jamming (400-6000 MHz)

## Installation

### Requirements
- Python 3.10-3.13
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- CUDA (optional, for GPU-accelerated YOLO)

### Setup with uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Navigate to project
cd threat-detection-agent-v1

# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies with uv
uv pip install -e .

# Create .env file
cp .env.example .env
# Edit .env and add your API keys
```

### Alternative Setup with pip

```bash
# Navigate to project
cd threat-detection-agent-v1

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Create .env file
cp .env.example .env
# Edit .env and add your API keys
```

### Environment Variables

Create a `.env` file:

```env
# LLM Provider (choose one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Nyckel Drone Classification (optional but recommended)
# Get free account at: https://www.nyckel.com/console
NYCKEL_CLIENT_ID=your-client-id
NYCKEL_CLIENT_SECRET=your-client-secret

# Optional: Logging level
LOG_LEVEL=INFO
```

## Usage

### CLI Mode

```bash
# Run with sample data
python -m src.main

# Or
python src/main.py
```

The CLI will:
1. Process sample drone swarm scenario
2. Generate 3 tactical plans
3. Prompt you to select a plan (1, 2, or 3)
4. Execute the selected countermeasures
5. Generate reports in `output/` directory

### Gradio Web Interface

```bash
python3 -m venv .venv\nsource .venv/bin/activate
uv pip install -e .\n
python gradio_images_app.py # sin el uv run
```

### Programmatic Usage

```python
from src.main import run_threat_detection

# Run threat detection
result = run_threat_detection(
    images=["path/to/image1.jpg", "path/to/image2.jpg"],
    radar_data='{"traces": [...]}',  # Optional
    hitl_callback=None  # Or provide custom callback
)

if result['success']:
    print(f"Selected plan: {result['selected_plan']}")
    print(f"Reports: {result['output_files']}")
```

### Custom HITL Callback

```python
def my_plan_selector(plans):
    # Custom logic to select plan
    # Example: always pick most aggressive
    return plans[0]['plan_id']

result = run_threat_detection(
    images=["image.jpg"],
    hitl_callback=my_plan_selector
)
```

## Input Format

### Images
Provide paths to image files:
```python
images = [
    "data/sample_threats/drone_001.jpg",
    "data/sample_threats/drone_002.jpg"
]
```

### Radar Data (Optional)
JSON format with radar traces:
```json
{
  "traces": [
    {
      "timestamp": "2025-01-15T10:25:00Z",
      "range_km": 2.5,
      "bearing_degrees": 45,
      "velocity_mps": 12,
      "doppler_frequency_hz": 45,
      "rcs_dbsm": -15,
      "band": "Ku"
    }
  ]
}
```

## Output

Generated reports in `output/` directory:

- `visual_detection_task.md`: YOLO detections and radar fusion
- `threat_coordination_task.md`: Threat prioritization and delegation
- `drone_analysis_task.md`: Detailed drone analysis
- `tactical_planning_task.md`: 2-3 countermeasure plans
- `countermeasure_execution_task.md`: Execution results

## Drone Classification

The system classifies drones into categories:

- **Micro/Mini** (< 2.5 kg): Reconnaissance, harassment → DEW, nets, jamming
- **Small Tactical** (2.5-25 kg): ISR, light payload → DEW or CIWS
- **Tactical/Strategic** (25-150 kg): Heavy payload, weapons → CIWS, missiles
- **Fixed-Wing** (5-100 kg): Long-range ISR, strike → SAM, CIWS, intercept

### Swarm Detection

The system detects drone swarms based on:
- Multiple small drones
- Similar bearings/ranges
- Coordinated approach patterns
- Doppler signatures

**Swarm countermeasures**: Area-effect DEW prioritized over kinetic

## Radar-Vision Fusion

The system uses Ku-band Doppler to detect rotating propellers:

- **Ku-band (12-18 GHz)**: Detects micro-Doppler from rotors
- **Doppler > 50 Hz**: 6-8 rotor drone (hexacopter/octocopter)
- **Doppler 30-50 Hz**: 4-6 rotor drone (quadcopter/hexacopter)
- **Doppler 20-30 Hz**: 2-4 rotor drone (small multirotor)

This helps distinguish drones from other airborne objects.

## Countermeasure Types

### Directed Energy Weapon (DEW)
- Power: 10-100 kW
- Frequency: 30-100 GHz (95 GHz optimal)
- Beam Width: 5-30°
- Duration: 0.5-10 seconds
- **Best for**: Small drones, swarms

### CIWS (Close-In Weapon System)
- Weapons: RAM, SeaRAM, Phalanx
- Range: 0.5-10 km
- Rounds: 1-10
- **Best for**: Large drones, missiles

### Electronic Jamming
- Frequency: 400-6000 MHz (2.4/5.8 GHz common)
- Power: 20-60 dBm
- Types: Barrage, spot, sweep
- **Best for**: C2 disruption, swarm coordination

## Development

### Project Structure

```
threat-detection-agent-v1/
├── config/
│   ├── agents.yaml          # Agent definitions
│   └── tasks.yaml           # Task definitions
├── data/
│   └── sample_threats/      # Sample scenarios
├── logs/                    # Log files
├── output/                  # Generated reports
├── src/
│   ├── models/
│   │   └── threat_data.py   # Pydantic models
│   ├── tools/
│   │   ├── vision_detector.py    # YOLO detection
│   │   ├── radar_fusion.py       # Sensor fusion
│   │   ├── drone_analyzer.py     # Drone analysis
│   │   └── actuators.py          # Weapon systems
│   ├── utils/
│   │   └── logger.py        # Logging config
│   ├── crew.py              # Crew definition
│   └── main.py              # Entry point
├── pyproject.toml           # Dependencies
└── README.md
```

### Adding New Threat Specialists

To add a new specialist (e.g., missile, vessel):

1. Create tool in `src/tools/`
2. Add agent definition in `config/agents.yaml`
3. Add task in `config/tasks.yaml`
4. Update `src/crew.py` to include new agent/task
5. Update coordinator to delegate to new specialist

## Limitations & Future Work

### Current Limitations
- YOLO uses pretrained COCO model (not fine-tuned for naval threats)
- Mock drone analysis (no real commercial software integration)
- Simulated actuators (no real weapon system integration)
- Single-image processing (no video stream analysis)
- Limited specialist types (drones only, no missile/vessel specialists)

### Future Enhancements
- Fine-tuned YOLO model for naval threats
- Real-time video stream processing
- Missile specialist agent
- Vessel specialist agent
- Aircraft specialist agent
- Integration with actual drone detection software
- Multi-ship coordination
- Advanced swarm behavior analysis
- Predictive threat assessment

## License

GNU General Public License (GPL) 3.0

## Author

Pablo Martínez Agulló (pablo.martinez.agullo@gmail.com)

## Acknowledgments

Built with:
- [CrewAI](https://www.crewai.com/) - Multi-agent orchestration
- [YOLOv8](https://github.com/ultralytics/ultralytics) - Object detection
- [Anthropic Claude](https://www.anthropic.com/) - LLM reasoning

<!-- 
tree -I "__init__.py|d_image_procesor-agent.egg-info|uv.lock|README.md|__pycache__|RESUMEN_PROYECTO.md"
  -->
