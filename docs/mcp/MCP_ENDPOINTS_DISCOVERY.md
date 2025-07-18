# IASO Platform MCP Endpoints Discovery Document

## Overview

This document serves as a comprehensive catalog of all Model Context Protocol (MCP) endpoints available in the IASO platform, including both current implementations and planned future services. As the platform evolves, this document will be updated to reflect new MCP-enabled services.

## Current MCP Endpoints

### 1. Whisper Transcription Service
**Server Name:** `whisper-transcription-service`  
**Status:** ✅ Active  
**Port:** RunPod Endpoint  
**Endpoint ID:** `rntxttrdl8uv3i`

#### Available Tools:

##### `transcribe_audio`
- **Description:** Transcribe audio file to text using Whisper
- **Parameters:**
  - `audio_url` (string): URL of the audio file to transcribe
  - `audio_base64` (string): Base64 encoded audio data (alternative to URL)
  - `language` (string, optional): Language code (e.g., 'en', 'es') or null for auto-detection
  - `return_segments` (boolean, default: false): Return word-level timestamps
- **Returns:** Transcription text, detected language, duration, processing time, optional segments

##### `transcribe_medical_dictation`
- **Description:** Transcribe medical dictation with optimized settings
- **Parameters:**
  - `audio_url` (string, required): URL of the medical dictation audio
  - `speaker_info` (string, optional): Information about the speaker (e.g., 'Dr. Smith, Cardiologist')
- **Returns:** Medical transcription with segments, speaker info, and medical metadata

##### `detect_audio_language`
- **Description:** Detect the language spoken in an audio file
- **Parameters:**
  - `audio_url` (string, required): URL of the audio file
- **Returns:** Detected language code and confidence level

### 2. Phi-4 Medical Reasoning Service
**Server Name:** `phi4-medical-reasoning`  
**Status:** ✅ Active  
**Port:** RunPod Endpoint  
**Endpoint ID:** `tmmwa4q8ax5sg4`

#### Available Tools:

##### `generate_soap_note`
- **Description:** Generate a SOAP note from medical transcription or clinical notes
- **Parameters:**
  - `text` (string, required): Medical transcription or clinical notes
  - `include_reasoning` (boolean, default: false): Include step-by-step clinical reasoning
- **Returns:** Structured SOAP note with optional clinical reasoning (uses `<think>` and `<solution>` tags)

##### `create_clinical_summary`
- **Description:** Create a comprehensive clinical summary from medical documentation
- **Parameters:**
  - `text` (string, required): Medical documentation to summarize
  - `max_words` (integer, optional): Maximum words for summary (e.g., 750)
  - `focus_areas` (array of strings, optional): Specific areas to focus on
- **Returns:** Clinical summary with word count and optional focus areas

##### `extract_medical_insights`
- **Description:** Extract key medical insights and clinical findings
- **Parameters:**
  - `text` (string, required): Medical text to analyze
  - `insight_types` (array, optional): Types to extract ["symptoms", "medications", "diagnoses", "procedures", "lab_results", "risk_factors"]
- **Returns:** Structured medical insights based on requested types

##### `analyze_clinical_case`
- **Description:** Provide comprehensive analysis of a clinical case
- **Parameters:**
  - `case_text` (string, required): Clinical case description
  - `analysis_type` (enum, default: "full_analysis"): ["differential_diagnosis", "treatment_plan", "risk_assessment", "full_analysis"]
- **Returns:** Detailed clinical analysis based on type requested

##### `generate_medical_report`
- **Description:** Generate a structured medical report from clinical data
- **Parameters:**
  - `clinical_data` (string, required): Clinical data to include in report
  - `report_type` (enum, default: "consultation"): ["consultation", "discharge", "progress", "procedure"]
  - `specialty` (string, optional): Medical specialty context
- **Returns:** Formatted medical report appropriate for the specified type

### 3. RASA Medical Dialog Service
**Server Name:** `rasa-medical-dialog`  
**Status:** ✅ Active  
**Port:** 5005 (RASA Server), 5055 (Action Server)  

#### Available Tools:

##### `send_message`
- **Description:** Send a message to RASA and get response
- **Parameters:**
  - `message` (string, required): User message to process
  - `sender_id` (string, optional): Unique conversation/user ID
  - `metadata` (object, optional): Additional context (patient_id, phone_number, etc.)
- **Returns:** Bot responses, session state, and conversation tracking

##### `start_conversation`
- **Description:** Start a new medical conversation session
- **Parameters:**
  - `conversation_type` (enum, required): ["symptom_check", "appointment", "medication", "prenatal", "general"]
  - `patient_id` (string, optional): Patient identifier
  - `initial_context` (object, optional): Initial clinical context
- **Returns:** Session ID, initial message, and conversation setup

##### `get_conversation_state`
- **Description:** Get current conversation state and context
- **Parameters:**
  - `sender_id` (string, required): Conversation ID
- **Returns:** Current slots, latest message, events, and session data

##### `extract_medical_entities`
- **Description:** Extract medical entities from a conversation
- **Parameters:**
  - `text` (string, required): Text to extract entities from
  - `entity_types` (array, optional): ["symptom", "medication", "condition", "body_part", "severity"]
- **Returns:** Grouped entities by type with confidence scores

##### `trigger_action`
- **Description:** Trigger a specific RASA custom action
- **Parameters:**
  - `action` (enum, required): Available medical actions
  - `sender_id` (string, required): Conversation ID
  - `parameters` (object, optional): Additional action parameters
- **Returns:** Action execution results and slot changes

##### `analyze_conversation`
- **Description:** Analyze a completed conversation for insights
- **Parameters:**
  - `sender_id` (string, required): Conversation ID to analyze
  - `analysis_type` (enum, default: "summary"): ["summary", "entities", "intents", "sentiment", "clinical_notes"]
- **Returns:** Conversation analysis based on type requested

### 4. IASO Medical Orchestrator
**Server Name:** `iaso-medical-orchestrator`  
**Status:** ✅ Active  
**Type:** Orchestration Agent  

#### Available Tools:

##### `process_medical_dictation`
- **Description:** Process medical dictation from audio to structured documentation
- **Parameters:**
  - `audio_url` (string, required): URL of medical dictation audio
  - `outputs` (array, default: ["transcription", "soap_note"]): Desired outputs from ["transcription", "soap_note", "clinical_summary", "medical_insights"]
  - `metadata` (object, optional): Additional metadata (provider info, patient context, etc.)
- **Returns:** Complete workflow results with all requested outputs

##### `analyze_patient_encounter`
- **Description:** Comprehensive analysis of patient encounter data
- **Parameters:**
  - `encounter_data` (object, required): Patient encounter data (can include text, vitals, labs, etc.)
  - `analysis_goals` (array, optional): Specific analysis goals
- **Returns:** Multi-faceted analysis results based on goals

##### `query_service_capabilities`
- **Description:** Query available services and their capabilities
- **Parameters:**
  - `capability` (string, optional): Specific capability to search for
- **Returns:** List of available services and their capabilities

##### `execute_custom_workflow`
- **Description:** Execute a custom workflow with specified steps
- **Parameters:**
  - `inputs` (object, required): Initial input data
  - `workflow_steps` (array, required): Array of workflow steps with service, tool, and parameters
- **Returns:** Results from each workflow step

## Planned MCP Endpoints (Future Services)

### 4. IasoClinical Entity Extraction Service
**Server Name:** `iaso-clinical-entities` (Planned)  
**Status:** 🔄 Planned for MCP conversion  
**Current API:** REST on port 8002  

#### Planned Tools:
- `extract_clinical_entities` - Extract medical entities using MedCAT
- `generate_clinical_embeddings` - Create ClinicalBERT embeddings
- `calculate_medical_similarity` - Compare clinical text similarity
- `map_to_fhir` - Convert entities to FHIR resources

### 5. IasoQL Text-to-SQL Service
**Server Name:** `iasoql-text-to-sql` (Planned)  
**Status:** 🔄 Planned for MCP conversion  
**Current API:** REST on port 8008  

#### Planned Tools:
- `generate_healthcare_sql` - Convert natural language to healthcare SQL
- `optimize_fhir_query` - Optimize queries for FHIR databases
- `validate_sql_safety` - Ensure generated SQL is safe and valid
- `explain_query_logic` - Provide explanation of generated queries

### 6. Medical Terminology Service
**Server Name:** `medical-terminology` (Planned)  
**Status:** 🔄 Planned for MCP conversion  
**Current API:** REST on port 8001  

#### Planned Tools:
- `search_medical_concepts` - Search UMLS terminology
- `get_concept_details` - Get full concept information by CUI
- `map_terminology_codes` - Map between different coding systems
- `identify_clinical_terms` - NLP-based term extraction from text

### 7. BGE-M3 Embeddings Service
**Server Name:** `bge-m3-embeddings` (Planned)  
**Status:** 🔄 Planned for MCP conversion  
**Current API:** gRPC on port 50051, HTTP wrapper on port 8050  

#### Planned Tools:
- `generate_embeddings` - Create multilingual medical embeddings
- `search_similar_documents` - Find semantically similar medical texts
- `cluster_medical_concepts` - Group related medical concepts
- `cross_lingual_search` - Search across multiple languages

### 8. Template Management Service
**Server Name:** `fhir-template-manager` (Planned)  
**Status:** 🔄 Planned for MCP conversion  
**Current API:** REST on port 8003  

#### Planned Tools:
- `create_fhir_template` - Create new FHIR questionnaire templates
- `manage_templates` - List, update, delete templates
- `validate_questionnaire` - Validate FHIR questionnaire responses
- `generate_form_ui` - Generate UI components from templates

### 9. Medical Knowledge Graph Service
**Server Name:** `medical-knowledge-graph` (Planned)  
**Status:** 🔄 Planned for MCP conversion  
**Current API:** REST on port 8004  

#### Planned Tools:
- `query_medical_relationships` - Find relationships between medical concepts
- `traverse_concept_hierarchy` - Navigate medical ontologies
- `find_related_conditions` - Discover related medical conditions
- `map_treatment_pathways` - Identify treatment options for conditions

### 10. Voice Recognition Service
**Server Name:** `medical-voice-recognition` (Planned)  
**Status:** 📋 On roadmap  
**Planned Port:** 8009  

#### Planned Tools:
- `real_time_transcription` - Live medical dictation transcription
- `voice_command_recognition` - Process voice commands for EHR
- `speaker_diarization` - Identify multiple speakers in recordings
- `accent_adaptation` - Adapt to different medical professional accents

### 11. Medical Vision AI Service
**Server Name:** `medical-vision-ai` (Planned)  
**Status:** 📋 On roadmap  
**Planned Port:** 8010  

#### Planned Tools:
- `analyze_medical_images` - Process X-rays, CT scans, MRIs
- `extract_document_text` - OCR for medical documents
- `detect_abnormalities` - Identify potential issues in images
- `measure_medical_features` - Quantify medical image features

### 12. Clinical Decision Support Service
**Server Name:** `clinical-decision-support` (Planned)  
**Status:** 📋 On roadmap  

#### Planned Tools:
- `assess_drug_interactions` - Check medication interactions
- `calculate_risk_scores` - Compute clinical risk assessments
- `suggest_diagnostic_tests` - Recommend appropriate tests
- `generate_care_plans` - Create evidence-based care plans

### 13. Medical Coding Service
**Server Name:** `medical-coding-assistant` (Planned)  
**Status:** 📋 On roadmap  

#### Planned Tools:
- `suggest_icd_codes` - Recommend ICD-10/11 codes
- `suggest_cpt_codes` - Recommend CPT procedure codes
- `validate_coding_compliance` - Check coding compliance
- `optimize_billing_codes` - Optimize for accurate billing

## Integration Patterns

### Direct Service Integration
```python
# Connect to individual MCP server
client.connect("whisper-transcription-service")
result = client.call_tool("transcribe_audio", {"audio_url": "..."})
```

### Orchestrated Workflows
```python
# Use orchestrator for complex workflows
client.connect("iaso-medical-orchestrator")
result = client.call_tool("process_medical_dictation", {
    "audio_url": "...",
    "outputs": ["transcription", "soap_note", "clinical_summary"]
})
```

### Service Discovery
```python
# Find services by capability
client.connect("iaso-medical-orchestrator")
services = client.call_tool("query_service_capabilities", {
    "capability": "medical_reasoning"
})
```

### Conversational Analytics with RASA
```python
# Use RASA for enhanced query understanding
client.connect("rasa-medical-dialog")

# Extract medical entities from query
entities = client.call_tool("extract_medical_entities", {
    "text": "Show me diabetic patients with high glucose",
    "entity_types": ["condition", "test_type", "severity"]
})

# Use extracted entities for better SQL generation
enhanced_query = f"Patients with {entities['condition']} and {entities['test_type']} readings"
```

### Multi-Service Integration
```python
# Example: Voice + Dialog + Analytics
# 1. Transcribe medical query
transcription = whisper_client.call_tool("transcribe_audio", {"audio_url": "..."})

# 2. Extract entities with RASA
entities = rasa_client.call_tool("extract_medical_entities", {
    "text": transcription["transcription"]
})

# 3. Generate insights with enhanced context
insights = analytics_client.generate_query(
    text=transcription["transcription"],
    entities=entities["entities"]
)
```

## Service Categories

### 🎯 Core Services
- Whisper Transcription
- Phi-4 Medical Reasoning
- RASA Medical Dialog
- IASO Orchestrator

### 🏥 Clinical NLP Services
- Clinical Entity Extraction
- Medical Terminology
- ClinicalBERT Embeddings

### 💬 Conversational AI Services
- RASA Dialog Management
- Intent Recognition
- Entity Extraction
- Conversation Analytics

### 💾 Data & Query Services
- IasoQL Text-to-SQL
- BGE-M3 Embeddings
- Medical Knowledge Graph

### 📋 Documentation Services
- Template Management
- Medical Coding Assistant
- Clinical Decision Support

### 🎤 Multimodal Services
- Voice Recognition
- Medical Vision AI

## Status Legend
- ✅ **Active** - MCP server is implemented and operational
- 🔄 **Planned** - Service exists but MCP conversion planned
- 📋 **On roadmap** - Future service in development pipeline

## Version History
- **v1.0** (2025-07-17): Initial document with 3 active MCP services and 10 planned services
- **v1.1** (2025-07-17): Added RASA Medical Dialog as 4th active MCP service with conversational AI capabilities
- Future versions will track additions and changes to the MCP ecosystem

## Contributing
To add a new MCP service to this registry:
1. Implement the MCP server following the patterns in existing services
2. Add service details to this document
3. Update the orchestrator's ServiceRegistry if applicable
4. Submit PR with implementation and documentation

## Resources
- [MCP Specification](https://github.com/anthropics/mcp)
- [IASO Platform Documentation](../README.md)
- [MCP User Guide](USER_GUIDE.md)
- [MCP Developer Guide](DEVELOPER_GUIDE.md)