"""
RunPod Whisper Medium Handler
Based on RunPod's official faster-whisper implementation
"""

import os
import json
import base64
import tempfile
import runpod
from faster_whisper import WhisperModel
import requests
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize model globally
whisper_model = None

def initialize_model():
    """Initialize Whisper model if not already loaded."""
    global whisper_model
    
    if whisper_model is None:
        logger.info("Loading Whisper medium model...")
        start_time = time.time()
        
        # Use GPU if available
        device = "cuda" if os.environ.get("DEVICE", "cuda") == "cuda" else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        
        whisper_model = WhisperModel(
            "medium",
            device=device,
            compute_type=compute_type,
            download_root="/runpod-volume/whisper-models" if os.path.exists("/runpod-volume") else "/models"
        )
        
        logger.info(f"Whisper model loaded in {time.time() - start_time:.2f}s")

def download_audio(url: str) -> str:
    """Download audio from URL."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(response.content)
        return tmp_file.name

def handler(job):
    """
    RunPod handler for Whisper transcription.
    
    Input format:
    {
        "input": {
            "audio": "URL or base64 encoded audio",
            "language": "en" (optional),
            "return_segments": false (optional)
        }
    }
    """
    try:
        # Initialize model
        initialize_model()
        
        # Get input
        job_input = job["input"]
        audio_input = job_input.get("audio")
        language = job_input.get("language")
        return_segments = job_input.get("return_segments", False)
        
        if not audio_input:
            raise ValueError("No audio input provided")
        
        # Handle audio input
        if audio_input.startswith(("http://", "https://")):
            audio_path = download_audio(audio_input)
        else:
            # Base64 encoded
            audio_data = base64.b64decode(audio_input)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_data)
                audio_path = tmp_file.name
        
        # Transcribe
        logger.info("Starting transcription...")
        start_time = time.time()
        
        segments, info = whisper_model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_speech_duration_ms=250,
                max_speech_duration_s=float('inf'),
                min_silence_duration_ms=2000,
                speech_pad_ms=400
            )
        )
        
        # Collect results
        transcription_segments = []
        full_text = []
        
        for segment in segments:
            seg_dict = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            }
            transcription_segments.append(seg_dict)
            full_text.append(segment.text.strip())
        
        transcription_time = time.time() - start_time
        
        # Prepare response
        response = {
            "transcription": " ".join(full_text),
            "language": info.language,
            "duration": info.duration,
            "processing_time": transcription_time
        }
        
        if return_segments:
            response["segments"] = transcription_segments
        
        # Clean up
        if os.path.exists(audio_path):
            os.unlink(audio_path)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {"error": str(e)}

# RunPod serverless entrypoint
runpod.serverless.start({"handler": handler})