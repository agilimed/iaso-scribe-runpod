"""
IASOQL RunPod Handler - Healthcare SQL Generation
Optimized for ClickHouse queries on FHIR data
"""

# CRITICAL: This is the IASOQL handler, NOT Phi-4!
print("="*80)
print("IASOQL HANDLER LOADED - If you see Phi-4 messages, wrong handler is running!")
print("="*80)

import runpod
import torch
import json
import re
from typing import Dict, Any, List, Optional
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from transformers import AutoModelForCausalLM, AutoTokenizer
# Try to import Qwen2 tokenizer if available
try:
    from transformers import Qwen2Tokenizer
except ImportError:
    logger.warning("Qwen2Tokenizer not available, will use AutoTokenizer")

# Model configuration - Using HuggingFace like Phi-4/Whisper
MODEL_NAME = "vivkris/iasoql-7B"  # Private HuggingFace repo
# Use unique subdirectory for IASOQL to avoid conflicts
CACHE_DIR = "/runpod-volume/iasoql/cache" if os.path.exists("/runpod-volume") else "/tmp/iasoql-cache"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Global model instance
model = None
tokenizer = None

def load_model():
    """Load IASOQL model from HuggingFace"""
    global model, tokenizer
    
    logger.info("="*60)
    logger.info("IASOQL Handler Starting - Healthcare SQL Generation")
    logger.info("="*60)
    logger.info(f"Loading model: {MODEL_NAME}")
    logger.info(f"Cache directory: {CACHE_DIR}")
    logger.info(f"Device: {DEVICE}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    
    try:
        # Get HuggingFace token from environment
        hf_token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN")
        
        if hf_token:
            logger.info("HuggingFace token found in environment")
        else:
            logger.warning("No HuggingFace token found - this may fail for private models")
        
        # Load tokenizer
        logger.info(f"Loading tokenizer from {MODEL_NAME}")
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            cache_dir=CACHE_DIR,
            token=hf_token,  # Use 'token' instead of deprecated 'use_auth_token'
            trust_remote_code=True
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model with optimizations
        logger.info(f"Loading model from {MODEL_NAME}")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            cache_dir=CACHE_DIR,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            token=hf_token  # Use 'token' instead of deprecated 'use_auth_token'
        )
        
        model.eval()
        logger.info("Model loaded successfully")
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise

def generate_sql_prompt(
    query: str,
    schema_context: str,
    rag_context: Optional[str] = None,
    examples: Optional[List[Dict[str, str]]] = None
) -> str:
    """Generate prompt for SQL generation with clinical context"""
    
    prompt = f"""You are IASOQL, an expert at generating ClickHouse SQL queries for healthcare analytics on FHIR data.

IMPORTANT: The FHIR resources are stored as JSON in the 'resource' column. Use ClickHouse JSON functions to extract data.

Database Schema:
{schema_context}

Key ClickHouse JSON Functions:
- JSONExtractString(resource, '$.path.to.field') - Extract string values
- JSONExtractFloat(resource, '$.path.to.field') - Extract numeric values
- JSONExtractBool(resource, '$.path.to.field') - Extract boolean values
- JSONHas(resource, '$.path.to.field') - Check if field exists
- JSONExtractArrayRaw(resource, '$.path.to.array') - Extract JSON arrays

"""

    if rag_context:
        prompt += f"""
Clinical Context from Knowledge Base:
{rag_context}

"""

    if examples:
        prompt += "Examples:\n"
        for example in examples:
            prompt += f"Q: {example['query']}\nSQL: {example['sql']}\n\n"

    prompt += f"""Q: {query}
SQL:"""

    return prompt

def validate_sql(sql: str) -> Dict[str, Any]:
    """Validate generated SQL for safety and correctness"""
    
    # Remove any potential harmful operations
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
    sql_upper = sql.upper()
    
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return {
                "valid": False,
                "error": f"Dangerous operation detected: {keyword}"
            }
    
    # Ensure it's a SELECT query
    if not sql_upper.strip().startswith('SELECT'):
        return {
            "valid": False,
            "error": "Only SELECT queries are allowed"
        }
    
    # Check for required elements
    if 'FROM' not in sql_upper:
        return {
            "valid": False,
            "error": "Missing FROM clause"
        }
    
    return {"valid": True, "sql": sql.strip()}

def extract_sql_from_response(response: str) -> str:
    """Extract SQL from model response"""
    
    # Try to find SQL between markers
    sql_match = re.search(r'```sql\n(.*?)\n```', response, re.DOTALL)
    if sql_match:
        return sql_match.group(1).strip()
    
    # Try to find SQL after "SQL:" marker
    sql_match = re.search(r'SQL:\s*(.*)', response, re.DOTALL)
    if sql_match:
        return sql_match.group(1).strip()
    
    # Return the whole response if no markers found
    return response.strip()

def handler(event):
    """RunPod handler function"""
    
    logger.info("IASOQL handler called - Processing healthcare SQL query")
    
    try:
        # Load model if not already loaded
        if model is None:
            load_model()
        
        # Extract inputs
        inputs = event.get("input", {})
        # Support both "query" and "text" for compatibility
        query = inputs.get("query") or inputs.get("text")
        schema_context = inputs.get("schema_context", "")
        rag_context = inputs.get("rag_context", "")
        examples = inputs.get("examples", [])
        
        # Validate inputs
        if not query:
            return {"error": "No query provided"}
        
        # Default schema if not provided
        if not schema_context:
            schema_context = """
Table: nexuscare_analytics.fhir_current
Columns:
- tenant_id: String
- resource_type: String (Patient, Observation, Condition, MedicationRequest, etc.)
- resource_id: String
- resource: JSON (contains full FHIR resource)
- sign: Int8 (1 for current, -1 for deleted)
- version_id: String
- created_at: DateTime
"""
        
        # Generate prompt
        prompt = generate_sql_prompt(query, schema_context, rag_context, examples)
        
        logger.info(f"Processing query: {query}")
        
        # Tokenize
        inputs_encoded = tokenizer(
            prompt,
            return_tensors="pt",
            max_length=2048,
            truncation=True,
            padding=True
        ).to(DEVICE)
        
        # Generate SQL
        with torch.no_grad():
            outputs = model.generate(
                **inputs_encoded,
                max_new_tokens=512,
                temperature=0.1,  # Low temperature for consistency
                do_sample=True,
                top_p=0.95,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        # Decode response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract SQL from response
        sql = extract_sql_from_response(response[len(prompt):])
        
        # Validate SQL
        validation = validate_sql(sql)
        
        if not validation["valid"]:
            return {
                "error": validation["error"],
                "generated_sql": sql,
                "status": "invalid"
            }
        
        # Return results
        return {
            "sql": validation["sql"],
            "query": query,
            "status": "success",
            "metadata": {
                "model": MODEL_NAME,
                "rag_context_provided": bool(rag_context),
                "examples_provided": len(examples) > 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error in IASOQL handler: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "status": "error"
        }

# RunPod endpoint
runpod.serverless.start({"handler": handler})