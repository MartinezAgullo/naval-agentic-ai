## Agent Workflow
```
┌─────────────────────────────────────────────────────────────────────┐
│                         INPUT: SIGNAL DATA                          │
│  (Radar detections, EW signals, electromagnetic environment data)   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 1: SIGNAL INTELLIGENCE SPECIALIST                            │
│  ────────────────────────────────────────────────────────────────   │
│  Role: Process and classify electromagnetic signals                 │
│                                                                     │
│  Tools Used:                                                        │
│    • InputTypeDeterminerTool                                        │
│    • RadarSignalProcessor                                           │
│    • EWSignalProcessor                                              │
│                                                                     │
│  Output: Signal Intelligence Report                                 │
│    - List of detected emitters (frequency, power, bearing, range)   │
│    - Emitter classifications (Early Warning, Fire Control, etc.)    │
│    - Critical detections flagged                                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 2: THREAT ASSESSMENT ANALYST                                 │
│  ────────────────────────────────────────────────────────────────   │
│  Role: Evaluate threat level and detection probability              │
│                                                                     │
│  Tools Used:                                                        │
│    • EmitterThreatLookupTool (queries threat database)              │
│    • EMSignatureCalculator (calculates own ship signature)          │
│                                                                     │
│  Output: Threat Assessment Report                                   │
│    - Threat scores (0-100) for each emitter                         │
│    - Detection probability for own ship                             │
│    - Overall threat level (LOW/MEDIUM/HIGH/CRITICAL)                │
│    - Own ship detectability range                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 3: ELECTRONIC WARFARE ADVISOR                                │
│  ────────────────────────────────────────────────────────────────   │
│  Role: Recommend tactical EW response                               │
│                                                                     │
│  Decision Logic:                                                    │
│    IF threat CRITICAL OR detection prob >80%                        │
│      → RECOMMEND: Activate stealth mode immediately                 │
│    ELSE IF threat HIGH OR detection prob 60-80%                     │
│      → RECOMMEND: Prepare for stealth, increase vigilance           │
│    ELSE                                                             │
│      → RECOMMEND: Maintain posture, continue monitoring             │
│                                                                     │
│  Output: EW Response Recommendation                                 │
│    - Action: ACTIVATE STEALTH MODE / MAINTAIN POSTURE               │
│    - Justification based on threat assessment                       │
│    - Emission control measures to apply                             │
│    - Countermeasure preparations                                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────┴────────┐
                    │  Decision Point  │
                    │ Stealth Mode?    │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
           YES  │                         │  NO
                │                         │
                ▼                         ▼
┌──────────────────────────┐    ┌────────────────────────┐
│  AGENT 4: COMMS          │    │  AGENT 4: COMMS        │
│  COORDINATOR             │    │  COORDINATOR           │
│  ──────────────────────  │    │  ────────────────────  │
│  Action: Execute         │    │  Action: Report no     │
│  Reconfiguration         │    │  changes needed        │
│                          │    │                        │
│  Tool Used:              │    │  Status: Normal        │
│    • CommsReconfigTool   │    │  operations maintained │
│                          │    │                        │
│  Output:                 │    │  Output:               │
│    - Channels modified   │    │    - All channels      │
│    - Frequency hopping   │    │      operational       │
│      enabled             │    │    - Standard config   │
│    - Enhanced encryption │    │                        │
│    - Power reduction     │    │                        │
│      (if needed)         │    │                        │
└──────────────┬───────────┘    └───────────┬────────────┘
               │                            │
               └────────────┬───────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    OUTPUTS: 4 MARKDOWN REPORTS                      │
│  ────────────────────────────────────────────────────────────────   │
│  1. signal_processing_task.md - Signal intelligence                 │
│  2. threat_assessment_task.md - Threat analysis                     │
│  3. ew_response_task.md - Tactical recommendations                  │
│  4. communication_reconfig_task.md - Communication changes          │
│                                                                     │
│  Stored in: output/                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Characteristics

**Sequential Processing:** Each agent builds upon the previous agent's analysis.

**Tool-Based Architecture:** Agents use specialized tools rather than hardcoded logic.

**Decision-Driven Flow:** The workflow adapts based on threat level assessment.

**Human-in-the-Loop Ready:** Although automated in demo, designed for commander validation.

**Comprehensive Output:** Multiple reports provide different perspectives for tactical decision-making.