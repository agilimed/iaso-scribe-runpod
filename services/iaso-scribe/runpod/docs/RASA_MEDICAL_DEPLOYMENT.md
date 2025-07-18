# RASA Medical Conversation Deployment Strategy

## Overview

This document outlines the deployment strategy for RASA Open Source to handle medical conversations in the IasoVoice system. RASA will manage dialog flows, understand medical intents, maintain conversation context, and trigger appropriate clinical actions.

## Why RASA for Medical Conversations

### Advantages over Amazon Lex V2
1. **Complex Medical Dialogs**: Multi-turn conversations with medical context
2. **Custom NLU Pipeline**: Medical entity recognition and intent classification
3. **Privacy**: Self-hosted solution for HIPAA compliance
4. **Flexibility**: Custom actions for clinical integrations
5. **Training Control**: Use real medical conversation data

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        RASA Deployment                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │   RASA Server   │  │  Action Server   │  │  Redis Cache   │  │
│  │   (NLU + Core)  │  │ (Custom Logic)   │  │ (Session Store)│  │
│  └────────┬────────┘  └────────┬────────┘  └────────────────┘  │
│           │                     │                                 │
│  ┌────────┴─────────────────────┴────────────────────────────┐  │
│  │              Kubernetes Cluster (EKS/GKE)                  │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Medical Domain Configuration

### 1. Domain Definition (`domain.yml`)

```yaml
version: "3.1"

intents:
  # General
  - greet
  - goodbye
  - affirm
  - deny
  - out_of_scope
  
  # Medical Intents
  - report_symptoms
  - request_appointment
  - medication_question
  - test_results_inquiry
  - emergency_symptoms
  - side_effect_report
  - prescription_refill
  - health_advice
  
  # Maternal Health
  - pregnancy_symptoms
  - prenatal_checkup
  - labor_signs
  - postpartum_concerns
  
  # Chronic Disease Management
  - diabetes_management
  - blood_pressure_check
  - medication_adherence

entities:
  - symptom
  - medication
  - body_part
  - severity
  - duration
  - frequency
  - appointment_type
  - time_reference
  - medical_condition
  - test_type
  - vital_sign
  - pregnancy_week

slots:
  # Patient Information
  patient_id:
    type: text
    mappings:
      - type: custom
  
  patient_name:
    type: text
    mappings:
      - type: from_entity
        entity: person
  
  # Medical Context
  current_symptoms:
    type: list
    mappings:
      - type: from_entity
        entity: symptom
  
  symptom_severity:
    type: categorical
    values:
      - mild
      - moderate
      - severe
      - critical
    mappings:
      - type: from_entity
        entity: severity
  
  symptom_duration:
    type: text
    mappings:
      - type: from_entity
        entity: duration
  
  medications_discussed:
    type: list
    mappings:
      - type: from_entity
        entity: medication
  
  # Conversation State
  authenticated:
    type: bool
    initial_value: false
    mappings:
      - type: custom
  
  emergency_detected:
    type: bool
    initial_value: false
    mappings:
      - type: custom
  
  # Maternal Health
  pregnancy_week:
    type: float
    min_value: 0
    max_value: 42
    mappings:
      - type: from_entity
        entity: pregnancy_week
  
  # Appointment
  requested_appointment_type:
    type: text
    mappings:
      - type: from_entity
        entity: appointment_type
  
  preferred_appointment_time:
    type: text
    mappings:
      - type: from_entity
        entity: time_reference

responses:
  # Greetings
  utter_greet:
    - text: "Hello! This is your IASO health assistant. How can I help you today?"
      metadata:
        voice_emotion: "friendly"
  
  utter_ask_symptoms:
    - text: "I'm here to help. Can you describe what symptoms you're experiencing?"
      metadata:
        voice_emotion: "concerned"
  
  # Symptom Assessment
  utter_ask_symptom_severity:
    - text: "On a scale of 1 to 10, how severe would you rate your {symptom}?"
      metadata:
        voice_emotion: "professional"
  
  utter_ask_symptom_duration:
    - text: "How long have you been experiencing {symptom}?"
  
  # Emergency Response
  utter_emergency_response:
    - text: "Based on what you've told me, I'm concerned about your symptoms. I strongly recommend you seek immediate medical attention. Would you like me to provide the nearest emergency room information?"
      metadata:
        voice_emotion: "urgent"
        priority: "high"
  
  # Appointment Scheduling
  utter_confirm_appointment:
    - text: "I can schedule a {requested_appointment_type} appointment for you. Dr. {doctor_name} has availability on {date} at {time}. Would that work for you?"
  
  # Medication
  utter_medication_reminder:
    - text: "It's important to take {medication} as prescribed. Are you experiencing any side effects?"
  
  # Maternal Health
  utter_pregnancy_check:
    - text: "How are you feeling at {pregnancy_week} weeks? Any new symptoms or concerns?"
      metadata:
        voice_emotion: "caring"

actions:
  # Built-in
  - action_listen
  - action_restart
  - action_default_fallback
  
  # Custom Medical Actions
  - action_authenticate_patient
  - action_assess_symptoms
  - action_check_drug_interactions
  - action_schedule_appointment
  - action_get_test_results
  - action_update_care_plan
  - action_emergency_protocol
  - action_medication_adherence_check
  - action_prenatal_risk_assessment
  - action_generate_soap_note

forms:
  symptom_form:
    required_slots:
      - current_symptoms
      - symptom_severity
      - symptom_duration
  
  appointment_form:
    required_slots:
      - requested_appointment_type
      - preferred_appointment_time
  
  medication_adherence_form:
    required_slots:
      - medications_discussed
      - side_effects
```

### 2. NLU Training Data (`data/nlu.yml`)

```yaml
version: "3.1"

nlu:
  - intent: report_symptoms
    examples: |
      - I have a [headache](symptom)
      - I'm experiencing [chest pain](symptom) and [shortness of breath](symptom)
      - My [stomach](body_part) has been [hurting](symptom) for [three days](duration)
      - I've had a [fever](symptom) since [yesterday](time_reference)
      - [Sharp pain](symptom) in my [lower back](body_part)
      - Feeling [dizzy](symptom) and [nauseous](symptom)
      - I have [severe](severity) [abdominal pain](symptom)
      - Been having [mild](severity) [headaches](symptom) [every morning](frequency)
  
  - intent: emergency_symptoms
    examples: |
      - I have [crushing chest pain](symptom) radiating to my [left arm](body_part)
      - Can't breathe properly and chest feels tight
      - [Severe](severity) [headache](symptom) with [vision changes](symptom)
      - [Slurred speech](symptom) and [weakness](symptom) on one side
      - [Heavy bleeding](symptom) that won't stop
      - [Severe](severity) [allergic reaction](symptom) with [swelling](symptom)
  
  - intent: pregnancy_symptoms
    examples: |
      - I'm [28 weeks](pregnancy_week) pregnant and having [contractions](symptom)
      - At [32 weeks](pregnancy_week) with [swollen feet](symptom)
      - [Morning sickness](symptom) at [10 weeks](pregnancy_week)
      - Baby hasn't moved much today, I'm [36 weeks](pregnancy_week)
      - Having [spotting](symptom) at [20 weeks](pregnancy_week) pregnant
  
  - intent: medication_question
    examples: |
      - Can I take [ibuprofen](medication) with [metformin](medication)?
      - What are the side effects of [lisinopril](medication)?
      - I forgot to take my [blood pressure medication](medication) this morning
      - Is [amoxicillin](medication) safe during pregnancy?
      - My [insulin](medication) doesn't seem to be working well

  - lookup: symptom
    examples: |
      - headache
      - fever
      - cough
      - chest pain
      - shortness of breath
      - nausea
      - vomiting
      - dizziness
      - fatigue
      - abdominal pain
      - back pain
      - swelling
      - rash
      - joint pain
      - muscle aches

  - lookup: medication
    examples: |
      - metformin
      - lisinopril
      - atorvastatin
      - levothyroxine
      - amlodipine
      - metoprolol
      - omeprazole
      - aspirin
      - insulin
      - ibuprofen
      - acetaminophen
      - amoxicillin
```

### 3. Conversation Stories (`data/stories.yml`)

```yaml
version: "3.1"

stories:
  - story: symptom assessment flow
    steps:
      - intent: greet
      - action: utter_greet
      - intent: report_symptoms
        entities:
          - symptom: "headache"
      - action: utter_ask_symptom_severity
      - intent: inform
        entities:
          - severity: "severe"
      - action: utter_ask_symptom_duration
      - intent: inform
        entities:
          - duration: "2 days"
      - action: action_assess_symptoms
      - action: utter_recommend_appointment

  - story: emergency detection flow
    steps:
      - intent: report_symptoms
        entities:
          - symptom: "chest pain"
          - symptom: "shortness of breath"
      - action: action_assess_symptoms
      - slot_was_set:
          - emergency_detected: true
      - action: action_emergency_protocol
      - action: utter_emergency_response

  - story: medication adherence check
    steps:
      - intent: greet
      - action: utter_greet
      - action: action_medication_adherence_check
      - action: utter_medication_reminder
      - intent: affirm
      - action: utter_ask_side_effects
      - intent: report_side_effect
      - action: action_check_side_effects
      - action: utter_schedule_followup

  - story: prenatal checkup flow
    steps:
      - intent: greet
      - action: action_authenticate_patient
      - slot_was_set:
          - pregnancy_week: 28
      - action: utter_pregnancy_check
      - intent: pregnancy_symptoms
        entities:
          - symptom: "swelling"
          - symptom: "headaches"
      - action: action_prenatal_risk_assessment
      - action: utter_prenatal_concern
      - action: action_schedule_appointment
```

## Custom Actions Implementation

### Action Server (`actions/actions.py`)

```python
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import httpx
import asyncio
from datetime import datetime

class ActionAuthenticatePatient(Action):
    """Authenticate caller and retrieve patient context"""
    
    def name(self) -> Text:
        return "action_authenticate_patient"
    
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Get phone number from metadata
        phone_number = tracker.latest_message.get('metadata', {}).get('phone_number')
        
        # Call authentication service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://clinical-ai:8002/authenticate",
                json={"phone_number": phone_number}
            )
        
        if response.status_code == 200:
            patient_data = response.json()
            
            return [
                SlotSet("patient_id", patient_data['patient_id']),
                SlotSet("patient_name", patient_data['name']),
                SlotSet("authenticated", True),
                SlotSet("pregnancy_week", patient_data.get('pregnancy_week'))
            ]
        
        return [SlotSet("authenticated", False)]

class ActionAssessSymptoms(Action):
    """Assess reported symptoms for severity"""
    
    def name(self) -> Text:
        return "action_assess_symptoms"
    
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        symptoms = tracker.get_slot("current_symptoms")
        severity = tracker.get_slot("symptom_severity")
        patient_id = tracker.get_slot("patient_id")
        
        # Emergency symptoms that require immediate attention
        emergency_keywords = [
            "chest pain", "shortness of breath", "severe headache",
            "slurred speech", "heavy bleeding", "unconscious",
            "severe abdominal pain", "difficulty breathing"
        ]
        
        # Check for emergency symptoms
        is_emergency = any(
            keyword in " ".join(symptoms).lower() 
            for keyword in emergency_keywords
        )
        
        if is_emergency or severity == "critical":
            return [
                SlotSet("emergency_detected", True),
                SlotSet("triage_priority", "immediate")
            ]
        
        # Call Clinical AI for detailed assessment
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://clinical-ai:8002/assess_symptoms",
                json={
                    "patient_id": patient_id,
                    "symptoms": symptoms,
                    "severity": severity
                }
            )
        
        assessment = response.json()
        
        # Determine response based on assessment
        if assessment['risk_level'] == 'high':
            dispatcher.utter_message(
                text=f"Based on your symptoms, I recommend seeing a healthcare provider soon. {assessment['recommendation']}"
            )
        else:
            dispatcher.utter_message(
                text=assessment['recommendation']
            )
        
        return [
            SlotSet("assessment_complete", True),
            SlotSet("risk_level", assessment['risk_level'])
        ]

class ActionScheduleAppointment(Action):
    """Schedule appointment with available provider"""
    
    def name(self) -> Text:
        return "action_schedule_appointment"
    
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        appointment_type = tracker.get_slot("requested_appointment_type")
        preferred_time = tracker.get_slot("preferred_appointment_time")
        patient_id = tracker.get_slot("patient_id")
        urgency = tracker.get_slot("risk_level", "routine")
        
        # Call appointment service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://appointment-service/schedule",
                json={
                    "patient_id": patient_id,
                    "type": appointment_type,
                    "preferred_time": preferred_time,
                    "urgency": urgency
                }
            )
        
        if response.status_code == 200:
            appointment = response.json()
            
            dispatcher.utter_message(
                template="utter_confirm_appointment",
                doctor_name=appointment['provider_name'],
                date=appointment['date'],
                time=appointment['time']
            )
            
            return [
                SlotSet("appointment_scheduled", True),
                SlotSet("appointment_id", appointment['id'])
            ]
        
        dispatcher.utter_message(
            text="I'm having trouble scheduling your appointment. Let me transfer you to our scheduling team."
        )
        
        return [SlotSet("appointment_scheduled", False)]

class ActionPrenatalRiskAssessment(Action):
    """Assess risks for pregnant patients"""
    
    def name(self) -> Text:
        return "action_prenatal_risk_assessment"
    
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        symptoms = tracker.get_slot("current_symptoms", [])
        pregnancy_week = tracker.get_slot("pregnancy_week")
        
        # High-risk pregnancy symptoms
        high_risk_symptoms = {
            "headache": ["preeclampsia", "high blood pressure"],
            "swelling": ["preeclampsia", "edema"],
            "bleeding": ["miscarriage", "placental issues"],
            "severe abdominal pain": ["ectopic pregnancy", "placental abruption"],
            "no fetal movement": ["fetal distress"],
            "contractions": ["preterm labor"] if pregnancy_week < 37 else ["labor"]
        }
        
        risks_identified = []
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            for risk_symptom, conditions in high_risk_symptoms.items():
                if risk_symptom in symptom_lower:
                    risks_identified.extend(conditions)
        
        if risks_identified:
            dispatcher.utter_message(
                text=f"Given your symptoms at {pregnancy_week} weeks, I'm concerned about possible {', '.join(set(risks_identified))}. "
                     f"I strongly recommend you contact your OB provider immediately or visit the emergency room."
            )
            return [
                SlotSet("prenatal_risk", "high"),
                SlotSet("emergency_detected", True)
            ]
        
        return [SlotSet("prenatal_risk", "low")]

class ActionGenerateSOAPNote(Action):
    """Generate SOAP note from conversation"""
    
    def name(self) -> Text:
        return "action_generate_soap_note"
    
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Collect conversation data
        conversation_data = {
            "patient_id": tracker.get_slot("patient_id"),
            "symptoms": tracker.get_slot("current_symptoms"),
            "severity": tracker.get_slot("symptom_severity"),
            "duration": tracker.get_slot("symptom_duration"),
            "medications": tracker.get_slot("medications_discussed"),
            "conversation_turns": [
                {
                    "speaker": event.get("event"),
                    "text": event.get("text", ""),
                    "timestamp": event.get("timestamp")
                }
                for event in tracker.events
                if event.get("event") in ["user", "bot"]
            ]
        }
        
        # Call Phi-4 via MCP to generate SOAP note
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://phi4-mcp:8090/generate_soap_note",
                json={
                    "conversation_text": self._format_conversation(tracker),
                    "clinical_context": conversation_data
                }
            )
        
        if response.status_code == 200:
            soap_note = response.json()['soap_note']
            
            # Save to clinical record
            await self._save_soap_note(
                patient_id=tracker.get_slot("patient_id"),
                soap_note=soap_note
            )
            
            return [SlotSet("soap_note_generated", True)]
        
        return [SlotSet("soap_note_generated", False)]
    
    def _format_conversation(self, tracker: Tracker) -> str:
        """Format conversation history for SOAP generation"""
        conversation = []
        for event in tracker.events:
            if event.get("event") == "user":
                conversation.append(f"Patient: {event.get('text', '')}")
            elif event.get("event") == "bot":
                conversation.append(f"Assistant: {event.get('text', '')}")
        
        return "\n".join(conversation)
```

## Deployment Configuration

### 1. RASA Server Deployment

```yaml
# rasa-server-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rasa-server
  namespace: iasovoice
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rasa-server
  template:
    metadata:
      labels:
        app: rasa-server
    spec:
      containers:
      - name: rasa
        image: iaso/rasa-medical:latest
        ports:
        - containerPort: 5005
        env:
        - name: RASA_TELEMETRY_ENABLED
          value: "false"
        - name: RASA_X_ENABLED
          value: "false"
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        volumeMounts:
        - name: models
          mountPath: /app/models
        - name: config
          mountPath: /app/config
        livenessProbe:
          httpGet:
            path: /
            port: 5005
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /status
            port: 5005
          initialDelaySeconds: 20
          periodSeconds: 5
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: rasa-models-pvc
      - name: config
        configMap:
          name: rasa-config
---
apiVersion: v1
kind: Service
metadata:
  name: rasa-server
  namespace: iasovoice
spec:
  selector:
    app: rasa-server
  ports:
  - port: 5005
    targetPort: 5005
  type: ClusterIP
```

### 2. Action Server Deployment

```yaml
# rasa-action-server-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rasa-action-server
  namespace: iasovoice
spec:
  replicas: 5
  selector:
    matchLabels:
      app: rasa-action-server
  template:
    metadata:
      labels:
        app: rasa-action-server
    spec:
      containers:
      - name: action-server
        image: iaso/rasa-actions-medical:latest
        ports:
        - containerPort: 5055
        env:
        - name: CLINICAL_AI_URL
          value: "http://clinical-ai-service:8002"
        - name: APPOINTMENT_SERVICE_URL
          value: "http://appointment-service:8080"
        - name: PHI4_MCP_URL
          value: "http://phi4-mcp:8090"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 5055
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: rasa-action-server
  namespace: iasovoice
spec:
  selector:
    app: rasa-action-server
  ports:
  - port: 5055
    targetPort: 5055
  type: ClusterIP
```

### 3. Redis Session Store

```yaml
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-session-store
  namespace: iasovoice
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: redis-data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis-session-store
  namespace: iasovoice
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

### 4. ConfigMap for RASA Configuration

```yaml
# rasa-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: rasa-config
  namespace: iasovoice
data:
  config.yml: |
    language: en
    
    pipeline:
      - name: WhitespaceTokenizer
      - name: RegexFeaturizer
      - name: LexicalSyntacticFeaturizer
      - name: CountVectorsFeaturizer
      - name: CountVectorsFeaturizer
        analyzer: char_wb
        min_ngram: 1
        max_ngram: 4
      - name: DIETClassifier
        epochs: 100
        entity_recognition: True
        constrain_similarities: True
      - name: EntitySynonymMapper
      - name: ResponseSelector
        epochs: 100
      
    policies:
      - name: MemoizationPolicy
      - name: RulePolicy
      - name: TEDPolicy
        max_history: 10
        epochs: 100
        constrain_similarities: True
      - name: UnexpecTEDIntentPolicy
        max_history: 5
        epochs: 100
    
    session_config:
      session_expiration_time: 3600  # 1 hour
      carry_over_slots_to_new_session: true

  endpoints.yml: |
    action_endpoint:
      url: "http://rasa-action-server:5055/webhook"
    
    tracker_store:
      type: redis
      url: redis-session-store
      port: 6379
      db: 0
      key_prefix: rasa
    
    event_broker:
      type: redis
      url: redis-session-store
      port: 6379
      db: 1
      key_prefix: events
```

## Training and Model Management

### 1. Training Pipeline

```bash
#!/bin/bash
# train-rasa-model.sh

# Train new model
rasa train \
  --config config.yml \
  --domain domain.yml \
  --data data/ \
  --out models/

# Test model
rasa test \
  --model models/latest.tar.gz \
  --stories data/test_stories.yml \
  --out results/

# Validate data
rasa data validate
```

### 2. Model Versioning

```python
# model_manager.py
import boto3
from datetime import datetime

class RASAModelManager:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.bucket = 'iaso-rasa-models'
    
    def upload_model(self, model_path: str, metadata: dict):
        """Upload trained model to S3 with versioning"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = f"rasa_medical_{timestamp}.tar.gz"
        
        # Upload to S3
        self.s3.upload_file(
            model_path,
            self.bucket,
            f"models/{model_name}",
            ExtraArgs={'Metadata': metadata}
        )
        
        # Update latest pointer
        self.s3.copy_object(
            Bucket=self.bucket,
            CopySource=f"{self.bucket}/models/{model_name}",
            Key="models/latest.tar.gz"
        )
    
    def deploy_model(self, model_version: str):
        """Deploy specific model version to production"""
        # Update Kubernetes deployment
        # Trigger rolling update
        pass
```

## Monitoring and Analytics

### 1. Conversation Metrics

```python
# conversation_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Metrics
conversation_duration = Histogram(
    'rasa_conversation_duration_seconds',
    'Duration of conversations',
    ['intent', 'completion_status']
)

intent_counter = Counter(
    'rasa_intent_total',
    'Total number of intents recognized',
    ['intent', 'confidence_level']
)

emergency_detection = Counter(
    'rasa_emergency_detection_total',
    'Number of emergency situations detected'
)

appointment_scheduled = Counter(
    'rasa_appointments_scheduled_total',
    'Number of appointments scheduled through voice'
)

active_conversations = Gauge(
    'rasa_active_conversations',
    'Number of currently active conversations'
)
```

### 2. Health Monitoring

```yaml
# monitoring-deployment.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: rasa-alerts
  namespace: iasovoice
data:
  alerts.yml: |
    groups:
      - name: rasa_alerts
        interval: 30s
        rules:
          - alert: RASAHighErrorRate
            expr: rate(rasa_errors_total[5m]) > 0.05
            for: 5m
            labels:
              severity: warning
            annotations:
              summary: "High error rate in RASA"
              
          - alert: RASALowConfidence
            expr: histogram_quantile(0.5, rasa_confidence_score) < 0.7
            for: 10m
            labels:
              severity: warning
            annotations:
              summary: "Low confidence scores in intent recognition"
```

## Testing Strategy

### 1. Unit Tests for Actions

```python
# test_actions.py
import pytest
from actions import ActionAssessSymptoms
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

@pytest.mark.asyncio
async def test_emergency_symptom_detection():
    action = ActionAssessSymptoms()
    
    # Mock tracker with emergency symptoms
    tracker = Tracker(
        sender_id="test_user",
        slots={
            "current_symptoms": ["chest pain", "shortness of breath"],
            "symptom_severity": "severe"
        },
        latest_message={},
        events=[],
        paused=False,
        followup_action=None,
        active_loop=None,
        latest_action_name=None
    )
    
    dispatcher = CollectingDispatcher()
    
    events = await action.run(dispatcher, tracker, {})
    
    # Check emergency detection
    emergency_slot = next(
        (e for e in events if e['event'] == 'slot' and e['name'] == 'emergency_detected'),
        None
    )
    
    assert emergency_slot is not None
    assert emergency_slot['value'] is True
```

### 2. Integration Tests

```python
# test_integration.py
import httpx
import pytest

@pytest.mark.asyncio
async def test_full_symptom_flow():
    """Test complete symptom assessment flow"""
    
    async with httpx.AsyncClient() as client:
        # Start conversation
        response = await client.post(
            "http://localhost:5005/conversations/test_user/messages",
            json={"text": "I have severe chest pain"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Check for emergency response
        assert any(
            "emergency" in r['text'].lower() 
            for r in result if r.get('text')
        )
```

## Production Deployment Checklist

### Pre-deployment
- [ ] Train model with production data
- [ ] Validate model performance (>90% intent accuracy)
- [ ] Test all custom actions
- [ ] Configure SSL/TLS for endpoints
- [ ] Set up monitoring and alerts
- [ ] Prepare rollback plan

### Deployment Steps
1. Build and push Docker images
2. Apply Kubernetes manifests
3. Update ConfigMaps and Secrets
4. Deploy new model version
5. Run smoke tests
6. Monitor metrics for 30 minutes
7. Full deployment or rollback decision

### Post-deployment
- [ ] Monitor conversation metrics
- [ ] Review emergency detection accuracy
- [ ] Collect feedback from initial calls
- [ ] Fine-tune based on real conversations
- [ ] Update training data with new examples

## Cost Optimization

### Resource Allocation
- **RASA Server**: 3 replicas (scales 2-10 based on load)
- **Action Server**: 5 replicas (scales 3-20 based on load)
- **Redis**: Single instance with persistence
- **Total Base Cost**: ~$200/month on GKE

### Optimization Strategies
1. Use spot instances for training
2. Scale down during off-hours
3. Cache common responses in Redis
4. Batch process non-urgent actions

## Next Steps

1. **Week 1**: Deploy base RASA infrastructure
2. **Week 2**: Train initial model with medical data
3. **Week 3**: Integrate with Clinical AI services
4. **Week 4**: Connect to IasoVoice orchestrator
5. **Week 5**: Begin pilot testing with real calls

This deployment strategy provides a robust, scalable, and medically-aware conversational AI system that can handle complex healthcare interactions while maintaining HIPAA compliance and clinical accuracy.