"""
Minimal RunPod handler for debugging - Whisper only, CPU mode
"""

import os
import runpod
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(job):
    """Minimal handler for debugging"""
    try:
        logger.info("Handler started")
        logger.info(f"Job input: {job}")
        
        # Just echo back the input to test basic functionality
        job_input = job.get("input", {})
        
        # Check environment
        logger.info(f"Python version: {os.sys.version}")
        logger.info(f"Available memory: {os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024**3):.2f} GB")
        logger.info(f"CPU count: {os.cpu_count()}")
        
        # Try importing required libraries
        try:
            import torch
            logger.info(f"PyTorch version: {torch.__version__}")
            logger.info(f"CUDA available: {torch.cuda.is_available()}")
        except Exception as e:
            logger.error(f"PyTorch import error: {e}")
        
        try:
            from faster_whisper import WhisperModel
            logger.info("faster_whisper imported successfully")
        except Exception as e:
            logger.error(f"faster_whisper import error: {e}")
            
        try:
            from llama_cpp import Llama
            logger.info("llama_cpp imported successfully")
        except Exception as e:
            logger.error(f"llama_cpp import error: {e}")
        
        return {
            "status": "test_complete",
            "input_received": job_input,
            "environment": {
                "python_version": os.sys.version,
                "cpu_count": os.cpu_count(),
                "cwd": os.getcwd(),
                "models_dir_exists": os.path.exists("/models"),
                "workspace_exists": os.path.exists("/workspace")
            }
        }
        
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# RunPod serverless entrypoint
runpod.serverless.start({"handler": handler})