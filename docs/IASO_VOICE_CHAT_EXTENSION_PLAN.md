# IASO Voice & Chat Extension Plan

## Executive Summary

This document outlines the extension of IASO AI platform with three new services:
1. **IasoScribe** - Advanced ASR system using Whisper Medium for medical transcription
2. **IasoVoice** - Amazon Lex + Connect integration for automated clinical voice calls
3. **IasoChat** - Empathetic virtual chat assistant for patient support

All services will be exposed as APIs for seamless integration with third-party platforms like Heramed.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        IASO Extended Platform                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ IasoScribe  │  │  IasoVoice  │  │  IasoChat  │             │
│  │   (ASR)     │  │ (Voice Bot) │  │ (Chat Bot) │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                 │                 │                     │
│  ┌──────┴─────────────────┴─────────────────┴──────┐            │
│  │            IASO Orchestration Layer              │            │
│  └──────┬─────────────────┬─────────────────┬──────┘            │
│         │                 │                 │                     │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐            │
│  │ Clinical AI │  │   IasoQL    │  │     RAG     │            │
│  │  Service    │  │   Service   │  │   Service   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 1. IasoScribe - Medical ASR Service

### Overview
Advanced speech-to-text service optimized for medical conversations, building on top of existing Clinical AI scribing capabilities.

### Technical Architecture

```yaml
service: iaso-scribe
components:
  - whisper-runpod:
      model: openai/whisper-medium
      deployment: runpod-serverless
      gpu: A40/A100
      scaling: 0-10 instances
  
  - audio-processor:
      features:
        - Noise reduction
        - Voice activity detection
        - Audio segmentation
        - Format conversion
  
  - medical-post-processor:
      integrations:
        - Clinical AI Service (entity extraction)
        - Terminology Service (medical term validation)
        - Template Service (FHIR structuring)
```

### API Endpoints

```python
# 1. Direct Transcription
POST /api/v1/scribe/transcribe
{
  "audio": "base64_encoded_audio",
  "format": "wav|mp3|m4a",
  "language": "en",
  "medical_context": {
    "specialty": "cardiology",
    "encounter_type": "consultation"
  }
}

Response:
{
  "transcript": "Patient presents with chest pain...",
  "confidence": 0.95,
  "segments": [...],
  "medical_entities": {
    "conditions": ["chest pain"],
    "medications": [],
    "procedures": []
  }
}

# 2. Streaming Transcription
WS /api/v1/scribe/stream
{
  "type": "audio_chunk",
  "data": "base64_chunk",
  "sequence": 1
}

# 3. Structured Medical Note
POST /api/v1/scribe/generate-note
{
  "transcript_id": "abc123",
  "template": "soap|progress|discharge",
  "include_fhir": true
}

Response:
{
  "structured_note": {
    "subjective": "...",
    "objective": "...",
    "assessment": "...",
    "plan": "..."
  },
  "fhir_resources": [
    {
      "resourceType": "Encounter",
      "status": "in-progress"
    }
  ]
}
```

### RunPod Serverless Configuration

```python
# runpod_whisper_config.py
import runpod

def handler(job):
    audio_data = job["input"]["audio"]
    model_name = "openai/whisper-medium"
    
    # Load model (cached between invocations)
    model = load_whisper_model(model_name)
    
    # Process audio
    result = model.transcribe(
        audio_data,
        language="en",
        task="transcribe",
        initial_prompt="Medical consultation transcript:"
    )
    
    # Post-process for medical terms
    enhanced_result = medical_postprocess(result)
    
    return {"transcript": enhanced_result}

runpod.serverless.start({
    "handler": handler,
    "model_cache": True,
    "max_workers": 4
})
```

### Integration with Existing IASO

```python
# Enhanced scribing pipeline
class IasoScribePipeline:
    def __init__(self):
        self.whisper_client = RunPodWhisperClient()
        self.clinical_ai = ClinicalAIClient()
        self.template_service = TemplateServiceClient()
    
    async def process_audio(self, audio_data, context):
        # Step 1: Transcribe with Whisper
        transcript = await self.whisper_client.transcribe(audio_data)
        
        # Step 2: Extract medical entities
        entities = await self.clinical_ai.extract_entities(transcript)
        
        # Step 3: Generate structured note
        structured_note = await self.template_service.generate_note(
            transcript=transcript,
            entities=entities,
            template_type=context.get("template", "soap")
        )
        
        return {
            "transcript": transcript,
            "entities": entities,
            "structured_note": structured_note
        }
```

## 2. IasoVoice - Clinical Voice Bot Service

### Overview
Automated voice calling system for patient outreach, appointment reminders, and clinical assessments using Amazon Lex + Connect.

### Technical Architecture

```yaml
service: iaso-voice
components:
  - amazon-connect:
      contact_flows:
        - appointment_reminder
        - medication_adherence
        - clinical_assessment
        - emergency_triage
  
  - amazon-lex:
      bots:
        - maternal_health_bot
        - chronic_care_bot
        - appointment_bot
      
  - orchestration-service:
      features:
        - Call scheduling
        - Response processing
        - Clinical flag generation
        - Care plan updates
```

### Use Case: Maternal Health Outreach

```python
# Lex Bot Definition
maternal_health_bot = {
    "name": "MaternalHealthAssessment",
    "intents": [
        {
            "name": "AssessPainLevel",
            "sampleUtterances": [
                "I have {PainLevel} pain",
                "My pain is {PainLevel}",
                "{PainLevel}"
            ],
            "slots": [{
                "name": "PainLevel",
                "type": "AMAZON.NUMBER",
                "prompt": "On a scale of 1 to 10, how would you rate your pain today?"
            }]
        },
        {
            "name": "CheckBabyMovement",
            "sampleUtterances": [
                "{YesNo}",
                "The baby {MovementDescription}"
            ],
            "slots": [{
                "name": "YesNo",
                "type": "AMAZON.YesNoIntent",
                "prompt": "Have you felt your baby move in the last hour?"
            }]
        }
    ]
}

# Connect Contact Flow
class MaternalHealthFlow:
    def __init__(self):
        self.connect_client = boto3.client('connect')
        self.lex_client = boto3.client('lexv2-runtime')
    
    async def initiate_call(self, patient_id, phone_number):
        # Get patient context from IASO
        patient_context = await self.get_patient_context(patient_id)
        
        # Start outbound call
        response = self.connect_client.start_outbound_voice_contact(
            DestinationPhoneNumber=phone_number,
            ContactFlowId='maternal-health-flow-id',
            InstanceId='connect-instance-id',
            Attributes={
                'patientId': patient_id,
                'riskLevel': patient_context['risk_level'],
                'gestationalWeek': patient_context['gestational_week']
            }
        )
        
        return response['ContactId']
    
    async def process_responses(self, contact_id, responses):
        # Extract clinical data
        clinical_data = {
            'pain_level': responses.get('PainLevel'),
            'baby_movement': responses.get('BabyMovement'),
            'symptoms': self.extract_symptoms(responses)
        }
        
        # Update care plan via IASO
        if clinical_data['pain_level'] > 7:
            await self.create_clinical_flag(
                patient_id=responses['patientId'],
                flag_type='HIGH_PAIN',
                severity='urgent'
            )
        
        # Store in FHIR format
        observation = self.create_fhir_observation(clinical_data)
        await self.store_observation(observation)
```

### API Endpoints

```python
# 1. Schedule Voice Call
POST /api/v1/voice/schedule-call
{
  "patient_id": "patient123",
  "phone_number": "+1234567890",
  "call_type": "maternal_assessment",
  "scheduled_time": "2024-01-15T10:00:00Z",
  "context": {
    "gestational_week": 32,
    "risk_factors": ["hypertension", "diabetes"]
  }
}

# 2. Get Call Results
GET /api/v1/voice/call-results/{call_id}

Response:
{
  "call_id": "call123",
  "status": "completed",
  "duration": 180,
  "responses": {
    "pain_level": 3,
    "baby_movement": true,
    "additional_symptoms": ["swelling", "headache"]
  },
  "clinical_flags": [
    {
      "type": "MONITOR_SWELLING",
      "severity": "moderate"
    }
  ],
  "fhir_resources": [...]
}

# 3. Bulk Campaign
POST /api/v1/voice/campaign
{
  "campaign_type": "appointment_reminder",
  "target_criteria": {
    "appointment_date": "tomorrow",
    "clinic": "maternal_health"
  },
  "message_template": "reminder_v1"
}
```

### Integration with IASO Clinical AI

```python
class VoiceResponseProcessor:
    def __init__(self):
        self.clinical_ai = ClinicalAIClient()
        self.iasoql = IasoQLClient()
        
    async def process_voice_response(self, transcript, context):
        # Extract medical entities from voice response
        entities = await self.clinical_ai.extract_entities(transcript)
        
        # Generate insights
        if "pain" in entities['symptoms']:
            # Query for similar cases
            similar_cases_query = f"""
                Find patients with similar pain symptoms 
                in gestational week {context['gestational_week']}
            """
            insights = await self.iasoql.query(similar_cases_query)
        
        # Create care recommendations
        recommendations = await self.generate_recommendations(
            entities, context, insights
        )
        
        return recommendations
```

## 3. IasoChat - Empathetic Virtual Assistant

### Overview
AI-powered chat assistant providing 24/7 patient support with empathetic responses, clinical guidance, and mental health support.

### Technical Architecture

```yaml
service: iaso-chat
components:
  - conversation-engine:
      model: gpt-4-turbo / claude-3
      fine-tuning: healthcare-empathy
      context-window: 128k
  
  - emotion-detection:
      features:
        - Sentiment analysis
        - Urgency detection
        - Mental health flags
  
  - content-recommendation:
      types:
        - Educational videos
        - Relaxation music
        - Breathing exercises
        - Support group contacts
  
  - escalation-engine:
      triggers:
        - Emergency keywords
        - High distress scores
        - Clinical red flags
```

### Empathetic Response Framework

```python
class EmpathyEngine:
    def __init__(self):
        self.llm = LLMClient(model="gpt-4-turbo")
        self.emotion_detector = EmotionDetector()
        self.clinical_ai = ClinicalAIClient()
    
    async def generate_response(self, message, context):
        # Detect emotional state
        emotion = await self.emotion_detector.analyze(message)
        
        # Extract clinical concerns
        clinical_entities = await self.clinical_ai.extract_entities(message)
        
        # Build empathetic prompt
        prompt = f"""
        You are a compassionate healthcare assistant supporting a {context['patient_type']} patient.
        
        Patient message: {message}
        Emotional state: {emotion['state']} (confidence: {emotion['confidence']})
        Clinical concerns: {clinical_entities}
        
        Respond with:
        1. Acknowledge their feelings
        2. Provide gentle, supportive guidance
        3. Suggest relevant resources if appropriate
        4. Know when to escalate to human care
        
        Previous context: {context['conversation_history'][-3:]}
        """
        
        response = await self.llm.generate(prompt)
        
        # Add recommendations if needed
        if emotion['state'] in ['anxious', 'stressed']:
            response['recommendations'] = await self.get_calming_resources()
        
        return response
```

### API Endpoints

```python
# 1. Start Chat Session
POST /api/v1/chat/start
{
  "patient_id": "patient123",
  "context": {
    "condition": "pregnancy",
    "week": 28,
    "concerns": ["first_time_mother", "anxiety"]
  }
}

Response:
{
  "session_id": "chat123",
  "welcome_message": "Hello! I'm here to support you through your pregnancy journey...",
  "suggested_topics": [
    "Common symptoms at 28 weeks",
    "Preparing for delivery",
    "Managing pregnancy anxiety"
  ]
}

# 2. Send Message
POST /api/v1/chat/message
{
  "session_id": "chat123",
  "message": "I'm feeling really anxious about the delivery",
  "timestamp": "2024-01-15T10:00:00Z"
}

Response:
{
  "response": "I understand delivery can feel overwhelming, especially for first-time mothers...",
  "emotion_detected": "anxious",
  "recommendations": [
    {
      "type": "video",
      "title": "Breathing Techniques for Labor",
      "url": "..."
    },
    {
      "type": "audio",
      "title": "Calming Pregnancy Meditation",
      "url": "..."
    }
  ],
  "escalation_needed": false
}

# 3. Emergency Escalation
POST /api/v1/chat/escalate
{
  "session_id": "chat123",
  "reason": "severe_symptoms",
  "urgency": "high"
}
```

### Mental Health Support Features

```python
class MentalHealthSupport:
    def __init__(self):
        self.content_db = ContentDatabase()
        self.escalation_service = EscalationService()
    
    async def provide_support(self, emotional_state, context):
        support_package = {
            "immediate_techniques": [],
            "resources": [],
            "human_support": None
        }
        
        if emotional_state == "panic":
            support_package["immediate_techniques"] = [
                {
                    "type": "breathing_exercise",
                    "title": "4-7-8 Breathing Technique",
                    "steps": [
                        "Breathe in for 4 counts",
                        "Hold for 7 counts",
                        "Exhale for 8 counts"
                    ],
                    "audio_guide": "url_to_audio"
                }
            ]
            
            # Check if human intervention needed
            if context['panic_frequency'] > 3:
                support_package["human_support"] = {
                    "recommended": True,
                    "type": "mental_health_professional",
                    "availability": "immediate"
                }
        
        elif emotional_state == "lonely":
            support_package["resources"] = [
                {
                    "type": "support_group",
                    "title": "New Mothers Support Circle",
                    "next_session": "Tomorrow 2 PM",
                    "join_link": "..."
                },
                {
                    "type": "hotline",
                    "title": "24/7 Maternal Support Line",
                    "number": "1-800-XXX-XXXX"
                }
            ]
        
        return support_package
```

## 4. Unified API Gateway

### Architecture

```python
# api_gateway_v4_voice_chat.py
class IasoExtendedGateway:
    def __init__(self):
        self.scribe = IasoScribeService()
        self.voice = IasoVoiceService()
        self.chat = IasoChatService()
        self.clinical = ClinicalAIService()
        self.rag = RAGService()
    
    @app.post("/api/v1/unified/process")
    async def unified_process(request: UnifiedRequest):
        """
        Single endpoint for all IASO services
        """
        results = {}
        
        # Process based on input type
        if request.audio_data:
            # Transcribe audio
            transcript = await self.scribe.transcribe(request.audio_data)
            results['transcript'] = transcript
            
            # Extract clinical entities
            entities = await self.clinical.extract_entities(transcript)
            results['entities'] = entities
        
        if request.schedule_call:
            # Schedule voice outreach
            call_id = await self.voice.schedule_call(
                patient_id=request.patient_id,
                call_type=request.call_type
            )
            results['call_scheduled'] = call_id
        
        if request.chat_message:
            # Process chat with empathy
            chat_response = await self.chat.respond(
                message=request.chat_message,
                session_id=request.session_id
            )
            results['chat_response'] = chat_response
        
        # Apply RAG if needed
        if request.enable_rag:
            context = await self.rag.get_relevant_context(
                query=request.query or transcript or request.chat_message
            )
            results['rag_context'] = context
        
        return results
```

### Integration Examples for Third-Party Apps

```python
# Example: Heramed Integration
class HeramedIASOClient:
    def __init__(self, api_key):
        self.client = IASOClient(
            base_url="https://api.iaso-health.com",
            api_key=api_key
        )
    
    async def process_prenatal_visit(self, audio_recording):
        # 1. Transcribe consultation
        result = await self.client.scribe.transcribe(
            audio=audio_recording,
            medical_context={
                "specialty": "obstetrics",
                "visit_type": "prenatal_checkup"
            }
        )
        
        # 2. Generate structured note
        note = await self.client.scribe.generate_note(
            transcript_id=result['transcript_id'],
            template="prenatal_visit"
        )
        
        # 3. Schedule follow-up if needed
        if note['risk_factors']:
            await self.client.voice.schedule_call(
                patient_id=patient_id,
                call_type="high_risk_followup",
                scheduled_time="+2days"
            )
        
        return note
    
    async def provide_continuous_support(self, patient_id):
        # 1. Start empathetic chat
        session = await self.client.chat.start_session(
            patient_id=patient_id,
            context={"trimester": 3, "concerns": ["first_baby"]}
        )
        
        # 2. Enable 24/7 support
        await self.client.chat.enable_notifications(
            session_id=session['id'],
            channels=["sms", "app_push"]
        )
        
        return session
```

## 5. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
1. Set up RunPod account and deploy Whisper Medium
2. Create IasoScribe service with basic transcription
3. Integrate with existing Clinical AI for entity extraction
4. Deploy API endpoints and test with sample audio

### Phase 2: Voice Integration (Weeks 5-8)
1. Set up Amazon Connect instance
2. Create Lex bots for maternal health and appointments
3. Build contact flows for outbound calls
4. Integrate with IASO clinical services
5. Test with pilot group of patients

### Phase 3: Chat Assistant (Weeks 9-12)
1. Fine-tune LLM for healthcare empathy
2. Build emotion detection system
3. Create content recommendation engine
4. Implement escalation logic
5. Deploy chat API and WebSocket support

### Phase 4: Integration & Testing (Weeks 13-16)
1. Create unified API gateway
2. Build SDKs for Python, JavaScript, Java
3. Create integration guides and examples
4. Partner testing with Heramed
5. Performance optimization and scaling

## 6. Security & Compliance

### HIPAA Compliance
- All audio stored encrypted at rest
- PHI isolation in separate databases
- Audit logs for all API calls
- BAA agreements with RunPod, AWS

### Data Flow Security
```
Audio → Encrypted Upload → RunPod (transient) → Transcript → Clinical AI → Encrypted Storage
         ↓                                         ↓                        ↓
     S3 Encryption                          De-identified          FHIR Resources
```

### Access Control
```python
# Role-based access
ROLES = {
    "provider": ["transcribe", "view_notes", "schedule_calls"],
    "patient": ["chat", "view_own_records", "receive_calls"],
    "admin": ["all_permissions", "view_analytics"]
}
```

## 7. Monitoring & Analytics

### Key Metrics
1. **IasoScribe**
   - Transcription accuracy (WER)
   - Processing time per minute of audio
   - Medical term recognition rate

2. **IasoVoice**
   - Call completion rate
   - Patient engagement score
   - Clinical flag generation accuracy

3. **IasoChat**
   - Response satisfaction rating
   - Escalation rate
   - Mental health support effectiveness

### Dashboard
```python
# Real-time monitoring
GET /api/v1/analytics/dashboard

{
  "services": {
    "scribe": {
      "requests_today": 1523,
      "avg_accuracy": 0.94,
      "avg_latency_ms": 2300
    },
    "voice": {
      "calls_completed": 234,
      "avg_duration_seconds": 180,
      "clinical_flags_generated": 45
    },
    "chat": {
      "active_sessions": 89,
      "messages_processed": 3421,
      "escalations": 12
    }
  }
}
```

## 8. Cost Optimization

### RunPod Serverless Pricing
- Whisper Medium: ~$0.00025 per second of audio
- Auto-scaling: 0 to 10 instances
- Cold start: ~5 seconds (mitigated by keep-warm)

### Amazon Services
- Connect: $0.018 per minute
- Lex: $0.00075 per text request
- Optimizations: Batch processing, caching common responses

### LLM Costs
- GPT-4 Turbo: ~$0.01 per 1K tokens
- Optimization: Use smaller models for emotion detection
- Cache empathetic responses for common scenarios

## Next Steps

1. **Approval**: Review and approve the architecture
2. **POC**: Build IasoScribe MVP with Heramed
3. **Pilot**: Test IasoVoice with 10 high-risk mothers
4. **Iterate**: Refine based on feedback
5. **Scale**: Full deployment across all services

This extended IASO platform will provide comprehensive voice and chat capabilities while leveraging existing clinical AI services for maximum value delivery.