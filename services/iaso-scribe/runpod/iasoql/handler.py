"""
IASOQL RunPod Handler - Healthcare SQL Generation
Optimized for ClickHouse queries on FHIR data
"""

import runpod
import torch
import json
import re
import os
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import transformers components
try:
    from transformers import (
        AutoModelForCausalLM, 
        AutoTokenizer,
        BitsAndBytesConfig,
        GenerationConfig
    )
except ImportError as e:
    logger.error(f"Failed to import transformers: {e}")
    sys.exit(1)

# Model configuration
MODEL_NAME = os.environ.get("MODEL_NAME", "vivkris/iasoql-7B")
# Use unique subdirectory for IASOQL to avoid conflicts with other endpoints
CACHE_DIR = "/runpod-volume/iasoql/cache" if os.path.exists("/runpod-volume") else "/tmp/iasoql-cache"

# Global model instance
model = None
tokenizer = None
generation_config = None

def setup_cuda():
    """Setup CUDA environment and check availability"""
    if torch.cuda.is_available():
        device = torch.cuda.current_device()
        logger.info(f"CUDA available: {torch.cuda.get_device_name(device)}")
        logger.info(f"CUDA memory: {torch.cuda.get_device_properties(device).total_memory / 1e9:.2f} GB")
        # Clear any existing cache
        torch.cuda.empty_cache()
        return "cuda"
    else:
        logger.warning("CUDA not available, using CPU")
        return "cpu"

def load_model():
    """Load IASOQL model with proper error handling"""
    global model, tokenizer, generation_config
    
    logger.info("="*60)
    logger.info("IASOQL Handler Starting - Healthcare SQL Generation")
    logger.info("="*60)
    logger.info(f"Loading model: {MODEL_NAME}")
    logger.info(f"Cache directory: {CACHE_DIR}")
    
    # Setup device
    device = setup_cuda()
    
    # Ensure cache directory exists
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    try:
        # Get HuggingFace token from environment
        hf_token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN")
        
        if hf_token:
            logger.info("HuggingFace token found in environment")
            # Set as environment variable for all HF operations
            os.environ["HF_TOKEN"] = hf_token
        else:
            logger.warning("No HuggingFace token found - this may fail for private models")
        
        # Determine if we should use quantization
        use_quantization = os.environ.get("USE_QUANTIZATION", "false").lower() == "true"
        
        # Setup quantization config if requested
        quantization_config = None
        if use_quantization and device == "cuda":
            logger.info("Setting up 4-bit quantization")
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
        
        # Load tokenizer
        logger.info(f"Loading tokenizer from {MODEL_NAME}")
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            cache_dir=CACHE_DIR,
            token=hf_token,
            trust_remote_code=True,
            use_fast=True
        )
        
        # Set padding token if not present
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            logger.info("Set pad_token to eos_token")
        
        # Load model
        logger.info(f"Loading model from {MODEL_NAME}")
        model_kwargs = {
            "cache_dir": CACHE_DIR,
            "token": hf_token,
            "trust_remote_code": True,
            "torch_dtype": torch.float16 if device == "cuda" else torch.float32,
            "low_cpu_mem_usage": True,
        }
        
        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
            model_kwargs["device_map"] = "auto"
        elif device == "cuda":
            model_kwargs["device_map"] = "auto"
        
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            **model_kwargs
        )
        
        # Set model to evaluation mode
        model.eval()
        
        # Setup generation config
        generation_config = GenerationConfig(
            do_sample=True,
            temperature=0.1,  # Low temperature for SQL generation
            top_p=0.95,
            max_new_tokens=512,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
        
        logger.info("Model loaded successfully")
        logger.info(f"Model device: {next(model.parameters()).device}")
        
        # Log memory usage
        if device == "cuda":
            allocated = torch.cuda.memory_allocated() / 1e9
            reserved = torch.cuda.memory_reserved() / 1e9
            logger.info(f"GPU memory - Allocated: {allocated:.2f} GB, Reserved: {reserved:.2f} GB")
        
    except Exception as e:
        logger.error(f"Error loading model: {e}", exc_info=True)
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
- JSONExtractString(resource, 'path.to.field') - Extract string values
- JSONExtractFloat(resource, 'path.to.field') - Extract numeric values  
- JSONExtractBool(resource, 'path.to.field') - Extract boolean values
- JSONHas(resource, 'path.to.field') - Check if field exists
- JSONExtractArrayRaw(resource, 'path.to.array') - Extract JSON arrays
- arrayElement(JSONExtractArrayRaw(...), 1) - Get array elements
- has(JSONExtractArrayRaw(...), 'value') - Check array contains value

Common FHIR Paths:
- Patient: gender, birthDate, name[0].given[0], name[0].family
- Observation: code.coding[0].code, valueQuantity.value, effectiveDateTime
- Condition: code.coding[0].display, clinicalStatus.coding[0].code
- Appointment: start, status, participant[0].actor.reference

"""

    if rag_context:
        prompt += f"""
Clinical Context from Knowledge Base:
{rag_context}

"""

    if examples:
        prompt += "Examples:\n"
        for example in examples[:3]:  # Limit to 3 examples
            prompt += f"Q: {example['query']}\nSQL: {example['sql']}\n\n"

    prompt += f"""Q: {query}
SQL:"""

    return prompt

def validate_sql(sql: str) -> Dict[str, Any]:
    """Validate generated SQL for safety and correctness"""
    
    # Remove any potential harmful operations
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE', 'GRANT', 'REVOKE']
    sql_upper = sql.upper()
    
    for keyword in dangerous_keywords:
        if re.search(r'\b' + keyword + r'\b', sql_upper):
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
    
    # Basic SQL injection prevention
    if re.search(r'(;|\bEXEC\b|\bEXECUTE\b)', sql_upper):
        return {
            "valid": False,
            "error": "Potential SQL injection detected"
        }
    
    return {"valid": True, "sql": sql.strip()}

def extract_sql_from_response(response: str) -> str:
    """Extract SQL from model response"""
    
    # Try to find SQL between markers
    sql_match = re.search(r'```sql\n(.*?)\n```', response, re.DOTALL | re.IGNORECASE)
    if sql_match:
        return sql_match.group(1).strip()
    
    # Try to find SQL after "SQL:" marker
    sql_match = re.search(r'SQL:\s*(.*?)(?:\n\n|$)', response, re.DOTALL)
    if sql_match:
        return sql_match.group(1).strip()
    
    # If no markers, look for SELECT statement
    sql_match = re.search(r'(SELECT\s+.*?)(?:\n\n|$)', response, re.DOTALL | re.IGNORECASE)
    if sql_match:
        return sql_match.group(1).strip()
    
    # Return the whole response if no SQL found
    return response.strip()

def handler(job):
    """RunPod handler function"""
    
    start_time = datetime.now()
    logger.info("IASOQL handler called - Processing healthcare SQL query")
    
    try:
        # Validate job structure
        if not isinstance(job, dict) or 'input' not in job:
            return {"error": "Invalid job structure - missing 'input'"}
        
        # Load model if not already loaded
        if model is None:
            load_model()
        
        # Extract inputs
        job_input = job['input']
        
        # Support multiple input formats for compatibility
        query = job_input.get("query") or job_input.get("text") or job_input.get("prompt")
        if not query:
            return {"error": "No query provided. Use 'query', 'text', or 'prompt' field"}
        
        schema_context = job_input.get("schema_context", "")
        rag_context = job_input.get("rag_context", "")
        examples = job_input.get("examples", [])
        
        # Generation parameters
        temperature = job_input.get("temperature", 0.1)
        max_tokens = job_input.get("max_tokens", 512)
        top_p = job_input.get("top_p", 0.95)
        
        # Default schema if not provided
        if not schema_context:
            schema_context = """
Table: nexuscare_analytics.fhir_current
Columns:
- tenant_id: String (organization identifier)
- resource_type: String (Patient, Observation, Condition, MedicationRequest, Appointment, etc.)
- resource_id: String (unique resource identifier)
- resource: JSON (contains full FHIR resource)
- sign: Int8 (1 for current, -1 for deleted)
- version_id: String
- created_at: DateTime
- last_updated: DateTime

Indexes: tenant_id, resource_type, resource_id, created_at
"""
        
        # Generate prompt
        prompt = generate_sql_prompt(query, schema_context, rag_context, examples)
        
        logger.info(f"Processing query: {query[:100]}...")
        
        # Tokenize
        inputs_encoded = tokenizer(
            prompt,
            return_tensors="pt",
            max_length=2048,
            truncation=True,
            padding=True
        )
        
        # Move to device
        if next(model.parameters()).is_cuda:
            inputs_encoded = {k: v.cuda() for k, v in inputs_encoded.items()}
        
        # Generate SQL
        logger.info("Generating SQL...")
        with torch.no_grad():
            outputs = model.generate(
                **inputs_encoded,
                generation_config=generation_config,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
        
        # Decode response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract SQL from response
        generated_text = response[len(prompt):].strip()
        sql = extract_sql_from_response(generated_text)
        
        logger.info(f"Generated SQL: {sql[:200]}...")
        
        # Validate SQL
        validation = validate_sql(sql)
        
        if not validation["valid"]:
            return {
                "error": validation["error"],
                "generated_sql": sql,
                "status": "invalid",
                "query": query,
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
        
        # Clear GPU cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Return results
        return {
            "sql": validation["sql"],
            "query": query,
            "status": "success",
            "metadata": {
                "model": MODEL_NAME,
                "rag_context_provided": bool(rag_context),
                "examples_provided": len(examples) > 0,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "prompt_tokens": len(inputs_encoded["input_ids"][0]),
                "generated_tokens": len(outputs[0]) - len(inputs_encoded["input_ids"][0])
            }
        }
        
    except torch.cuda.OutOfMemoryError as e:
        logger.error("GPU out of memory", exc_info=True)
        torch.cuda.empty_cache()
        return {
            "error": "GPU out of memory. Try reducing max_tokens or query length.",
            "status": "error",
            "execution_time": (datetime.now() - start_time).total_seconds()
        }
        
    except Exception as e:
        logger.error(f"Error in IASOQL handler: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "status": "error",
            "execution_time": (datetime.now() - start_time).total_seconds()
        }

# Start RunPod serverless handler
if __name__ == "__main__":
    logger.info("Starting IASOQL RunPod handler...")
    runpod.serverless.start({"handler": handler})