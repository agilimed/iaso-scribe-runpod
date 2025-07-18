from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, ActionExecuted
from rasa_sdk.forms import FormValidationAction
import httpx
import asyncio
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
WHISPER_ENDPOINT_ID = os.getenv("WHISPER_ENDPOINT_ID", "rntxttrdl8uv3i")
PHI4_ENDPOINT_ID = os.getenv("PHI4_ENDPOINT_ID", "tmmwa4q8ax5sg4")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
CLINICAL_AI_URL = os.getenv("CLINICAL_AI_URL", "http://localhost:8002")

class ActionAuthenticatePatient(Action):
    """Authenticate patient using provided ID"""
    
    def name(self) -> Text:
        return "action_authenticate_patient"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        patient_id = tracker.get_slot("patient_id")
        phone_number = tracker.get_slot("phone_number")
        
        # Simple authentication logic (replace with actual authentication)
        if patient_id and len(patient_id) >= 5:
            authenticated = True
            dispatcher.utter_message(
                text=f"Thank you for verifying your identity. How can I help you today?",
                json_message={"custom": {"voice_emotion": "friendly"}}
            )
        else:
            authenticated = False
            dispatcher.utter_message(
                text="I couldn't verify your identity. Please provide a valid patient ID.",
                json_message={"custom": {"voice_emotion": "empathetic"}}
            )
        
        return [SlotSet("authenticated", authenticated)]

class ActionCollectSymptoms(Action):
    """Collect and process patient symptoms"""
    
    def name(self) -> Text:
        return "action_collect_symptoms"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Extract symptoms from user message
        symptoms = []
        entities = tracker.latest_message.get('entities', [])
        
        for entity in entities:
            if entity.get('entity') == 'symptom':
                symptoms.append(entity.get('value'))
        
        # Get current symptoms from slot
        current_symptoms = tracker.get_slot("symptoms") or []
        all_symptoms = current_symptoms + symptoms
        
        if symptoms:
            symptom_text = ", ".join(symptoms)
            dispatcher.utter_message(
                text=f"I understand you're experiencing {symptom_text}. Let me gather some more information.",
                json_message={"custom": {"voice_emotion": "empathetic"}}
            )
        else:
            dispatcher.utter_message(
                text="I didn't catch any specific symptoms. Could you please describe what you're feeling?",
                json_message={"custom": {"voice_emotion": "empathetic"}}
            )
        
        return [SlotSet("symptoms", all_symptoms)]

class ActionAssessEmergency(Action):
    """Assess if situation requires emergency care"""
    
    def name(self) -> Text:
        return "action_assess_emergency"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        symptoms = tracker.get_slot("symptoms") or []
        pain_level = tracker.get_slot("pain_level")
        
        # Emergency keywords
        emergency_symptoms = [
            "chest pain", "difficulty breathing", "severe headache",
            "stroke", "heart attack", "unconscious", "bleeding",
            "severe pain", "poisoning", "overdose"
        ]
        
        # Check for emergency conditions
        emergency_level = "low"
        
        # Check symptoms
        for symptom in symptoms:
            if any(emergency_word in symptom.lower() for emergency_word in emergency_symptoms):
                emergency_level = "high"
                break
        
        # Check pain level
        if pain_level and int(pain_level) >= 8:
            emergency_level = "high"
        elif pain_level and int(pain_level) >= 6:
            emergency_level = "medium"
        
        # Handle based on emergency level
        if emergency_level == "high":
            dispatcher.utter_message(
                text="Based on your symptoms, this appears to be a medical emergency. I'm connecting you with emergency services immediately.",
                json_message={"custom": {"voice_emotion": "urgent"}}
            )
            return [
                SlotSet("emergency_level", emergency_level),
                FollowupAction("action_escalate_to_human")
            ]
        elif emergency_level == "medium":
            dispatcher.utter_message(
                text="Your symptoms indicate you should seek medical attention today. I recommend scheduling an urgent appointment.",
                json_message={"custom": {"voice_emotion": "professional"}}
            )
        else:
            dispatcher.utter_message(
                text="Let me continue gathering information to provide you with the best recommendation.",
                json_message={"custom": {"voice_emotion": "professional"}}
            )
        
        return [SlotSet("emergency_level", emergency_level)]

class ActionGetClinicalContext(Action):
    """Get clinical context for patient"""
    
    def name(self) -> Text:
        return "action_get_clinical_context"
    
    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        patient_id = tracker.get_slot("patient_id")
        
        if not patient_id:
            return [SlotSet("clinical_context", {})]
        
        try:
            # Call Clinical AI service for patient context
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{CLINICAL_AI_URL}/patient/{patient_id}/context"
                )
                
                if response.status_code == 200:
                    clinical_context = response.json()
                    
                    # Inform user about retrieved context
                    dispatcher.utter_message(
                        text="I've retrieved your medical history. This will help me provide better recommendations.",
                        json_message={"custom": {"voice_emotion": "professional"}}
                    )
                    
                    return [SlotSet("clinical_context", clinical_context)]
                else:
                    logger.error(f"Clinical AI service error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error getting clinical context: {e}")
        
        return [SlotSet("clinical_context", {})]

class ActionGenerateRecommendation(Action):
    """Generate medical recommendation using Phi-4"""
    
    def name(self) -> Text:
        return "action_generate_recommendation"
    
    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Gather all information
        symptoms = tracker.get_slot("symptoms") or []
        pain_level = tracker.get_slot("pain_level")
        medications = tracker.get_slot("medications") or []
        allergies = tracker.get_slot("allergies") or []
        medical_history = tracker.get_slot("medical_history") or []
        clinical_context = tracker.get_slot("clinical_context") or {}
        
        # Build context for Phi-4
        context = {
            "symptoms": symptoms,
            "pain_level": pain_level,
            "medications": medications,
            "allergies": allergies,
            "medical_history": medical_history,
            "clinical_context": clinical_context
        }
        
        try:
            # Call Phi-4 for recommendation
            recommendation = await self._call_phi4_for_recommendation(context)
            
            if recommendation:
                dispatcher.utter_message(
                    text=recommendation,
                    json_message={"custom": {"voice_emotion": "professional"}}
                )
            else:
                dispatcher.utter_message(
                    text="Based on your symptoms, I recommend consulting with your healthcare provider for a proper evaluation.",
                    json_message={"custom": {"voice_emotion": "professional"}}
                )
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            dispatcher.utter_message(
                text="I'm having trouble processing your information right now. Please consult with your healthcare provider.",
                json_message={"custom": {"voice_emotion": "empathetic"}}
            )
        
        return []
    
    async def _call_phi4_for_recommendation(self, context: Dict[str, Any]) -> str:
        """Call Phi-4 via RunPod for medical recommendation"""
        
        prompt = f"""
        You are a medical assistant AI providing recommendations based on patient information.
        
        Patient Information:
        - Symptoms: {', '.join(context['symptoms']) if context['symptoms'] else 'None reported'}
        - Pain Level: {context['pain_level']}/10
        - Current Medications: {', '.join(context['medications']) if context['medications'] else 'None reported'}
        - Allergies: {', '.join(context['allergies']) if context['allergies'] else 'None reported'}
        - Medical History: {', '.join(context['medical_history']) if context['medical_history'] else 'None reported'}
        
        Please provide a brief, professional recommendation for this patient. Include:
        1. Assessment of symptoms
        2. Recommended next steps
        3. Any red flags or urgent concerns
        
        Keep response under 150 words and use empathetic, professional language.
        """
        
        url = f"https://api.runpod.ai/v2/{PHI4_ENDPOINT_ID}/runsync"
        headers = {
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": {
                "prompt": prompt,
                "max_tokens": 300,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "COMPLETED":
                        return result["output"].get("generated_text", "")
                        
        except Exception as e:
            logger.error(f"Phi-4 API error: {e}")
        
        return ""

class ActionScheduleAppointment(Action):
    """Schedule an appointment for the patient"""
    
    def name(self) -> Text:
        return "action_schedule_appointment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        patient_id = tracker.get_slot("patient_id")
        
        if not patient_id:
            dispatcher.utter_message(
                text="I need to verify your identity before scheduling an appointment.",
                json_message={"custom": {"voice_emotion": "professional"}}
            )
            return [FollowupAction("action_authenticate_patient")]
        
        # In a real implementation, this would integrate with scheduling system
        dispatcher.utter_message(
            text="I'll help you schedule an appointment. Our next available slot is tomorrow at 2 PM. Would that work for you?",
            json_message={"custom": {"voice_emotion": "professional"}}
        )
        
        return [SlotSet("appointment_requested", True)]

class ActionCreateSoapNote(Action):
    """Create SOAP note from conversation"""
    
    def name(self) -> Text:
        return "action_create_soap_note"
    
    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Gather conversation information
        conversation_text = self._format_conversation(tracker)
        
        try:
            # Call Phi-4 to generate SOAP note
            soap_note = await self._generate_soap_note(conversation_text)
            
            if soap_note:
                logger.info(f"Generated SOAP note for patient {tracker.get_slot('patient_id')}")
                
                # In production, save to clinical system
                # await self._save_soap_note(patient_id, soap_note)
                
                dispatcher.utter_message(
                    text="I've created a summary of our conversation for your medical record.",
                    json_message={"custom": {"voice_emotion": "professional"}}
                )
            
        except Exception as e:
            logger.error(f"Error creating SOAP note: {e}")
        
        return []
    
    def _format_conversation(self, tracker: Tracker) -> str:
        """Format conversation for SOAP note generation"""
        
        # Get all events from tracker
        events = tracker.events
        conversation = []
        
        for event in events:
            if event.get('event') == 'user':
                conversation.append(f"Patient: {event.get('text', '')}")
            elif event.get('event') == 'bot':
                conversation.append(f"Assistant: {event.get('text', '')}")
        
        return "\n".join(conversation)
    
    async def _generate_soap_note(self, conversation: str) -> str:
        """Generate SOAP note using Phi-4"""
        
        prompt = f"""
        Generate a SOAP note from the following medical conversation:
        
        {conversation}
        
        Format as:
        SUBJECTIVE: Patient's chief complaint and symptoms
        OBJECTIVE: Observed findings and vital signs (if any)
        ASSESSMENT: Clinical impression
        PLAN: Recommended treatment or follow-up
        
        Keep it concise and professional.
        """
        
        url = f"https://api.runpod.ai/v2/{PHI4_ENDPOINT_ID}/runsync"
        headers = {
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": {
                "prompt": prompt,
                "max_tokens": 500,
                "temperature": 0.3
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "COMPLETED":
                        return result["output"].get("generated_text", "")
                        
        except Exception as e:
            logger.error(f"SOAP note generation error: {e}")
        
        return ""

class ActionEscalateToHuman(Action):
    """Escalate to human healthcare provider"""
    
    def name(self) -> Text:
        return "action_escalate_to_human"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        emergency_level = tracker.get_slot("emergency_level")
        
        if emergency_level == "high":
            dispatcher.utter_message(
                text="I'm connecting you with emergency services now. Please stay on the line.",
                json_message={"custom": {"voice_emotion": "urgent"}}
            )
        else:
            dispatcher.utter_message(
                text="I'm connecting you with a healthcare provider who can better assist you. Please hold for a moment.",
                json_message={"custom": {"voice_emotion": "professional"}}
            )
        
        return []

class ValidateSymptomAssessmentForm(FormValidationAction):
    """Validate the symptom assessment form"""
    
    def name(self) -> Text:
        return "validate_symptom_assessment_form"
    
    def validate_symptoms(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate symptoms slot"""
        
        if slot_value and len(slot_value) > 0:
            return {"symptoms": slot_value}
        else:
            dispatcher.utter_message(text="Please describe your symptoms so I can help you better.")
            return {"symptoms": None}
    
    def validate_pain_level(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate pain level slot"""
        
        if slot_value and str(slot_value).isdigit():
            pain_level = int(slot_value)
            if 1 <= pain_level <= 10:
                return {"pain_level": str(pain_level)}
        
        dispatcher.utter_message(text="Please provide a number between 1 and 10 for your pain level.")
        return {"pain_level": None}