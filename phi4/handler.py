"""
RunPod Phi-4 Reasoning Plus Handler
Medical insights generation using quantized Phi-4
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
# Use unique subdirectory for Phi-4 to avoid conflicts
MODEL_DIR = "/runpod-volume/phi4/models" if os.path.exists("/runpod-volume") else "/models/phi4"
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
                n_batch=512,
                rope_scaling_type=1  # Enable RoPE scaling for full context
            )
            logger.info(f"Phi-4 model loaded in {time.time() - start_time:.2f}s")
            logger.info(f"GPU layers: {n_gpu_layers}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

def handler(job):
    """
    RunPod handler for Phi-4 medical reasoning.
    
    Input format:
    {
        "input": {
            "text": "Medical transcription or text to analyze",
            "prompt_type": "medical_insights" (optional),
            "max_tokens": 1024 (optional),
            "temperature": 0.7 (optional)
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
        max_tokens = job_input.get("max_tokens", 8192)  # Increased for complete medical summaries
        temperature = job_input.get("temperature", 0.7)
        
        if not text:
            raise ValueError("No text input provided")
        
        # Build prompt based on type
        if prompt_type == "medical_insights":
            prompt = f"""<|system|>
You are an expert medical documentation assistant. You MUST structure your response with <think> tags for reasoning and <solution> tags for the final answer.
<|end|>
<|user|>
Analyze this medical transcription:

{text}

YOU MUST structure your response EXACTLY like this:

<think>
[Your step-by-step reasoning here]
</think>

<solution>
1. Chief complaint and key symptoms
2. Medical findings and observations  
3. Relevant medications with dosages
4. Clinical assessment and diagnosis considerations
5. Recommended follow-up actions
6. Any urgent concerns or red flags
</solution>
<|end|>
<|assistant|><think>"""
        elif prompt_type == "soap":
            prompt = f"""<|system|>
You are an expert medical scribe. Convert the transcription into a properly formatted SOAP note using active voice and complete clinical details.
IMPORTANT: Show your analysis in <think>...</think> tags, then provide the final SOAP note in <solution>...</solution> tags.
<|end|>
<|user|>
Convert this medical transcription into a SOAP note:

{text}

First, analyze the information in <think> tags, then format your SOAP note in <solution> tags EXACTLY as follows:

SUBJECTIVE:
• Chief complaint and HPI
• Patient-reported symptoms and history
• Relevant medical history, medications, allergies
• Social history if relevant

OBJECTIVE:
• Vital signs
• Physical examination findings
• ALL clinical measurements (include stations, effacement, dilation)
• Laboratory results and imaging findings
• Procedure details and measurements

ASSESSMENT:
• Primary diagnosis with supporting evidence
• Secondary diagnoses
• Clinical reasoning
• Risk factors addressed

PLAN:
• Immediate interventions performed
• Medications (with exact doses and routes)
• Monitoring parameters
• Follow-up appointments
• Patient education provided
• Disposition

Important: Use active voice, include ALL clinical details, and maintain exact terminology from the source.
<|end|>
<|assistant|><think>"""
        elif prompt_type == "summary":
            prompt = f"""<|system|>
You are a medical documentation specialist. Create a concise clinical summary using active voice and complete medical details.
IMPORTANT: Show your analysis in <think>...</think> tags, then provide your final summary in <solution>...</solution> tags.
<|end|>
<|user|>
Summarize this medical encounter:

{text}

First, analyze the key information in <think> tags, then provide your clinical summary in <solution> tags including:
- Chief complaint
- Key findings (include ALL clinical measurements, stations, test results)
- Diagnosis/Assessment
- Treatment plan
- Follow-up requirements

Important guidelines:
1. Use active voice (e.g., "Patient had a spontaneous vaginal delivery" not "Delivery was achieved")
2. Include ALL clinical details mentioned (stations, cord gases, specific team names)
3. Use EXACT terminology from the source (e.g., "neonatal care team" not "NICU" unless specifically stated)
4. Include all test results and measurements
5. Be precise about medication courses (e.g., betamethasone standard two-dose course)
6. Include complete postpartum monitoring (fundal height, lochia, epidural discontinuation)
7. Maintain clinical accuracy while being concise
8. Do NOT assume or upgrade terminology (e.g., don't say "NICU" if source says "neonatal observation")

Keep it complete but concise.
<|end|>
<|assistant|><think>"""
        else:
            # Use text as direct prompt
            prompt = text
        
        # Generate response
        logger.info("Generating medical insights...")
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
        
        # Ensure proper tag closure for structured prompts
        if prompt_type in ["medical_insights", "soap", "summary"]:
            # Add the initial <think> tag if missing (since we start with it in prompt)
            if not generated_text.startswith("<think>") and "<think>" not in generated_text:
                generated_text = "<think>\n" + generated_text
            # Check if we need to close tags
            if "<think>" in generated_text and "</think>" not in generated_text:
                generated_text += "\n</think>"
            if "</think>" in generated_text and "<solution>" not in generated_text:
                generated_text += "\n<solution>\n[Response was incomplete]\n</solution>"
        
        # Log performance metrics
        tokens_per_second = response['usage']['completion_tokens'] / generation_time if generation_time > 0 else 0
        logger.info(f"Generated {response['usage']['completion_tokens']} tokens in {generation_time:.2f}s ({tokens_per_second:.1f} tokens/s)")
        
        return {
            "insights": generated_text,
            "processing_time": generation_time,
            "tokens_generated": response['usage']['completion_tokens'],
            "tokens_per_second": round(tokens_per_second, 1),
            "model": "phi-4-reasoning-plus-Q6_K_L"
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e), "error_type": type(e).__name__}

# RunPod serverless entrypoint
runpod.serverless.start({"handler": handler})