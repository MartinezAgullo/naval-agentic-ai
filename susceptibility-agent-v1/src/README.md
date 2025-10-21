# src/ - Source Code Directory

Core implementation of the Susceptibility Agent v1 system.

## Directory Structure

```
src/
├── crew.py              Crew definition with agents and tasks
├── main.py              Public API and CLI entry point
├── models/              Data models
├── tools/               Agent tools
└── utils/               Utilities
```

## Module Descriptions

### crew.py
CrewAI crew definition decorated with @CrewBase.

Contains:
- 4 agent definitions (signal intelligence, threat assessment, EW advisor, communication coordinator)
- 4 task definitions (signal processing, threat assessment, EW response, communication reconfiguration)
- Tool setup and initialization
- Crew assembly logic

Does NOT contain:
- Execution logic
- Public API
- CLI interface

### main.py
Public API and command-line interface.

Exports:
- `run_susceptibility_assessment(signal_input, active_systems)` - Main public API
- `test_with_sample_data()` - Built-in test function
- `main()` - CLI entry point

Usage:
```python
from src.main import run_susceptibility_assessment
result = run_susceptibility_assessment(signal_json, systems_list)
```

### models/
Pydantic data models for type safety and validation.

Files:
- `signal_data.py` - Models for electromagnetic signals (EmitterDetection, RadarSignalInput, ThreatLevel, EMSignature, CommunicationConfig)

### tools/
Agent tools for signal processing, threat assessment, and response coordination.

Categories:

Signal Processing Tools:
- `multimodal_tools.py` - Input type determination, radar/EW signal processing, audio transcription, document analysis

Threat Assessment Tools:
- `emitter_threat_tool.py` - Threat database lookup
- `em_signature_tool.py` - Ship electromagnetic signature calculation

Response Tools:
- `comms_reconfig_tool.py` - Communication system reconfiguration

Legacy Tools (preserved from agents-crewai-tactical-multimodal):
- `exif_tools.py` - EXIF metadata extraction
- `location_tools.py` - Geographic context

### utils/
Utility modules for cross-cutting concerns.

Files:
- `logger.py` - Centralized logging configuration using Python standard library

Provides:
- `setup_logging(level, log_file, console_level)` - Initialize logging
- `get_logger(name)` - Get module-specific logger

## Import Conventions

Public API (external use):
```python
from src.main import run_susceptibility_assessment
```

Internal imports (within src/):
```python
from src.crew import SusceptibilityCrew
from src.tools.emitter_threat_tool import EmitterThreatLookupTool
from src.models.signal_data import EmitterDetection
from src.utils.logger import get_logger
```

## Execution Entry Points

CLI:
```bash
python src/main.py
python -m src.main
```

Programmatic:
```python
from src.main import run_susceptibility_assessment
result = run_susceptibility_assessment(signal_data, active_systems)
```

Web UI (uses public API):
```bash
python gradio_susceptibility_v1_app.py
```

## Dependencies

External:
- crewai - Agent framework
- pydantic - Data validation
- gradio - Web interface (only for gradio_app.py)

Internal:
- config/agents.yaml - Agent definitions
- config/tasks.yaml - Task definitions
- config/threat_database.json - Emitter threat reference

## Output

All assessments generate markdown reports in output/:
- signal_processing_task.md
- threat_assessment_task.md
- ew_response_task.md
- communication_reconfig_task.md

## Logging

Logs written to:
- Console: INFO level
- File: logs/susceptibility_agent.log (DEBUG level)

Configure via:
```python
from src.utils.logger import setup_logging
setup_logging(level="DEBUG")
```