# IasoVoice Orchestrator Architecture

## Overview

IasoVoice is a comprehensive voice-based healthcare communication system that orchestrates multiple AI services to enable natural medical conversations over phone calls. It combines telephony infrastructure with advanced AI capabilities for speech recognition, dialog management, clinical intelligence, and empathetic voice synthesis.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Phone Network                               │
│                     (Incoming/Outgoing Calls)                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────────┐
│                      Amazon Connect                                  │
│  • Phone number management                                           │
│  • Call routing and queuing                                          │
│  • Recording management                                              │
│  • Contact flows                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │ Audio Stream (WebSocket)
┌────────────────────────────┴────────────────────────────────────────┐
│                   IasoVoice Orchestrator                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  Core Components                              │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │ • Audio Buffer Manager - Handles streaming audio chunks      │   │
│  │ • Session Manager - Maintains conversation state             │   │
│  │ • Pipeline Coordinator - Orchestrates service calls          │   │
│  │ • Error Handler - Fallback and retry logic                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────┬───────────┬───────────┬───────────┬──────────────────┘
              │           │           │           │
    ┌─────────┴───┐ ┌─────┴───┐ ┌────┴────┐ ┌───┴──────┐
    │  Whisper    │ │  RASA   │ │Clinical │ │  Polly   │
    │   (STT)     │ │(Dialog) │ │   AI    │ │  (TTS)   │
    └─────────────┘ └─────────┘ └─────────┘ └──────────┘
```

## Component Details

### 1. Amazon Connect Integration

**Purpose**: Handles telephony infrastructure and call management

**Key Features**:
- Phone number provisioning and management
- Intelligent call routing based on caller data
- Queue management with priority handling
- Call recording with secure S3 storage
- Real-time metrics and monitoring

**Integration Points**:
```python
class ConnectIntegration:
    def __init__(self):
        self.connect_client = boto3.client('connect')
        self.instance_id = os.getenv('CONNECT_INSTANCE_ID')
    
    async def handle_incoming_call(self, contact_id: str):
        # Get caller information
        # Route to appropriate flow
        # Start audio streaming
```

### 2. IasoVoice Orchestrator Service

**Purpose**: Central coordination hub for all voice interactions

**Core Modules**:

#### Audio Buffer Manager
```python
class AudioBufferManager:
    """Manages streaming audio with intelligent chunking"""
    
    def __init__(self):
        self.buffer = bytearray()
        self.chunk_size = 16000  # 1 second at 16kHz
        self.silence_threshold = 500  # ms
    
    async def add_audio(self, chunk: bytes):
        # Buffer incoming audio
        # Detect speech boundaries
        # Trigger processing when ready
```

#### Session Manager
```python
class SessionManager:
    """Maintains conversation context and state"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
    
    class ConversationSession:
        call_id: str
        patient_id: Optional[str]
        conversation_history: List[Turn]
        clinical_context: Dict[str, Any]
        current_flow: str
        metadata: Dict[str, Any]
```

#### Pipeline Coordinator
```python
class PipelineCoordinator:
    """Orchestrates the STT → Dialog → TTS pipeline"""
    
    async def process_audio_turn(self, audio: bytes, session: ConversationSession):
        # 1. Send to Whisper for transcription
        text = await self.whisper_client.transcribe(audio)
        
        # 2. Send to RASA with context
        response = await self.rasa_client.process(text, session.conversation_history)
        
        # 3. Enhance with Clinical AI if needed
        if response.needs_clinical_data:
            clinical_data = await self.clinical_ai.get_context(session.patient_id)
            response = await self.rasa_client.process_with_context(text, clinical_data)
        
        # 4. Generate speech with Polly
        audio_response = await self.polly_client.synthesize(response.text, voice='Joanna')
        
        return audio_response
```

### 3. Whisper Integration (Speech-to-Text)

**Deployment**: RunPod Serverless (Existing)

**Configuration**:
```python
class WhisperClient:
    def __init__(self):
        self.endpoint_id = "rntxttrdl8uv3i"
        self.api_key = os.getenv("RUNPOD_API_KEY")
    
    async def transcribe(self, audio: bytes) -> str:
        # Convert audio to base64
        # Call RunPod endpoint
        # Return transcribed text
```

**Optimizations**:
- VAD (Voice Activity Detection) filtering
- Medical vocabulary bias
- Real-time streaming support
- Language detection for multilingual support

### 4. RASA Dialog Management

**Deployment**: Kubernetes (EKS/GKE)

**Architecture**:
```yaml
# rasa-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rasa-medical-dialog
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: rasa
        image: iaso/rasa-medical:latest
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
```

**Domain Configuration**:
```yaml
# domain.yml
intents:
  - greet
  - symptom_report
  - medication_query
  - appointment_request
  - emergency_symptoms
  - pregnancy_checkup
  - test_results_inquiry

entities:
  - symptom
  - medication
  - body_part
  - time_reference
  - severity_level

slots:
  patient_id:
    type: text
  current_symptoms:
    type: list
  pregnancy_week:
    type: float
  emergency_detected:
    type: bool
```

**Custom Actions**:
```python
class ActionAssessSymptoms(Action):
    """RASA custom action for symptom assessment"""
    
    async def run(self, dispatcher, tracker, domain):
        symptoms = tracker.get_slot("current_symptoms")
        patient_id = tracker.get_slot("patient_id")
        
        # Call Clinical AI for assessment
        assessment = await clinical_ai.assess_symptoms(symptoms, patient_id)
        
        if assessment.severity == "critical":
            dispatcher.utter_message(template="utter_emergency_response")
            # Trigger emergency protocol
        else:
            dispatcher.utter_message(text=assessment.response)
        
        return []
```

### 5. Clinical AI Integration

**Purpose**: Provides medical intelligence and context

**Integration Points**:
- Entity extraction from conversation
- Clinical context retrieval
- Symptom severity assessment
- Medication interaction checking
- Care plan updates

```python
class ClinicalAIClient:
    def __init__(self):
        self.base_url = os.getenv("CLINICAL_AI_URL", "http://localhost:8002")
    
    async def get_patient_context(self, patient_id: str) -> Dict:
        # Retrieve patient history
        # Current medications
        # Active conditions
        # Recent encounters
    
    async def assess_symptoms(self, symptoms: List[str], patient_id: str) -> Assessment:
        # Analyze symptom severity
        # Check against patient history
        # Recommend actions
```

### 6. Amazon Polly Integration (Text-to-Speech)

**Configuration**:
```python
class PollyClient:
    def __init__(self):
        self.polly = boto3.client('polly')
        self.voice_mappings = {
            'empathetic': 'Joanna',  # Neural voice
            'professional': 'Matthew',
            'multilingual': 'Aditi'
        }
    
    async def synthesize(self, text: str, emotion: str = 'caring') -> bytes:
        # Add SSML tags for emotion
        ssml_text = self._add_emotion_tags(text, emotion)
        
        response = self.polly.synthesize_speech(
            Text=ssml_text,
            TextType='ssml',
            OutputFormat='pcm',
            VoiceId=self.voice_mappings['empathetic'],
            Engine='neural'
        )
        
        return response['AudioStream'].read()
```

## Data Flow

### Incoming Call Flow

```
1. Patient calls IasoVoice number
   ↓
2. Amazon Connect answers and identifies caller
   ↓
3. Connect starts audio streaming to Orchestrator
   ↓
4. Orchestrator buffers audio until speech detected
   ↓
5. Audio chunk sent to Whisper for transcription
   ↓
6. Transcribed text sent to RASA with conversation history
   ↓
7. RASA determines intent and required actions
   ↓
8. If clinical data needed, query Clinical AI
   ↓
9. RASA generates response text
   ↓
10. Polly converts response to speech
    ↓
11. Audio streamed back to caller via Connect
```

### State Management

```python
@dataclass
class ConversationState:
    # Call metadata
    call_id: str
    start_time: datetime
    phone_number: str
    
    # Patient context
    patient_id: Optional[str]
    authenticated: bool
    
    # Conversation tracking
    turns: List[ConversationTurn]
    current_intent: str
    active_form: Optional[str]
    
    # Clinical context
    reported_symptoms: List[Symptom]
    medications_discussed: List[Medication]
    appointments_scheduled: List[Appointment]
    
    # Audio settings
    language: str = "en"
    speaking_rate: float = 1.0
```

## Deployment Architecture

### Kubernetes Deployment

```yaml
# iasovoice-orchestrator-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iasovoice-orchestrator
spec:
  replicas: 5
  template:
    spec:
      containers:
      - name: orchestrator
        image: iaso/voice-orchestrator:latest
        env:
        - name: WHISPER_ENDPOINT_ID
          value: "rntxttrdl8uv3i"
        - name: CLINICAL_AI_URL
          value: "http://clinical-ai-service:8002"
        - name: RASA_URL
          value: "http://rasa-service:5005"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
---
apiVersion: v1
kind: Service
metadata:
  name: iasovoice-orchestrator
spec:
  selector:
    app: iasovoice-orchestrator
  ports:
  - port: 8888
    targetPort: 8888
  type: LoadBalancer
```

### Auto-scaling Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: iasovoice-orchestrator-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: iasovoice-orchestrator
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: active_calls
      target:
        type: AverageValue
        averageValue: "10"
```

## Security Considerations

### 1. Authentication & Authorization
```python
class CallAuthentication:
    async def authenticate_caller(self, phone_number: str, dob: str) -> Optional[str]:
        # Verify caller identity
        # Return patient_id if authenticated
        # Log authentication attempts
```

### 2. Data Encryption
- All audio streams encrypted in transit (TLS)
- S3 recordings encrypted at rest
- Patient data tokenized in logs

### 3. HIPAA Compliance
- Call recordings retained per policy
- Audit logs for all interactions
- Data isolation per tenant

## Monitoring & Observability

### Key Metrics
```python
# Prometheus metrics
call_duration_histogram = Histogram('iasovoice_call_duration_seconds')
transcription_latency = Histogram('iasovoice_transcription_latency_seconds')
dialog_turns_counter = Counter('iasovoice_dialog_turns_total')
error_rate = Counter('iasovoice_errors_total', ['service', 'error_type'])
```

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "whisper": await check_whisper_health(),
            "rasa": await check_rasa_health(),
            "clinical_ai": await check_clinical_health(),
            "polly": await check_polly_health()
        },
        "active_calls": session_manager.active_count()
    }
```

## Example Conversation Flows

### Maternal Health Check-in
```
IasoVoice: "Hello! This is your IASO health assistant calling for your 
           prenatal check-in. Is this Sarah Johnson?"

Patient: "Yes, this is Sarah."

IasoVoice: "Great! How are you feeling today? Any concerns since your 
           last visit?"

Patient: "I've been having some swelling in my feet and occasional headaches."

IasoVoice: [Clinical AI flags potential preeclampsia risk]
          "I understand. Swelling and headaches during pregnancy need attention. 
           On a scale of 1-10, how severe are your headaches?"

Patient: "About a 6 or 7, especially in the mornings."

IasoVoice: "Thank you for letting me know. Given your symptoms, I'd like to 
           schedule you for an appointment tomorrow. Dr. Smith has an opening 
           at 10 AM. Would that work for you?"
```

### Medication Adherence Check
```
IasoVoice: "Hi John, this is your IASO health assistant. I'm calling to 
           check on your new blood pressure medication. Have you been 
           taking it as prescribed?"

Patient: "I've been taking it, but it makes me dizzy sometimes."

IasoVoice: "I'm sorry to hear that. Dizziness can be a side effect. 
           Are you taking it with food as recommended?"

Patient: "No, I usually take it first thing in the morning."

IasoVoice: "Taking it with breakfast might help reduce the dizziness. 
           I'll make a note for Dr. Martinez. Would you like me to 
           schedule a follow-up to discuss alternative medications?"
```

## Future Enhancements

### Phase 1 (Next 3 months)
- Multi-language support (Spanish, Mandarin)
- Emotion detection in voice
- Proactive health reminders
- Integration with wearable data

### Phase 2 (6 months)
- Video call support
- Real-time clinical decision support
- Advanced symptom triage
- Prescription refill automation

### Phase 3 (12 months)
- AI-powered health coaching
- Predictive health alerts
- Integration with emergency services
- Behavioral health support

## Getting Started

### Prerequisites
1. AWS Account with Connect enabled
2. RunPod API key
3. Kubernetes cluster (EKS/GKE)
4. RASA training data
5. Clinical AI service running

### Installation Steps
1. Deploy RASA on Kubernetes
2. Configure Amazon Connect instance
3. Deploy IasoVoice Orchestrator
4. Set up monitoring
5. Test with sample calls

### Configuration
```bash
# Environment variables
export AWS_REGION=us-east-1
export CONNECT_INSTANCE_ID=xxx
export RUNPOD_API_KEY=xxx
export CLINICAL_AI_URL=http://clinical-ai:8002
export RASA_URL=http://rasa:5005
```

This architecture provides a scalable, secure, and intelligent voice interaction system for healthcare, enabling natural conversations while maintaining clinical accuracy and regulatory compliance.