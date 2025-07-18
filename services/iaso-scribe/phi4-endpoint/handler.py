"""
RunPod Phi-4 Reasoning Plus Handler
Quantized Q6_K_L version for medical insights
"""

import os
import json
import runpod
from llama_cpp import Llama
import logging
import time
import urllib.request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configuration
PHI_MODEL_URL = "https://huggingface.co/bartowski/microsoft_Phi-4-reasoning-plus-GGUF/resolve/main/microsoft_Phi-4-reasoning-plus-Q6_K_L.gguf"
PHI_MODEL_PATH = "/runpod-volume/models/microsoft_Phi-4-reasoning-plus-Q6_K_L.gguf" if os.path.exists("/runpod-volume") else "/models/phi4.gguf"

# Initialize model globally
phi_model = None

def download_model_if_needed():
    """Download Phi-4 model if not present."""
    if not os.path.exists(PHI_MODEL_PATH):
        logger.info(f"Downloading Phi-4-reasoning-plus Q6_K_L model (12.28GB)...")
        os.makedirs(os.path.dirname(PHI_MODEL_PATH), exist_ok=True)
        
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100.0 / total_size, 100)
            print(f"Download progress: {percent:.1f}%", end='\r')
        
        urllib.request.urlretrieve(PHI_MODEL_URL, PHI_MODEL_PATH, reporthook=download_progress)
        print("\nModel downloaded successfully!")

def initialize_model():
    """Initialize Phi-4 model if not already loaded."""
    global phi_model
    
    if phi_model is None:
        download_model_if_needed()
        
        logger.info("Loading Phi-4-reasoning-plus model...")
        start_time = time.time()
        
        # Detect GPU layers
        n_gpu_layers = -1 if os.environ.get("DEVICE", "cuda") == "cuda" else 0
        
        phi_model = Llama(
            model_path=PHI_MODEL_PATH,
            n_ctx=16384,  # 16K context
            n_threads=8,
            n_gpu_layers=n_gpu_layers,
            verbose=False,
            use_mlock=True,
            use_mmap=True,
            seed=-1,
            f16_kv=True,
            logits_all=False,
            n_batch=512
        )
        
        logger.info(f"Phi-4 model loaded in {time.time() - start_time:.2f}s")

def handler(job):
    """
    RunPod handler for Phi-4 medical reasoning.
    
    Input format:
    {
        "input": {
            "text": "Medical transcription or text to analyze",
            "prompt_type": "medical_insights" (optional),
            "max_tokens": 1024 (optional)
        }
    }
    """
    try:
        # Initialize model
        initialize_model()
        
        # Get input
        job_input = job["input"]
        text = job_input.get("text", "")
        prompt_type = job_input.get("prompt_type", "medical_insights")
        max_tokens = job_input.get("max_tokens", 1024)
        
        if not text:
            raise ValueError("No text input provided")
        
        # Build prompt based on type
        if prompt_type == "medical_insights":
            prompt = f"""<|system|>
You are an expert medical documentation assistant with step-by-step reasoning capabilities. Show your reasoning process clearly.
<|end|>
<|user|>
Analyze this medical transcription:

{text}

Provide a comprehensive analysis with visible reasoning:

## Step-by-Step Reasoning:
[Think through the medical information systematically]

## Medical Summary:
- Chief complaint and symptoms
- Key findings and diagnoses
- Medications and dosages
- Follow-up recommendations

## Clinical Assessment:
- Differential diagnosis considerations
- Risk factors identified
- Recommended actions

<|end|>
<|assistant|>"""
        else:
            # Custom prompt
            prompt = text
        
        # Generate response
        logger.info("Generating medical insights...")
        start_time = time.time()
        
        response = phi_model(
            prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1,
            stop=["<|end|>", "<|user|>", "<|system|>"]
        )
        
        generation_time = time.time() - start_time
        generated_text = response['choices'][0]['text'].strip()
        
        return {
            "insights": generated_text,
            "processing_time": generation_time,
            "tokens_generated": response['usage']['completion_tokens'],
            "model": "phi-4-reasoning-plus-Q6_K_L"
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {"error": str(e)}

# RunPod serverless entrypoint
runpod.serverless.start({"handler": handler})