## Susceptibility Agent v1: Naval Electronic Warfare Susceptibility Analysis

An agentic AI system that analyzes electromagnetic signals from naval sensors, assesses threat levels, and recommends tactical responses to minimize detection risk. This project focuses on **Susceptibility**—avoiding being attacked or detected.

-----

## Project Overview

This system processes radar and Electronic Warfare (EW) sensor data to help ships prevent detection by hostile forces.

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

  * `emitter_threat_tool.py`: Used to look up emitter threats.
  * `em_signature_tool.py`: Used to calculate the ship's electromagnetic (EM) signature.
  * `comms_reconfig_tool.py`: Used to simulate communication system changes.

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

## Usage (Summarized)

The assessment can be run via an interactive web interface or the command line.

### Gradio Web Interface (Recommended for Demos)

Launch the interface with:

```bash
python gradio_susceptibility_v1_app.py
```

Open your browser to `http://localhost:7860`. This interface features predefined scenarios, real-time progress, and detailed reports.

### Command Line

Run an assessment programmatically with:

```bash
python src/main.py
```
