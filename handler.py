"""
RunPod serverless handler for IASO Scribe service.
Combines Whisper transcription with Phi-4-reasoning-plus medical insights generation.
Uses GGUF Q6_K_L quantization for optimal quality and performance.
Production-ready with error handling, logging, and monitoring.
"""

import os
import json
import base64
import tempfile
import runpod
from faster_whisper import WhisperModel
from llama_cpp import Llama
import torch
import requests
from typing import Dict, Any, Optional
import urllib.request
import logging
import time
import traceback

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Model paths (will be downloaded on first run)
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "medium")
PHI_MODEL_URL = os.environ.get(
    "PHI_MODEL_URL", 
    "https://huggingface.co/bartowski/microsoft_Phi-4-reasoning-plus-GGUF/resolve/main/microsoft_Phi-4-reasoning-plus-Q6_K_L.gguf"
)
# Use /workspace if available (network volume), fallback to /models
MODEL_BASE_PATH = "/workspace/models" if os.path.exists("/workspace") else "/models"
PHI_MODEL_PATH = os.environ.get("PHI_MODEL_PATH", f"{MODEL_BASE_PATH}/microsoft_Phi-4-reasoning-plus-Q6_K_L.gguf")

# Initialize models globally for reuse
whisper_model = None
phi_model = None

def download_model_if_needed():
    """Download Phi-4-reasoning-plus model if not already present."""
    if not os.path.exists(PHI_MODEL_PATH):
        logger.info(f"Model not found at {PHI_MODEL_PATH}")
        logger.info(f"Downloading Phi-4-reasoning-plus Q6_K_L model (12.28GB)...")
        
        # Create directory with proper permissions
        model_dir = os.path.dirname(PHI_MODEL_PATH)
        os.makedirs(model_dir, exist_ok=True)
        logger.info(f"Created directory: {model_dir}")
        
        # Download with progress tracking
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100.0 / total_size, 100)
            print(f"Download progress: {percent:.1f}%", end='\r')
        
        try:
            urllib.request.urlretrieve(PHI_MODEL_URL, PHI_MODEL_PATH, reporthook=download_progress)
            print("\nModel downloaded successfully!")
            
            # Verify file size
            file_size = os.path.getsize(PHI_MODEL_PATH)
            expected_size_min = 11.0 * 1024 * 1024 * 1024  # 11GB minimum
            expected_size_max = 13.0 * 1024 * 1024 * 1024  # 13GB maximum
            if file_size < expected_size_min or file_size > expected_size_max:
                raise ValueError(f"Downloaded file size {file_size} bytes is outside expected range (11-13GB)")
            logger.info(f"Model file size verified: {file_size / (1024**3):.2f}GB")
                
        except Exception as e:
            # Clean up partial download
            if os.path.exists(PHI_MODEL_PATH):
                os.remove(PHI_MODEL_PATH)
            raise RuntimeError(f"Failed to download model: {str(e)}")

def initialize_models():
    """Initialize models if not already loaded."""
    global whisper_model, phi_model
    
    if whisper_model is None:
        logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
        
        # Check CUDA availability and version
        if torch.cuda.is_available():
            logger.info(f"CUDA available: {torch.version.cuda}")
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            # Log GPU memory
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            gpu_memory_allocated = torch.cuda.memory_allocated(0) / (1024**3)
            logger.info(f"GPU memory: {gpu_memory:.2f} GB total, {gpu_memory_allocated:.2f} GB allocated")
            device = "cuda"
            compute_type = "float16"
        else:
            logger.warning("CUDA not available, falling back to CPU")
            device = "cpu"
            compute_type = "int8"
        
        logger.info(f"Whisper device: {device}, compute type: {compute_type}")
        start_time = time.time()
        
        try:
            # Add debug environment variable to get more info
            os.environ['CT2_VERBOSE'] = '3'
            
            whisper_model = WhisperModel(
                WHISPER_MODEL, 
                device=device, 
                compute_type=compute_type,
                download_root=f"{MODEL_BASE_PATH}/whisper",  # Use network volume if available
                cpu_threads=4,  # Limit CPU threads to prevent memory issues
                device_index=0  # Explicitly set GPU index
            )
            logger.info(f"Whisper model loaded in {time.time() - start_time:.2f}s")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    if phi_model is None:
        # Download model if needed
        download_model_if_needed()
        
        logger.info(f"Loading Phi-4-reasoning-plus GGUF model from: {PHI_MODEL_PATH}")
        start_time = time.time()
        
        # Check CUDA availability for llama.cpp
        n_gpu_layers = -1 if torch.cuda.is_available() else 0
        logger.info(f"GPU layers for Phi-4: {n_gpu_layers}")
        
        try:
            # Initialize llama.cpp with optimal settings for Phi-4-reasoning-plus
            phi_model = Llama(
                model_path=PHI_MODEL_PATH,
                n_ctx=4096,  # Context window
                n_threads=min(8, os.cpu_count() or 8),  # CPU threads
                n_gpu_layers=n_gpu_layers,  # Use all GPU layers if available
                verbose=False,
                use_mlock=True,  # Lock model in memory
                use_mmap=True,   # Memory-map the model
                seed=-1,  # Random seed
                f16_kv=True,  # Use f16 for key/value cache
                logits_all=False,  # Only compute logits for last token
                vocab_only=False,  # Load full model
                n_batch=512,  # Batch size for prompt processing
            )
            logger.info(f"Phi-4 model loaded in {time.time() - start_time:.2f}s")
        except Exception as e:
            logger.error(f"Failed to load Phi-4 model: {str(e)}")
            raise

def download_audio(url: str) -> str:
    """Download audio from URL to temporary file."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(response.content)
        return tmp_file.name

def transcribe_audio(audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """Transcribe audio using Faster Whisper."""
    try:
        # Log before transcription
        logger.info(f"Transcribing audio file: {audio_path}")
        logger.info(f"File size: {os.path.getsize(audio_path) / (1024*1024):.2f} MB")
        
        # Force garbage collection before transcription
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info(f"GPU memory before transcription: {torch.cuda.memory_allocated(0) / (1024**3):.2f} GB")
        
        # Use simpler parameters that are known to work
        segments, info = whisper_model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                threshold=0.5,
                min_speech_duration_ms=250,
                max_speech_duration_s=float('inf'),
                min_silence_duration_ms=2000,
                speech_pad_ms=400
            )
        )
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            logger.error("GPU out of memory, retrying with smaller beam size")
            # Retry with reduced parameters
            segments, info = whisper_model.transcribe(
                audio_path,
                language=language,
                beam_size=1,
                best_of=1,
                temperature=0,
                vad_filter=False
            )
        else:
            raise
    
    # Collect all segments
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
    
    return {
        "text": " ".join(full_text),
        "segments": transcription_segments,
        "language": info.language,
        "duration": info.duration
    }

def generate_medical_insights(transcription: str) -> str:
    """Generate medical insights using Phi-4-reasoning-plus with advanced reasoning capabilities."""
    # Phi-4-reasoning-plus optimized prompt for medical reasoning
    prompt = f"""<|system|>
You are an expert medical documentation assistant powered by Phi-4-reasoning-plus, with advanced reasoning and analytical capabilities. Your role is to analyze medical transcriptions with clinical precision and generate comprehensive documentation.
<|end|>
<|user|>
Analyze the following medical transcription using step-by-step reasoning:

Transcription: {transcription}

Please provide a comprehensive analysis including:

1. **Medical Entity Extraction**: Identify all clinically relevant entities
   - Symptoms and their characteristics (onset, duration, severity)
   - Conditions or diagnoses mentioned
   - Medications (name, dosage, frequency)
   - Procedures or tests performed/ordered
   - Vital signs or measurements

2. **Clinical Reasoning**: Apply medical reasoning to the findings
   - Relationship between symptoms and potential conditions
   - Drug-condition interactions
   - Clinical significance of findings
   - Risk factors identified

3. **Differential Diagnosis** (if applicable):
   - Most likely diagnosis based on presented symptoms
   - Alternative diagnoses to consider
   - Additional tests or information needed

4. **Care Plan Recommendations**:
   - Immediate actions required
   - Follow-up recommendations
   - Patient education points
   - Referrals if needed

5. **SOAP Note**: Structure the information as:
   - Subjective: Patient-reported symptoms and concerns
   - Objective: Clinical findings and measurements
   - Assessment: Clinical judgment and diagnosis
   - Plan: Treatment and follow-up actions

Provide your analysis:
<|end|>
<|assistant|>"""
    
    # Generate response using llama.cpp
    response = phi_model(
        prompt,
        max_tokens=1024,  # Generous token limit for detailed analysis
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repeat_penalty=1.1,
        stop=["<|end|>", "<|user|>", "<|system|>"]
    )
    
    # Extract the generated text
    generated_text = response['choices'][0]['text']
    
    return generated_text.strip()

def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod handler function for IASO Scribe.
    Production-ready with comprehensive error handling and logging.
    
    Expected input format:
    {
        "input": {
            "audio": "URL or base64 encoded audio",
            "language": "en" (optional),
            "generate_insights": true (optional, default: true),
            "return_segments": false (optional)
        }
    }
    """
    start_time = time.time()
    request_id = job.get("id", "unknown")
    audio_path = None
    
    try:
        logger.info(f"Processing request {request_id}")
        
        # Initialize models
        initialize_models()
        
        # Validate input
        if "input" not in job:
            raise ValueError("Missing 'input' field in request")
            
        job_input = job["input"]
        audio_input = job_input.get("audio")
        language = job_input.get("language")
        generate_insights = job_input.get("generate_insights", True)
        return_segments = job_input.get("return_segments", False)
        
        if not audio_input:
            raise ValueError("No audio input provided")
        
        # Handle audio input (URL or base64)
        logger.info(f"Processing audio input type: {'URL' if audio_input.startswith(('http://', 'https://')) else 'base64'}")
        
        if audio_input.startswith(("http://", "https://")):
            audio_path = download_audio(audio_input)
        else:
            # Assume base64 encoded
            try:
                audio_data = base64.b64decode(audio_input)
            except Exception as e:
                raise ValueError(f"Invalid base64 audio data: {str(e)}")
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_data)
                audio_path = tmp_file.name
        
        # Transcribe audio
        logger.info("Starting transcription...")
        transcription_start = time.time()
        transcription_result = transcribe_audio(audio_path, language)
        transcription_time = time.time() - transcription_start
        logger.info(f"Transcription completed in {transcription_time:.2f}s")
        
        # Prepare response
        response = {
            "transcription": transcription_result["text"],
            "language": transcription_result["language"],
            "duration": transcription_result["duration"],
            "processing_time": {
                "transcription": transcription_time
            }
        }
        
        if return_segments:
            response["segments"] = transcription_result["segments"]
        
        # Generate medical insights if requested
        if generate_insights and transcription_result["text"]:
            logger.info("Generating medical insights...")
            insights_start = time.time()
            insights = generate_medical_insights(transcription_result["text"])
            insights_time = time.time() - insights_start
            logger.info(f"Insights generated in {insights_time:.2f}s")
            
            response["medical_insights"] = insights
            response["processing_time"]["insights"] = insights_time
        
        # Total processing time
        total_time = time.time() - start_time
        response["processing_time"]["total"] = total_time
        
        logger.info(f"Request {request_id} completed successfully in {total_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"Error processing request {request_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return structured error response
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "request_id": request_id,
            "processing_time": time.time() - start_time
        }
        
    finally:
        # Clean up temporary file
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
                logger.debug(f"Cleaned up temporary file: {audio_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")

# RunPod serverless entrypoint
runpod.serverless.start({"handler": handler})