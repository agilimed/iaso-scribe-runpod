# IASO Medical Services MCP Architecture

## Overview

This implements an agentic system where Whisper and Phi-4 services can:
1. Function independently as MCP servers
2. Coordinate through an orchestration agent when needed
3. Be discovered and used by any MCP client
4. Maintain their specialized capabilities

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Clients                            │
│  (Claude Desktop, VS Code, Custom Apps, Medical Systems)    │
└─────────────┬───────────────────────────┬───────────────────┘
              │                           │
              ▼                           ▼
┌─────────────────────────┐   ┌─────────────────────────────┐
│   IASO Orchestrator     │   │    Direct Service Access    │
│   (MCP Server + Agent)  │   │                             │
└─────────┬───────────────┘   └──────────┬──────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Service Registry                      │
└─────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Whisper MCP    │  │   Phi-4 MCP     │  │  Future MCPs    │
│    Server        │  │    Server        │  │   (Lab, Rx)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ RunPod Whisper  │  │  RunPod Phi-4   │  │ Other Services  │
│    Endpoint     │  │    Endpoint      │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Key Components

### 1. Individual MCP Servers

Each service exposes MCP tools:

**Whisper MCP Server:**
- `transcribe_audio` - Convert audio to text
- `detect_language` - Identify spoken language
- `transcribe_streaming` - Real-time transcription

**Phi-4 MCP Server:**
- `generate_soap_note` - Create SOAP documentation
- `create_summary` - Medical summaries
- `extract_insights` - Clinical insights
- `analyze_symptoms` - Symptom analysis

### 2. Service Registry

Central registry for service discovery:
- Services register their capabilities
- Clients can query available services
- Health monitoring and failover

### 3. Orchestration Agent

Intelligent coordinator that:
- Understands task requirements
- Plans multi-step workflows
- Handles service composition
- Manages context between services

## Example Use Cases

### Independent Usage
```python
# Direct Phi-4 usage via MCP
client.call_tool("phi4_generate_soap_note", {
    "text": "Patient presents with...",
    "format": "structured"
})
```

### Orchestrated Usage
```python
# Agent automatically coordinates services
client.call_tool("process_medical_dictation", {
    "audio_url": "https://...",
    "outputs": ["transcription", "soap", "summary", "icd_codes"]
})
# Agent internally calls: Whisper → Phi-4 → ICD Coder
```

### Dynamic Composition
```python
# Agent discovers and uses available services
client.call_tool("analyze_patient_encounter", {
    "data": {...},
    "required_outputs": ["diagnosis", "treatment_plan", "prescriptions"]
})
# Agent finds and coordinates relevant services
```

## Benefits

1. **Flexibility**: Services work independently or together
2. **Extensibility**: Easy to add new medical services
3. **Intelligence**: Agent makes smart routing decisions
4. **Standardization**: MCP provides consistent interface
5. **Composability**: Build complex workflows from simple tools