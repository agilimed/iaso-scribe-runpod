"""
RunPod serverless handler for IASO Scribe service.
Combines Whisper transcription with Phi-4-reasoning-plus medical insights generation.
Uses GGUF Q6_K_L quantization for optimal quality and performance.
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

# Model paths (will be downloaded on first run)
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "large-v3")
PHI_MODEL_URL = os.environ.get(
    "PHI_MODEL_URL", 
    "https://huggingface.co/bartowski/microsoft_Phi-4-reasoning-plus-GGUF/resolve/main/Phi-4-reasoning-plus-Q6_K_L.gguf"
)
PHI_MODEL_PATH = os.environ.get("PHI_MODEL_PATH", "/models/Phi-4-reasoning-plus-Q6_K_L.gguf")

# Initialize models globally for reuse
whisper_model = None
phi_model = None

def download_model_if_needed():
    """Download Phi-4-reasoning-plus model if not already present."""
    if not os.path.exists(PHI_MODEL_PATH):
        print(f"Downloading Phi-4-reasoning-plus Q6_K_L model (12.28GB)...")
        os.makedirs(os.path.dirname(PHI_MODEL_PATH), exist_ok=True)
        urllib.request.urlretrieve(PHI_MODEL_URL, PHI_MODEL_PATH)
        print("Model downloaded successfully!")

def initialize_models():
    """Initialize models if not already loaded."""
    global whisper_model, phi_model
    
    if whisper_model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL}")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        whisper_model = WhisperModel(WHISPER_MODEL, device=device, compute_type=compute_type)
    
    if phi_model is None:
        # Download model if needed
        download_model_if_needed()
        
        print(f"Loading Phi-4-reasoning-plus GGUF model from: {PHI_MODEL_PATH}")
        # Initialize llama.cpp with optimal settings for Phi-4-reasoning-plus
        phi_model = Llama(
            model_path=PHI_MODEL_PATH,
            n_ctx=4096,  # Context window
            n_threads=8,  # CPU threads
            n_gpu_layers=-1,  # Use all GPU layers if available
            verbose=False,
            use_mlock=True,  # Lock model in memory
            use_mmap=True,   # Memory-map the model
        )

def download_audio(url: str) -> str:
    """Download audio from URL to temporary file."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(response.content)
        return tmp_file.name

def transcribe_audio(audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """Transcribe audio using Faster Whisper."""
    segments, info = whisper_model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        best_of=5,
        temperature=0,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
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
    try:
        # Initialize models
        initialize_models()
        
        # Extract input
        job_input = job["input"]
        audio_input = job_input.get("audio")
        language = job_input.get("language")
        generate_insights = job_input.get("generate_insights", True)
        return_segments = job_input.get("return_segments", False)
        
        if not audio_input:
            raise ValueError("No audio input provided")
        
        # Handle audio input (URL or base64)
        if audio_input.startswith(("http://", "https://")):
            audio_path = download_audio(audio_input)
        else:
            # Assume base64 encoded
            audio_data = base64.b64decode(audio_input)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_data)
                audio_path = tmp_file.name
        
        # Transcribe audio
        transcription_result = transcribe_audio(audio_path, language)
        
        # Clean up temporary file
        os.unlink(audio_path)
        
        # Prepare response
        response = {
            "transcription": transcription_result["text"],
            "language": transcription_result["language"],
            "duration": transcription_result["duration"]
        }
        
        if return_segments:
            response["segments"] = transcription_result["segments"]
        
        # Generate medical insights if requested
        if generate_insights and transcription_result["text"]:
            insights = generate_medical_insights(transcription_result["text"])
            response["medical_insights"] = insights
        
        return response
        
    except Exception as e:
        return {"error": str(e)}

# RunPod serverless entrypoint
runpod.serverless.start({"handler": handler})