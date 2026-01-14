## Susceptibility Agent

**Naval Electronic Warfare Susceptibility Analysis**

An agentic AI system that analyzes electromagnetic signals from naval sensors, assesses threat levels, and recommends tactical responses to minimize detection risk. 
<!-- This project focuses on **Susceptibility**—avoiding being attacked or detected. -->
Part 1 of a 3-project naval AI series.
-----

## Project Overview

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

## Project Structure

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
├── pyproject.toml               # UV dependencies
├── .env.example                 # Environment variables template
└── README.md                    
```

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

## Installation (Summarized)

### Prerequisites

  * Python 3.9+
  * [UV](https://github.com/astral-sh/uv) package manager

### Setup

1.  **Clone the repository**: `git clone https://github.com/MartinezAgullo/naval-agentic-ai/tree/`
2.  **Go to susceptibility agent folder**: `cd susceptibility-agent-v1``
2.  **Install dependencies**: Use `uv sync .`
3.  **Configure API keys**: 
4.  **Execute**

-----

## Usage

The assessment can be run via an interactive web interface or the command line.

### Gradio Web Interface

Recomended for demos.
Launch the interface with:

```bash
uv run python gradio_susceptibility_v1_app.py
```

Open your browser to `http://localhost:7860`. This interface features predefined scenarios, real-time progress, and detailed reports.

### Command Line

Run an assessment programmatically with:

```bash
uv run python -m src.main  # Execute as a module
```

---

**Susceptibility Agent** - Minimizing naval vessel detection through intelligent electromagnetic signature management.

*Part of the Naval Agentic AI Research Series*

<!-- tree -I "__init__.py|susceptibility_agent_v1.egg-info|uv.lock|README.md|__pycache__"  -->

