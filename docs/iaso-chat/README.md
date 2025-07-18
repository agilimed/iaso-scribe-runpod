# IasoChat - Conversational AI Service

IasoChat is IASO's specialized conversational AI service built on RASA Open Source, designed for medical and healthcare conversations.

## Overview

IasoChat provides intelligent conversational capabilities for:
- **Medical Consultations**: Natural language understanding of patient symptoms and concerns
- **Appointment Scheduling**: Automated appointment booking and management
- **Clinical Information Gathering**: Structured data collection through conversation
- **Patient Authentication**: Secure identity verification during conversations
- **Emergency Assessment**: Automatic escalation for urgent medical situations

## Architecture

### Core Components

1. **RASA Server** (`rasa/rasa:3.6.0`)
   - Natural Language Understanding (NLU)
   - Dialogue Management
   - Response Generation
   - Intent Classification and Entity Extraction

2. **Action Server** (`iaso/rasa-actions-medical:latest`)
   - Custom medical actions
   - External API integrations
   - RunPod AI service calls (Whisper, Phi-4)
   - Clinical AI integration

3. **Redis Session Store**
   - Conversation state management
   - Session persistence
   - Scalable storage backend

4. **MCP Integration**
   - Model Context Protocol server
   - Independent service capability
   - Integration with other IASO services

### Service Integration

```
📞 Amazon Connect → 🎙️ Whisper → 🧠 IasoChat → 🏥 Clinical AI → 🗣️ Polly
```

## Deployment

### EKS Fargate Deployment

IasoChat is designed for deployment on AWS EKS with Fargate for:
- **Serverless scaling**: Pay-per-use model
- **High availability**: Multi-AZ deployment
- **Security**: Network isolation and encryption
- **Compliance**: HIPAA-ready infrastructure

### Docker Images

- **Official RASA Image**: `rasa/rasa:3.6.0`
- **Custom Actions**: `iaso/rasa-actions-medical:latest`
- **MCP Server**: `iaso/rasa-mcp:latest`

## Configuration

### Key Features

- **Medical Intent Recognition**: Specialized NLU for healthcare terminology
- **Symptom Assessment**: Structured symptom collection and analysis
- **Emergency Detection**: Automatic escalation for urgent situations
- **Patient Authentication**: Secure identity verification
- **SOAP Note Generation**: Automated clinical documentation
- **Multi-modal Integration**: Voice, text, and structured data

### Environment Variables

```bash
RUNPOD_API_KEY=your-runpod-api-key
WHISPER_ENDPOINT_ID=rntxttrdl8uv3i
PHI4_ENDPOINT_ID=tmmwa4q8ax5sg4
CLINICAL_AI_URL=http://clinical-ai-service:8002
REDIS_URL=redis://redis-service:6379
```

## Medical Conversation Flow

1. **Greeting & Authentication**
   - Welcome message
   - Patient ID verification
   - Identity confirmation

2. **Symptom Assessment**
   - Symptom collection
   - Pain level assessment
   - Medical history review

3. **Clinical Analysis**
   - Emergency assessment
   - Clinical context retrieval
   - Recommendation generation

4. **Documentation**
   - SOAP note creation
   - Clinical record updates
   - Summary generation

## Integration Points

### RunPod AI Services

- **Whisper**: Audio transcription
- **Phi-4**: Medical reasoning and SOAP note generation

### Clinical AI Services

- **Entity Extraction**: Medical concept identification
- **Terminology Search**: UMLS terminology lookup
- **Knowledge Base**: Medical knowledge integration

### Amazon Connect

- **Voice Interface**: Telephony integration
- **Audio Streaming**: Real-time audio processing
- **Session Management**: Call state handling

## Security & Compliance

- **HIPAA Compliance**: Encrypted data transmission and storage
- **Access Control**: Role-based authentication
- **Audit Logging**: Comprehensive conversation logging
- **Data Encryption**: End-to-end encryption for sensitive data

## Monitoring & Observability

- **Conversation Metrics**: Response time, intent accuracy
- **Health Checks**: Service availability monitoring
- **Error Tracking**: Exception handling and reporting
- **Performance Metrics**: Resource utilization and scaling

## Development

### Local Development

```bash
# Start services
docker-compose -f docker-compose.dev.yml up

# Train model
rasa train --config config.yml --domain domain.yml --data data/

# Test conversations
rasa shell
```

### Testing

```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/

# Load testing
python -m pytest tests/load/
```

## API Reference

### REST API

```bash
# Send message
POST /webhooks/rest/webhook
{
  "sender": "user123",
  "message": "I have a headache",
  "metadata": {
    "patient_id": "patient123",
    "authenticated": true
  }
}
```

### MCP Protocol

```bash
# Available tools
- send_message: Send message to RASA
- start_conversation: Initialize conversation
- extract_medical_entities: Extract medical entities
- analyze_conversation: Analyze conversation patterns
```

## Related Services

- **IasoScribe**: Medical transcription service
- **IasoClinical**: Clinical AI processing
- **IasoVoice**: Voice interaction orchestration
- **IasoEmbeddings**: Vector embedding service

## Documentation

- [Deployment Guide](../infrastructure/iaso-chat/deployment.md)
- [Configuration Reference](../infrastructure/iaso-chat/configuration.md)
- [API Documentation](../infrastructure/iaso-chat/api.md)
- [Integration Guide](../infrastructure/iaso-chat/integration.md)

---

**IasoChat**: Intelligent conversations for better healthcare outcomes.