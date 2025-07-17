"""
RunPod Phi-4 Streaming Handler with Reasoning
Supports both sync and streaming responses with step-by-step reasoning
"""

import os
import json
import runpod
from llama_cpp import Llama
import logging
import time
import urllib.request
from typing import Generator, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configuration
PHI_MODEL_URL = "https://huggingface.co/bartowski/microsoft_Phi-4-reasoning-plus-GGUF/resolve/main/microsoft_Phi-4-reasoning-plus-Q6_K_L.gguf"
MODEL_DIR = "/runpod-volume/models" if os.path.exists("/runpod-volume") else "/models"
PHI_MODEL_PATH = os.path.join(MODEL_DIR, "microsoft_Phi-4-reasoning-plus-Q6_K_L.gguf")

# Initialize model globally
phi_model = None

def download_model_if_needed():
    """Download Phi-4 model if not present."""
    if not os.path.exists(PHI_MODEL_PATH):
        logger.info(f"Downloading Phi-4-reasoning-plus Q6_K_L model (12.28GB)...")
        os.makedirs(MODEL_DIR, exist_ok=True)
        
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100.0 / total_size, 100)
            print(f"Download progress: {percent:.1f}%", end='\r')
        
        try:
            urllib.request.urlretrieve(PHI_MODEL_URL, PHI_MODEL_PATH, reporthook=download_progress)
            print("\nModel downloaded successfully!")
            logger.info(f"Model saved to {PHI_MODEL_PATH}")
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            raise

def initialize_model():
    """Initialize Phi-4 model if not already loaded."""
    global phi_model
    
    if phi_model is None:
        download_model_if_needed()
        
        logger.info("Loading Phi-4-reasoning-plus model...")
        start_time = time.time()
        
        # Check for GPU
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                logger.info(f"CUDA available: {torch.version.cuda}")
                logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
                n_gpu_layers = -1  # Use all layers on GPU
            else:
                logger.warning("CUDA not available, using CPU")
                n_gpu_layers = 0
        except ImportError:
            logger.warning("PyTorch not installed, assuming CPU mode")
            n_gpu_layers = 0
        
        try:
            phi_model = Llama(
                model_path=PHI_MODEL_PATH,
                n_ctx=32768,  # 32K context window for long medical documents
                n_threads=min(8, os.cpu_count() or 8),
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
            logger.info(f"GPU layers: {n_gpu_layers}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

def build_prompt_with_reasoning(text: str, prompt_type: str) -> str:
    """Build prompt that encourages step-by-step reasoning."""
    
    if prompt_type == "medical_insights":
        prompt = f"""<|system|>
You are an expert medical documentation assistant. Always show your step-by-step reasoning process before providing your final answer.
<|end|>
<|user|>
Analyze this medical transcription with step-by-step reasoning:

{text}

First, show your reasoning process:
1. Identify key clinical information
2. Analyze symptoms and findings
3. Consider differential diagnoses
4. Evaluate treatment options

Then provide:
1. Chief complaint and key symptoms
2. Medical findings and observations
3. Relevant medications with dosages
4. Clinical assessment and diagnosis considerations
5. Recommended follow-up actions
6. Any urgent concerns or red flags
<|end|>
<|assistant|>Let me analyze this medical transcription step by step.

**Step 1: Identifying Key Clinical Information**
"""
    
    elif prompt_type == "soap":
        prompt = f"""<|system|>
You are an expert medical scribe. Show your reasoning process when converting transcriptions to SOAP notes.
<|end|>
<|user|>
Convert this medical transcription into a SOAP note with reasoning:

{text}

First, explain your reasoning:
- What information belongs in Subjective vs Objective?
- What clinical assessments can be made?
- What treatment plans are appropriate?

Then format as:

SUBJECTIVE:
[Patient's complaints, symptoms, and history as reported]

OBJECTIVE:
[Measurable findings, vital signs, exam results, lab values]

ASSESSMENT:
[Clinical judgment, differential diagnosis, problem list]

PLAN:
[Treatment plan, medications, follow-up, patient education]
<|end|>
<|assistant|>I'll analyze this transcription and convert it to a SOAP note format.

**Reasoning Process:**
"""
    
    elif prompt_type == "summary":
        prompt = f"""<|system|>
You are a medical documentation specialist. Show your analytical process when creating clinical summaries.
<|end|>
<|user|>
Summarize this medical encounter with reasoning:

{text}

First, show your analysis:
- What are the most critical findings?
- What information is essential vs supplementary?
- What follow-up is crucial?

Then provide a concise clinical summary including:
- Chief complaint
- Key findings
- Diagnosis/Assessment
- Treatment plan
- Follow-up requirements
<|end|>
<|assistant|>Let me analyze this medical encounter systematically.

**Analysis Process:**
"""
    else:
        # Direct prompt without special formatting
        prompt = text
    
    return prompt

def stream_response(prompt: str, max_tokens: int, temperature: float) -> Generator[Dict[str, Any], None, None]:
    """Stream tokens as they're generated."""
    
    # Create stream
    stream = phi_model(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.9,
        top_k=40,
        repeat_penalty=1.1,
        stop=["<|end|>", "<|user|>", "<|system|>"],
        stream=True
    )
    
    start_time = time.time()
    total_tokens = 0
    accumulated_text = ""
    
    for output in stream:
        token = output['choices'][0]['text']
        accumulated_text += token
        total_tokens += 1
        
        # Calculate current metrics
        elapsed = time.time() - start_time
        tokens_per_second = total_tokens / elapsed if elapsed > 0 else 0
        
        yield {
            "token": token,
            "accumulated_text": accumulated_text,
            "tokens_generated": total_tokens,
            "elapsed_time": elapsed,
            "tokens_per_second": round(tokens_per_second, 1)
        }

def handler(job):
    """
    RunPod handler supporting both sync and streaming modes.
    
    Input format:
    {
        "input": {
            "text": "Medical transcription or text to analyze",
            "prompt_type": "medical_insights" (optional),
            "max_tokens": 4096 (optional),
            "temperature": 0.7 (optional),
            "stream": false (optional)
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
        max_tokens = job_input.get("max_tokens", 4096)  # Default 4096 for full documents
        temperature = job_input.get("temperature", 0.7)
        stream = job_input.get("stream", False)
        
        if not text:
            raise ValueError("No text input provided")
        
        # Build prompt with reasoning
        prompt = build_prompt_with_reasoning(text, prompt_type)
        
        if stream:
            # Return generator for streaming
            logger.info("Starting streaming generation...")
            
            def generate_stream():
                """Yield streaming responses in RunPod format."""
                for chunk in stream_response(prompt, max_tokens, temperature):
                    yield {
                        "status": "streaming",
                        "output": chunk
                    }
                
                # Final message
                yield {
                    "status": "completed",
                    "output": {
                        "message": "Streaming completed",
                        "model": "phi-4-reasoning-plus-Q6_K_L"
                    }
                }
            
            return generate_stream()
        
        else:
            # Sync mode - return complete response
            logger.info("Generating medical insights (sync mode)...")
            start_time = time.time()
            
            response = phi_model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1,
                stop=["<|end|>", "<|user|>", "<|system|>"]
            )
            
            generation_time = time.time() - start_time
            generated_text = response['choices'][0]['text'].strip()
            
            # Log performance metrics
            tokens_per_second = response['usage']['completion_tokens'] / generation_time if generation_time > 0 else 0
            logger.info(f"Generated {response['usage']['completion_tokens']} tokens in {generation_time:.2f}s ({tokens_per_second:.1f} tokens/s)")
            
            return {
                "insights": generated_text,
                "processing_time": generation_time,
                "tokens_generated": response['usage']['completion_tokens'],
                "tokens_per_second": round(tokens_per_second, 1),
                "model": "phi-4-reasoning-plus-Q6_K_L",
                "context_window": 32768,
                "max_tokens_setting": max_tokens
            }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e), "error_type": type(e).__name__}

# RunPod serverless entrypoint
runpod.serverless.start({"handler": handler})