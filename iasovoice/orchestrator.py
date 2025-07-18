#!/usr/bin/env python3
"""
IasoVoice Orchestrator
Coordinates Amazon Connect, Whisper, RASA, and Polly for voice interactions
"""

import asyncio
import json
import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import base64
from dataclasses import dataclass, field
from enum import Enum

import httpx
import boto3
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
from pydantic import BaseModel

# Configuration
WHISPER_ENDPOINT_ID = os.getenv("WHISPER_ENDPOINT_ID", "rntxttrdl8uv3i")
PHI4_ENDPOINT_ID = os.getenv("PHI4_ENDPOINT_ID", "tmmwa4q8ax5sg4")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RASA_URL = os.getenv("RASA_URL", "http://localhost:5005")
CLINICAL_AI_URL = os.getenv("CLINICAL_AI_URL", "http://localhost:8002")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# AWS clients
polly_client = boto3.client('polly', region_name='us-east-1')
connect_client = boto3.client('connect', region_name='us-east-1')

# FastAPI app
app = FastAPI(title="IasoVoice Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis for session management
redis_client = None

@dataclass
class AudioBuffer:
    """Manages streaming audio chunks"""
    buffer: bytearray = field(default_factory=bytearray)
    sample_rate: int = 8000  # Amazon Connect uses 8kHz
    silence_threshold_ms: int = 1000
    last_audio_time: float = field(default_factory=lambda: datetime.now().timestamp())
    
    def add_chunk(self, chunk: bytes) -> bool:
        """Add audio chunk and return True if ready to process"""
        self.buffer.extend(chunk)
        self.last_audio_time = datetime.now().timestamp()
        
        # Process when we have at least 1 second of audio
        return len(self.buffer) >= self.sample_rate

    def get_audio_base64(self) -> str:
        """Get buffered audio as base64"""
        return base64.b64encode(self.buffer).decode('utf-8')
    
    def clear(self):
        """Clear the buffer"""
        self.buffer.clear()

@dataclass
class ConversationSession:
    """Maintains conversation state"""
    session_id: str
    call_id: str
    patient_id: Optional[str] = None
    phone_number: Optional[str] = None
    rasa_sender_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    audio_buffer: AudioBuffer = field(default_factory=AudioBuffer)
    conversation_history: list = field(default_factory=list)
    clinical_context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    authenticated: bool = False

class IasoVoiceOrchestrator:
    """Main orchestrator for voice interactions"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
        self.whisper_client = WhisperClient()
        self.rasa_client = RASAClient()
        self.clinical_client = ClinicalAIClient()
        self.polly_client = PollyClient()
    
    async def handle_connect_stream(self, websocket: WebSocket, call_id: str):
        """Handle Amazon Connect audio stream"""
        await websocket.accept()
        
        # Create session
        session = ConversationSession(
            session_id=str(uuid.uuid4()),
            call_id=call_id
        )
        self.sessions[call_id] = session
        
        try:
            # Send initial greeting
            initial_audio = await self._generate_greeting(session)
            await self._send_audio_to_connect(websocket, initial_audio)
            
            while True:
                # Receive message from Connect
                message = await websocket.receive_json()
                
                if message.get("type") == "audio":
                    # Handle audio chunk
                    audio_chunk = base64.b64decode(message["data"])
                    
                    if session.audio_buffer.add_chunk(audio_chunk):
                        # Process accumulated audio
                        await self._process_audio_turn(session, websocket)
                        session.audio_buffer.clear()
                
                elif message.get("type") == "metadata":
                    # Update session metadata
                    session.phone_number = message.get("phoneNumber")
                    
                elif message.get("type") == "disconnect":
                    break
                    
        except WebSocketDisconnect:
            pass
        finally:
            # Clean up session
            await self._end_session(session)
            if call_id in self.sessions:
                del self.sessions[call_id]
    
    async def _process_audio_turn(self, session: ConversationSession, websocket: WebSocket):
        """Process one turn of conversation"""
        
        # Step 1: Transcribe audio
        audio_base64 = session.audio_buffer.get_audio_base64()
        transcription = await self.whisper_client.transcribe(audio_base64)
        
        if not transcription:
            return
        
        # Add to history
        session.conversation_history.append({
            "speaker": "user",
            "text": transcription,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 2: Send to RASA
        rasa_response = await self.rasa_client.send_message(
            message=transcription,
            sender_id=session.rasa_sender_id,
            metadata={
                "patient_id": session.patient_id,
                "phone_number": session.phone_number,
                "authenticated": session.authenticated
            }
        )
        
        # Step 3: Process RASA response
        for response in rasa_response.get("responses", []):
            response_text = response.get("text", "")
            
            # Check if we need clinical data
            if response.get("custom", {}).get("needs_clinical_data"):
                clinical_data = await self._get_clinical_context(session)
                # Send back to RASA with context
                enhanced_response = await self.rasa_client.send_message(
                    message="/inform_clinical_context",
                    sender_id=session.rasa_sender_id,
                    metadata={"clinical_context": clinical_data}
                )
                response_text = enhanced_response["responses"][0]["text"]
            
            # Add to history
            session.conversation_history.append({
                "speaker": "assistant",
                "text": response_text,
                "timestamp": datetime.now().isoformat()
            })
            
            # Step 4: Generate speech
            emotion = response.get("custom", {}).get("voice_emotion", "neutral")
            audio_response = await self.polly_client.synthesize(
                text=response_text,
                emotion=emotion
            )
            
            # Step 5: Send audio back
            await self._send_audio_to_connect(websocket, audio_response)
    
    async def _generate_greeting(self, session: ConversationSession) -> bytes:
        """Generate initial greeting"""
        greeting = "Hello, this is your IASO health assistant. How can I help you today?"
        return await self.polly_client.synthesize(greeting, emotion="friendly")
    
    async def _get_clinical_context(self, session: ConversationSession) -> Dict[str, Any]:
        """Get clinical context for patient"""
        if not session.patient_id:
            return {}
        
        return await self.clinical_client.get_patient_context(session.patient_id)
    
    async def _send_audio_to_connect(self, websocket: WebSocket, audio: bytes):
        """Send audio back to Amazon Connect"""
        # Convert to 8kHz mono for Connect
        # In production, use proper audio processing library
        
        await websocket.send_json({
            "type": "audio",
            "data": base64.b64encode(audio).decode('utf-8')
        })
    
    async def _end_session(self, session: ConversationSession):
        """End conversation session"""
        # Generate SOAP note if medical conversation
        if len(session.conversation_history) > 2:
            try:
                # Call Phi-4 to generate SOAP note
                conversation_text = self._format_conversation(session.conversation_history)
                soap_note = await self._generate_soap_note(conversation_text)
                
                # Save to clinical system
                if session.patient_id and soap_note:
                    await self.clinical_client.save_soap_note(
                        patient_id=session.patient_id,
                        soap_note=soap_note,
                        encounter_metadata={
                            "type": "phone_consultation",
                            "duration": (datetime.now() - session.created_at).total_seconds(),
                            "call_id": session.call_id
                        }
                    )
            except Exception as e:
                print(f"Error generating SOAP note: {e}")
    
    def _format_conversation(self, history: list) -> str:
        """Format conversation history for SOAP generation"""
        lines = []
        for turn in history:
            speaker = "Patient" if turn["speaker"] == "user" else "Assistant"
            lines.append(f"{speaker}: {turn['text']}")
        return "\n".join(lines)
    
    async def _generate_soap_note(self, conversation: str) -> Optional[str]:
        """Generate SOAP note using Phi-4"""
        # Call Phi-4 via RunPod
        # Implementation would call the Phi-4 endpoint
        pass

class WhisperClient:
    """Client for Whisper transcription"""
    
    async def transcribe(self, audio_base64: str) -> Optional[str]:
        """Transcribe audio using Whisper"""
        url = f"https://api.runpod.ai/v2/{WHISPER_ENDPOINT_ID}/runsync"
        headers = {
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": {
                "audio": audio_base64,
                "language": "en",
                "vad_filter": True
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "COMPLETED":
                        return result["output"].get("transcription")
        except Exception as e:
            print(f"Whisper error: {e}")
        
        return None

class RASAClient:
    """Client for RASA dialog management"""
    
    async def send_message(self, message: str, sender_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to RASA"""
        url = f"{RASA_URL}/webhooks/rest/webhook"
        
        payload = {
            "sender": sender_id,
            "message": message,
            "metadata": metadata
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    return {"responses": response.json()}
        except Exception as e:
            print(f"RASA error: {e}")
        
        return {"responses": [{"text": "I'm having trouble understanding. Could you please repeat that?"}]}

class ClinicalAIClient:
    """Client for Clinical AI integration"""
    
    async def get_patient_context(self, patient_id: str) -> Dict[str, Any]:
        """Get patient clinical context"""
        # Implementation would call Clinical AI service
        return {
            "medications": [],
            "conditions": [],
            "recent_visits": []
        }
    
    async def save_soap_note(self, patient_id: str, soap_note: str, encounter_metadata: Dict[str, Any]):
        """Save SOAP note to clinical system"""
        # Implementation would save to clinical system
        pass

class PollyClient:
    """Client for Amazon Polly TTS"""
    
    async def synthesize(self, text: str, emotion: str = "neutral") -> bytes:
        """Convert text to speech using Polly"""
        
        # Add SSML tags for emotion
        ssml_text = self._add_emotion_ssml(text, emotion)
        
        try:
            response = polly_client.synthesize_speech(
                Text=ssml_text,
                TextType='ssml',
                OutputFormat='pcm',  # Raw audio for Connect
                VoiceId='Joanna',    # Or Matthew, Salli, etc.
                Engine='neural',
                SampleRate='8000'    # Match Connect's sample rate
            )
            
            return response['AudioStream'].read()
        except Exception as e:
            print(f"Polly error: {e}")
            # Return empty audio on error
            return b''
    
    def _add_emotion_ssml(self, text: str, emotion: str) -> str:
        """Add SSML tags for emotional speech"""
        emotion_styles = {
            "friendly": '<amazon:domain name="conversational">',
            "empathetic": '<amazon:domain name="conversational"><prosody rate="slow">',
            "urgent": '<prosody rate="fast" pitch="+5%">',
            "professional": '<amazon:domain name="news">'
        }
        
        style_open = emotion_styles.get(emotion, "")
        style_close = style_open.replace("<", "</").replace(" ", ">") if style_open else ""
        
        return f'<speak>{style_open}{text}{style_close}</speak>'

# WebSocket endpoint for Amazon Connect
@app.websocket("/connect/{call_id}")
async def connect_websocket(websocket: WebSocket, call_id: str):
    """Handle Amazon Connect WebSocket connection"""
    orchestrator = IasoVoiceOrchestrator()
    await orchestrator.handle_connect_stream(websocket, call_id)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "IasoVoice Orchestrator",
        "timestamp": datetime.now().isoformat()
    }

# Session management endpoints
@app.get("/sessions")
async def get_sessions():
    """Get active sessions"""
    # Implementation would return active sessions
    return {"sessions": []}

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get specific session details"""
    # Implementation would return session details
    return {"session_id": session_id}

# Initialize Redis on startup
@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_client = await redis.from_url(REDIS_URL)

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)