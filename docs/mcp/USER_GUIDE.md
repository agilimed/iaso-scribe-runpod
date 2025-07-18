# IASO Medical AI Services - User Guide

## Overview

IASO Medical AI Services provide powerful medical documentation and analysis capabilities through the Model Context Protocol (MCP). Whether you need to transcribe medical dictation, generate SOAP notes, or analyze clinical cases, our services work independently or together to streamline your medical workflows.

## Quick Start

### 1. Available Services

#### **Whisper Transcription Service**
- Convert medical audio to accurate text
- Support for multiple languages
- Optimized for medical terminology

#### **Phi-4 Medical Reasoning Service**
- Generate SOAP notes from clinical text
- Create clinical summaries
- Extract medical insights
- Analyze complex cases

#### **IASO Orchestrator**
- Automatically coordinates multiple services
- Handles complete workflows end-to-end
- Intelligent service routing

### 2. Common Use Cases

#### Medical Dictation to SOAP Note
```python
# Complete workflow: Audio → Transcription → SOAP Note
result = client.call_tool("process_medical_dictation", {
    "audio_url": "https://your-audio.wav",
    "outputs": ["transcription", "soap_note", "clinical_summary"]
})
```

#### Direct SOAP Note Generation
```python
# Generate SOAP note from existing text
result = client.call_tool("generate_soap_note", {
    "text": "Patient is a 45-year-old male presenting with...",
    "include_reasoning": True
})
```

#### Clinical Summary (750 words)
```python
# Create concise summary
result = client.call_tool("create_clinical_summary", {
    "text": "Full consultation note text...",
    "max_words": 750
})
```

## Integration Methods

### Method 1: Claude Desktop

1. Add to your Claude Desktop config:
```json
{
  "mcpServers": {
    "iaso-orchestrator": {
      "command": "python",
      "args": ["/path/to/iaso-orchestrator.py"],
      "env": {
        "RUNPOD_API_KEY": "your_key"
      }
    }
  }
}
```

2. Use natural language:
- "Transcribe this medical audio and create a SOAP note"
- "Summarize this clinical consultation in 750 words"
- "Extract key medical insights from this case"

### Method 2: Python Application

```python
from mcp import Client

# Connect to IASO services
client = Client()
client.connect("iaso-orchestrator")

# Process medical dictation
result = client.call_tool("process_medical_dictation", {
    "audio_url": "consultation.wav",
    "outputs": ["transcription", "soap_note"],
    "metadata": {
        "provider": "Dr. Smith",
        "patient_id": "12345"
    }
})

print(result["results"]["soap_note"])
```

### Method 3: Conversational Analytics Integration

```python
# Use RASA for better query understanding
rasa_client = Client()
rasa_client.connect("rasa-medical-dialog")

# Extract entities from natural language query
entities = rasa_client.call_tool("extract_medical_entities", {
    "text": "Show me all diabetic patients with recent high glucose readings",
    "entity_types": ["condition", "test_type", "severity"]
})

# Use entities to enhance SQL generation
# entities["entities"] contains structured medical concepts
```

### Method 4: REST API Wrapper

```bash
# Call via HTTP endpoint
curl -X POST https://your-api.com/iaso/process \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "generate_soap_note",
    "arguments": {
      "text": "Patient presents with...",
      "include_reasoning": false
    }
  }'
```

## Detailed Examples

### Example 1: Emergency Department Documentation

```python
# ED physician dictates patient encounter
ed_workflow = {
    "tool": "process_medical_dictation",
    "arguments": {
        "audio_url": "ed-trauma-patient.wav",
        "outputs": ["transcription", "soap_note", "medical_insights"],
        "metadata": {
            "department": "Emergency",
            "priority": "urgent",
            "provider": "Dr. Johnson"
        }
    }
}

result = client.call_tool(**ed_workflow)

# Results include:
# - Accurate transcription with medical terms
# - Structured SOAP note for EMR
# - Key insights: diagnosis, urgency, disposition
```

### Example 2: Specialty Consultation

```python
# Cardiologist reviews complex case
cardio_analysis = {
    "tool": "analyze_clinical_case",
    "arguments": {
        "case_text": "72-year-old male with new-onset AFib...",
        "analysis_type": "full_analysis"
    }
}

result = client.call_tool(**cardio_analysis)

# Provides:
# - Differential diagnosis
# - Treatment recommendations
# - Risk assessment
# - Follow-up plan
```

### Example 3: Multi-Language Support

```python
# Spanish language consultation
spanish_dictation = {
    "tool": "transcribe_medical_dictation",
    "arguments": {
        "audio_url": "consulta-medica.wav",
        "language": "es",
        "speaker_info": "Dra. García, Medicina Interna"
    }
}

result = client.call_tool(**spanish_dictation)
```

### Example 4: RASA-Enhanced Query Understanding

```python
# Connect to RASA for medical dialog management
rasa_client = Client()
rasa_client.connect("rasa-medical-dialog")

# Start a symptom assessment conversation
session = rasa_client.call_tool("start_conversation", {
    "conversation_type": "symptom_check",
    "patient_id": "12345"
})

# Send patient message
response = rasa_client.call_tool("send_message", {
    "message": "I've been having severe headaches and dizziness for 3 days",
    "sender_id": session["sender_id"]
})

# Extract medical entities for analytics
entities = rasa_client.call_tool("extract_medical_entities", {
    "text": "diabetic patients with uncontrolled glucose above 200",
    "entity_types": ["condition", "severity", "lab_value"]
})

# Result includes:
# - condition: ["diabetic"]
# - severity: ["uncontrolled"]
# - lab_value: ["glucose above 200"]
```

## Output Formats

### SOAP Note Structure
```
SUBJECTIVE:
• Chief complaint and HPI
• Relevant history
• Current medications

OBJECTIVE:
• Vital signs
• Physical examination
• Lab results

ASSESSMENT:
• Primary diagnosis
• Differential diagnoses
• Clinical reasoning

PLAN:
• Immediate interventions
• Medications
• Follow-up
```

### Clinical Summary Format
- Comprehensive narrative (customizable length)
- Key findings highlighted
- Action items clearly stated
- Suitable for handoffs and referrals

### Medical Insights Structure
```json
{
  "chief_complaint": "Chest pain",
  "key_symptoms": ["substernal pain", "dyspnea"],
  "medications": [
    {"name": "Aspirin", "dose": "325mg", "route": "PO"}
  ],
  "diagnoses": ["STEMI", "Type 2 MI"],
  "urgent_concerns": ["Requires cath lab activation"],
  "follow_up": ["Cardiology consult", "Serial troponins"]
}
```

## Best Practices

### 1. Audio Quality
- Use high-quality recordings when possible
- Minimize background noise
- Speak clearly and include relevant details

### 2. Text Input
- Include all relevant clinical information
- Use standard medical terminology
- Specify context (specialty, setting)

### 3. Output Selection
- Choose only needed outputs to optimize speed
- Use `include_reasoning` for teaching scenarios
- Specify word counts for summaries

### 4. Metadata Usage
- Always include provider information
- Add encounter/patient IDs for tracking
- Specify department/specialty for context

## Troubleshooting

### Common Issues

**Slow Response Times**
- Check network connectivity
- Reduce number of requested outputs
- Use direct service calls instead of orchestrator

**Incomplete Outputs**
- Increase max_tokens for longer documents
- Ensure complete input text
- Check for special characters in input

**Authentication Errors**
- Verify RUNPOD_API_KEY is set
- Check endpoint IDs are correct
- Ensure API key has proper permissions

## Support

- Documentation: [GitHub Repository](https://github.com/your-repo)
- Issues: Report via GitHub Issues
- Contact: support@iaso-medical.ai

## Privacy & Security

- All audio is processed securely
- No patient data is stored permanently
- HIPAA-compliant infrastructure
- End-to-end encryption available