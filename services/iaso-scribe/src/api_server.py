"""
IasoScribe API Server
FastAPI endpoints for medical transcription service
"""

import os
import tempfile
import asyncio
import json
import redis
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import numpy as np

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from medical_whisper_handler import MedicalWhisperHandler
from audio_preprocessor import AudioPreprocessor
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Metrics
transcription_requests = Counter('iaso_scribe_transcription_requests_total', 'Total transcription requests')
transcription_duration = Histogram('iaso_scribe_transcription_duration_seconds', 'Transcription duration')
active_transcriptions = Gauge('iaso_scribe_active_transcriptions', 'Number of active transcriptions')
transcription_errors = Counter('iaso_scribe_transcription_errors_total', 'Total transcription errors')

# Initialize FastAPI app
app = FastAPI(
    title="IasoScribe Medical Transcription API",
    description="Advanced medical speech-to-text service with clinical AI integration",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
whisper_handler = MedicalWhisperHandler(
    model_size=os.getenv("WHISPER_MODEL_SIZE", "medium"),
    device=os.getenv("DEVICE", "auto")
)
audio_preprocessor = AudioPreprocessor()

# Redis client for batch processing storage
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True
    )
    redis_client.ping()  # Test connection
except Exception as e:
    print(f"Redis connection failed: {e}. Batch processing will use in-memory storage.")
    redis_client = None

# In-memory storage fallback for batch processing
batch_results = {}

# Active WebSocket connections for streaming
active_connections: Dict[str, WebSocket] = {}

# Streaming transcription buffers
stream_buffers: Dict[str, List[bytes]] = {}

# Pydantic models
class TranscriptionRequest(BaseModel):
    """Request model for transcription"""
    audio_url: str = Field(..., description="URL of the audio file to transcribe")
    medical_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Medical context including specialty, chief complaint, etc."
    )
    language: str = Field(default="en", description="Language code")
    enable_vad: bool = Field(default=True, description="Enable voice activity detection")
    generate_note: bool = Field(default=False, description="Generate structured clinical note")
    note_template: str = Field(default="soap", description="Note template type (soap, progress, discharge)")

class TranscriptionResponse(BaseModel):
    """Response model for transcription"""
    transcript: str
    confidence: float
    duration: float
    medical_entities: Optional[Dict[str, Any]]
    structured_note: Optional[Dict[str, Any]]
    segments: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class BatchTranscriptionRequest(BaseModel):
    """Request model for batch transcription"""
    tasks: List[TranscriptionRequest]
    priority: str = Field(default="normal", description="Processing priority (low, normal, high)")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    services: Dict[str, str]
    model_loaded: bool

# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": "IasoScribe Medical Transcription",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Check service health
    clinical_ai_healthy = await whisper_handler.clinical_ai.is_available()
    services_status = {
        "whisper": "healthy" if whisper_handler else "unavailable",
        "clinical_ai": "healthy" if clinical_ai_healthy else "degraded",
        "audio_processor": "healthy"
    }
    
    return HealthResponse(
        status="healthy" if all(s == "healthy" for s in services_status.values()) else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        services=services_status,
        model_loaded=whisper_handler is not None
    )

@app.post("/api/v1/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(request: TranscriptionRequest):
    """
    Transcribe audio file with medical optimization
    
    - Accepts audio URL or base64 encoded audio
    - Applies medical vocabulary enhancement
    - Extracts clinical entities
    - Optionally generates structured notes
    """
    transcription_requests.inc()
    
    with transcription_duration.time():
        active_transcriptions.inc()
        
        try:
            # Process transcription
            result = await whisper_handler.transcribe_audio(
                audio_path=request.audio_url,
                specialty=request.medical_context.get("specialty", "general"),
                context=request.medical_context,
                language=request.language,
                enable_vad=request.enable_vad
            )
            
            # Generate structured note if requested
            if request.generate_note:
                note_result = await whisper_handler.generate_medical_note(
                    transcript=result["transcript"],
                    template=request.note_template,
                    specialty=request.medical_context.get("specialty", "general"),
                    entities=result.get("medical_entities")
                )
                result["structured_note"] = note_result
            
            return TranscriptionResponse(**result)
            
        except Exception as e:
            transcription_errors.inc()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            active_transcriptions.dec()

@app.post("/api/v1/transcribe/upload")
async def transcribe_upload(
    file: UploadFile = File(...),
    specialty: str = Form(default="general"),
    language: str = Form(default="en"),
    generate_note: bool = Form(default=False),
    note_template: str = Form(default="soap")
):
    """
    Transcribe uploaded audio file
    
    Accepts direct file uploads for transcription
    """
    transcription_requests.inc()
    
    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        with transcription_duration.time():
            active_transcriptions.inc()
            
            # Process transcription
            result = await whisper_handler.transcribe_audio(
                audio_path=tmp_path,
                specialty=specialty,
                context={"specialty": specialty},
                language=language
            )
            
            # Generate structured note if requested
            if generate_note:
                note_result = await whisper_handler.generate_medical_note(
                    transcript=result["transcript"],
                    template=note_template,
                    specialty=specialty,
                    entities=result.get("medical_entities")
                )
                result["structured_note"] = note_result
            
            return TranscriptionResponse(**result)
            
    except Exception as e:
        transcription_errors.inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        active_transcriptions.dec()
        # Clean up temporary file
        os.unlink(tmp_path)

@app.post("/api/v1/transcribe/batch")
async def transcribe_batch(
    request: BatchTranscriptionRequest,
    background_tasks: BackgroundTasks
):
    """
    Batch transcription endpoint
    
    Process multiple transcription tasks asynchronously
    """
    batch_id = str(uuid.uuid4())
    
    # Queue tasks for background processing
    for idx, task in enumerate(request.tasks):
        background_tasks.add_task(
            process_batch_task,
            batch_id=batch_id,
            task_id=f"{batch_id}-{idx}",
            task=task
        )
    
    return {
        "batch_id": batch_id,
        "task_count": len(request.tasks),
        "status": "processing",
        "message": "Batch transcription started. Use batch_id to check status."
    }

@app.websocket("/api/v1/transcribe/stream")
async def transcribe_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time transcription
    
    Supports streaming audio chunks for live transcription
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    active_connections[session_id] = websocket
    
    try:
        # Initialize streaming session
        audio_buffer = []
        
        while True:
            # Receive audio chunk
            data = await websocket.receive_json()
            
            if data["type"] == "audio_chunk":
                # Add to buffer
                audio_buffer.append(data["audio"])
                
                # Process when buffer reaches threshold (e.g., 1 second)
                if len(audio_buffer) >= 16000:  # 1 second at 16kHz
                    try:
                        # Convert audio buffer to numpy array
                        audio_chunk = np.array(audio_buffer, dtype=np.float32)
                        
                        # Save to temporary file for processing
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                            # Write audio chunk as WAV
                            import soundfile as sf
                            sf.write(tmp.name, audio_chunk, 16000)
                            tmp_path = tmp.name
                        
                        # Process chunk with Whisper
                        result = await whisper_handler.transcribe_audio(
                            audio_path=tmp_path,
                            specialty=data.get("specialty", "general"),
                            context=data.get("context", {}),
                            language=data.get("language", "en"),
                            enable_vad=data.get("enable_vad", True)
                        )
                        
                        # Clean up temporary file
                        os.unlink(tmp_path)
                        
                        # Send partial transcript
                        await websocket.send_json({
                            "type": "partial_transcript",
                            "text": result["transcript"],
                            "confidence": result.get("language_probability", 0.0),
                            "segments": result.get("segments", []),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Transcription error: {str(e)}"
                        })
                    
                    # Clear buffer
                    audio_buffer = []
                    
            elif data["type"] == "end_stream":
                # Process final audio chunk if any remains
                if audio_buffer:
                    try:
                        # Convert remaining audio buffer to numpy array
                        audio_chunk = np.array(audio_buffer, dtype=np.float32)
                        
                        # Save to temporary file for processing
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                            import soundfile as sf
                            sf.write(tmp.name, audio_chunk, 16000)
                            tmp_path = tmp.name
                        
                        # Process final chunk with Whisper
                        result = await whisper_handler.transcribe_audio(
                            audio_path=tmp_path,
                            specialty=data.get("specialty", "general"),
                            context=data.get("context", {}),
                            language=data.get("language", "en"),
                            enable_vad=data.get("enable_vad", True)
                        )
                        
                        # Clean up temporary file
                        os.unlink(tmp_path)
                        
                        # Send final transcript with entities
                        await websocket.send_json({
                            "type": "final_transcript",
                            "text": result["transcript"],
                            "confidence": result.get("language_probability", 0.0),
                            "segments": result.get("segments", []),
                            "entities": result.get("medical_entities", {}),
                            "processing_speed": result.get("processing_speed", 0.0),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Final transcription error: {str(e)}"
                        })
                else:
                    # No remaining audio, send empty final transcript
                    await websocket.send_json({
                        "type": "final_transcript",
                        "text": "",
                        "confidence": 0.0,
                        "segments": [],
                        "entities": {},
                        "timestamp": datetime.utcnow().isoformat()
                    })
                break
                
    except WebSocketDisconnect:
        del active_connections[session_id]
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        await websocket.close()

@app.post("/api/v1/generate-note")
async def generate_note(
    transcript: str = Form(...),
    template: str = Form(default="soap"),
    specialty: str = Form(default="general")
):
    """
    Generate structured clinical note from transcript
    
    Converts free-text transcript into structured clinical documentation
    """
    try:
        # Extract entities first
        entities = None
        if await whisper_handler.clinical_ai.is_available():
            entities_result = await whisper_handler.clinical_ai.extract_entities(
                transcript,
                specialty=specialty
            )
            entities = entities_result.get("entities")
        
        # Generate note
        note = await whisper_handler.generate_medical_note(
            transcript=transcript,
            template=template,
            specialty=specialty,
            entities=entities
        )
        
        return note
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/audio-info")
async def get_audio_info(audio_url: str):
    """
    Get audio file information
    
    Returns duration, format, and other metadata
    """
    try:
        # Download if URL
        if audio_url.startswith("http"):
            audio_path = audio_preprocessor.download_audio(audio_url)
        else:
            audio_path = audio_url
        
        info = audio_preprocessor.get_audio_info(audio_path)
        
        # Clean up if downloaded
        if audio_url.startswith("http"):
            os.unlink(audio_path)
        
        return info
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return StreamingResponse(
        generate_latest(),
        media_type="text/plain"
    )

# Background task processor
async def process_batch_task(batch_id: str, task_id: str, task: TranscriptionRequest):
    """
    Process individual batch transcription task
    """
    # This would typically write results to a database or cache
    # For now, just process the transcription
    try:
        result = await whisper_handler.transcribe_audio(
            audio_path=task.audio_url,
            specialty=task.medical_context.get("specialty", "general"),
            context=task.medical_context,
            language=task.language,
            enable_vad=task.enable_vad
        )
        
        # Store result using Redis or in-memory storage
        await store_batch_result(batch_id, task_id, result)
        
    except Exception as e:
        # Store error using Redis or in-memory storage
        await store_batch_error(batch_id, task_id, str(e))

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Warm up models
    if os.getenv("WARM_UP_MODEL", "true").lower() == "true":
        try:
            # Process a short test audio to load models
            test_audio = AudioPreprocessor().process(
                # Generate 1 second of silence
                audio_input=AudioPreprocessor()._normalize_audio(
                    audio=AudioPreprocessor()._apply_compression(
                        audio=AudioPreprocessor()._enhance_speech(
                            audio=AudioPreprocessor()._reduce_noise(
                                audio=AudioPreprocessor()._optimize_for_medical(
                                    audio=AudioPreprocessor()._remove_silence(
                                        audio=AudioPreprocessor()._load_audio(
                                            file_path="/dev/null"
                                        )[0],
                                        sr=16000
                                    ),
                                    sr=16000
                                ),
                                sr=16000
                            ),
                            sr=16000
                        ),
                        threshold=0.3,
                        ratio=2.0
                    )
                )
            )
            print("Model warm-up completed")
        except:
            print("Model warm-up skipped")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Close any open connections
    if hasattr(whisper_handler, 'clinical_ai'):
        await whisper_handler.clinical_ai.close()
    
    # Close WebSocket connections
    for websocket in active_connections.values():
        await websocket.close()

# Batch processing storage functions
async def store_batch_result(batch_id: str, task_id: str, result: Dict[str, Any]):
    """Store batch transcription result"""
    try:
        if redis_client:
            # Store in Redis with TTL of 24 hours
            redis_client.setex(
                f"batch:{batch_id}:{task_id}",
                86400,  # 24 hours
                json.dumps({
                    "status": "completed",
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
        else:
            # Store in memory
            if batch_id not in batch_results:
                batch_results[batch_id] = {}
            batch_results[batch_id][task_id] = {
                "status": "completed",
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        print(f"Failed to store batch result: {e}")

async def store_batch_error(batch_id: str, task_id: str, error: str):
    """Store batch transcription error"""
    try:
        if redis_client:
            # Store in Redis with TTL of 24 hours
            redis_client.setex(
                f"batch:{batch_id}:{task_id}",
                86400,  # 24 hours
                json.dumps({
                    "status": "error",
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
        else:
            # Store in memory
            if batch_id not in batch_results:
                batch_results[batch_id] = {}
            batch_results[batch_id][task_id] = {
                "status": "error",
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        print(f"Failed to store batch error: {e}")

@app.get("/api/v1/batch/{batch_id}/status")
async def get_batch_status(batch_id: str):
    """Get batch transcription status"""
    try:
        if redis_client:
            # Get all keys for this batch
            keys = redis_client.keys(f"batch:{batch_id}:*")
            results = {}
            for key in keys:
                task_id = key.split(":")[-1]
                data = json.loads(redis_client.get(key))
                results[task_id] = data
        else:
            # Get from memory
            results = batch_results.get(batch_id, {})
        
        # Calculate batch status
        if not results:
            return {"batch_id": batch_id, "status": "not_found"}
        
        total_tasks = len(results)
        completed_tasks = sum(1 for r in results.values() if r["status"] == "completed")
        error_tasks = sum(1 for r in results.values() if r["status"] == "error")
        
        if completed_tasks + error_tasks == total_tasks:
            batch_status = "completed"
        else:
            batch_status = "processing"
        
        return {
            "batch_id": batch_id,
            "status": batch_status,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "error_tasks": error_tasks,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/batch/{batch_id}/results")
async def get_batch_results(batch_id: str):
    """Get batch transcription results"""
    try:
        if redis_client:
            # Get all keys for this batch
            keys = redis_client.keys(f"batch:{batch_id}:*")
            results = {}
            for key in keys:
                task_id = key.split(":")[-1]
                data = json.loads(redis_client.get(key))
                results[task_id] = data
        else:
            # Get from memory
            results = batch_results.get(batch_id, {})
        
        if not results:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        return {
            "batch_id": batch_id,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        workers=int(os.getenv("WORKERS", 1)),
        log_level=os.getenv("LOG_LEVEL", "info")
    )