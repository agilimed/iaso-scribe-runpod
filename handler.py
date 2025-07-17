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

# Disable HF_TRANSFER if package not available
try:
    import hf_transfer
except ImportError:
    os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
    
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
if os.path.exists("/workspace"):
    MODEL_BASE_PATH = "/workspace/models"
    logger.info("Using network volume at /workspace for persistent model storage")
else:
    MODEL_BASE_PATH = "/models"
    logger.warning("Network volume not found at /workspace, using ephemeral /models directory")
    logger.warning("Models will need to be re-downloaded when workers restart!")

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
        if torch.cuda.is_available():
            n_gpu_layers = -1  # Use all layers on GPU
            logger.info(f"GPU layers for Phi-4: {n_gpu_layers} (GPU mode)")
            logger.info("Checking llama-cpp-python CUDA support...")
            try:
                # Test if llama-cpp was built with CUDA
                test_llama = Llama(model_path=PHI_MODEL_PATH, n_ctx=512, n_gpu_layers=1, verbose=False)
                del test_llama
                logger.info("✅ llama-cpp-python has CUDA support")
            except Exception as e:
                logger.warning(f"⚠️ llama-cpp-python CUDA test failed: {e}")
                logger.warning("Falling back to CPU mode for Phi-4")
                n_gpu_layers = 0
        else:
            n_gpu_layers = 0
            logger.warning("CUDA not available for Phi-4, using CPU mode")
        
        try:
            # Initialize llama.cpp with optimal settings for Phi-4-reasoning-plus
            phi_model = Llama(
                model_path=PHI_MODEL_PATH,
                n_ctx=16384,  # Increased context window for long medical conversations
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

def generate_medical_insights(transcription: str, stream_callback=None) -> str:
    """Generate medical insights using Phi-4-reasoning-plus with advanced reasoning capabilities.
    
    Args:
        transcription: The medical transcription text
        stream_callback: Optional callback function for streaming tokens (token, metadata)
    """
    
    # Check if transcription is too long and needs chunking
    max_chars = 8000  # Conservative limit to leave room for prompt and response
    
    if len(transcription) > max_chars:
        logger.info(f"Long transcription ({len(transcription)} chars), using summarization approach")
        
        # For very long transcriptions, focus on key medical information
        prompt = f"""<|system|>
You are an expert medical documentation assistant with step-by-step reasoning capabilities. Show your reasoning process clearly.
<|end|>
<|user|>
Analyze this medical transcription (showing first {max_chars} characters):

{transcription[:max_chars]}...

Provide a concise medical analysis with clear reasoning steps:

## Reasoning Process:
[Show your step-by-step thinking]

## Medical Summary:
1. Chief complaint and primary symptoms
2. Key medical findings and diagnoses
3. Critical medications and dosages
4. Essential follow-up actions
5. Any urgent medical concerns

Show your reasoning before each conclusion.
<|end|>
<|assistant|>"""
    else:
        # Original detailed prompt for shorter transcriptions
        prompt = f"""<|system|>
You are an expert medical documentation assistant powered by Phi-4-reasoning-plus, with advanced reasoning and analytical capabilities. Show your step-by-step reasoning process transparently.
<|end|>
<|user|>
Analyze the following medical transcription using step-by-step reasoning:

Transcription: {transcription}

Please provide a comprehensive analysis with visible reasoning:

## Step-by-Step Reasoning:
[Think through the medical information systematically]

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
    
    # Generate response using llama.cpp with streaming support
    if stream_callback:
        # Streaming mode - send tokens as they're generated with reasoning tracking
        generated_tokens = []
        current_section = "reasoning"  # Track what section we're in
        
        stream = phi_model(
            prompt,
            max_tokens=1024,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1,
            stop=["<|end|>", "<|user|>", "<|system|>"],
            stream=True
        )
        
        for output in stream:
            token = output['choices'][0]['text']
            generated_tokens.append(token)
            
            # Track which section we're in based on content
            full_text = ''.join(generated_tokens)
            if "## Medical Summary:" in full_text or "## Clinical Analysis:" in full_text:
                current_section = "analysis"
            elif "## SOAP Note:" in full_text:
                current_section = "soap"
            elif "## Care Plan:" in full_text:
                current_section = "plan"
            
            # Send token with metadata about current section
            stream_callback(token, {"section": current_section, "total_tokens": len(generated_tokens)})
            
        return ''.join(generated_tokens).strip()
    else:
        # Non-streaming mode (current behavior)
        response = phi_model(
            prompt,
            max_tokens=1024,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1,
            stop=["<|end|>", "<|user|>", "<|system|>"]
        )
        
        generated_text = response['choices'][0]['text']
        return generated_text.strip()

def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod handler function for IASO Scribe.
    Production-ready with comprehensive error handling and logging.
    
    Supports streaming mode for real-time insights generation.
    
    Expected input format:
    {
        "input": {
            "audio": "URL or base64 encoded audio",
            "language": "en" (optional),
            "generate_insights": true (optional, default: true),
            "return_segments": false (optional),
            "stream": false (optional, enables streaming response)
        }
    }
    
    Note: Streaming requires RunPod to support generator responses.
    Currently returns full response with reasoning visible.
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
            
            # Check if streaming is requested
            enable_stream = job_input.get("stream", False)
            
            if enable_stream:
                # Streaming mode - collect tokens with reasoning metadata
                streamed_sections = {
                    "reasoning": [],
                    "analysis": [],
                    "soap": [],
                    "plan": []
                }
                current_section_tokens = []
                
                def stream_collector(token, metadata):
                    """Collect streamed tokens by section"""
                    section = metadata.get("section", "reasoning")
                    current_section_tokens.append(token)
                    
                    # Log progress for debugging
                    if metadata.get("total_tokens", 0) % 50 == 0:
                        logger.info(f"Streaming progress: {metadata.get('total_tokens')} tokens, section: {section}")
                
                # Process with streaming
                insights = generate_medical_insights(transcription_result["text"], stream_callback=stream_collector)
                
                # Add streaming metadata to response
                response["streaming_enabled"] = True
                response["reasoning_visible"] = True
            else:
                # Non-streaming mode
                transcription_length = len(transcription_result["text"])
                
                if transcription_length > 10000:
                    # For very long transcriptions, process in semantic chunks
                    logger.info(f"Long transcription ({transcription_length} chars), using chunked processing")
                    
                    # Split by paragraphs/sentences for medical context preservation
                    chunks = transcription_result["text"].split('\n\n')
                    if len(chunks) == 1:  # No paragraph breaks, split by sentences
                        import re
                        chunks = re.split(r'(?<=[.!?])\s+', transcription_result["text"])
                    
                    # Process most recent/relevant chunk first (often contains summary)
                    relevant_text = '\n'.join(chunks[-min(len(chunks), 50):])  # Last 50 sentences
                    insights = generate_medical_insights(relevant_text)
                else:
                    # Standard processing for normal length
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