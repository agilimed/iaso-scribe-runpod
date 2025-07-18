"""
IASOQL RunPod Handler - Healthcare SQL Generation
Optimized for ClickHouse queries on FHIR data
"""

import runpod
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import re
from typing import Dict, Any, List, Optional
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configuration - Using HuggingFace like Phi-4/Whisper
MODEL_NAME = "vivkris/iasoql-7B"  # Private HuggingFace repo
CACHE_DIR = "/runpod-volume/huggingface-cache" if os.path.exists("/runpod-volume") else "/tmp/huggingface-cache"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Global model instance
model = None
tokenizer = None

def load_model():
    """Load IASOQL model from HuggingFace"""
    global model, tokenizer
    
    logger.info(f"Loading model: {MODEL_NAME}")
    logger.info(f"Device: {DEVICE}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    
    try:
        # Get HuggingFace token from environment
        hf_token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN")
        
        # Load tokenizer
        logger.info(f"Loading tokenizer from {MODEL_NAME}")
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            cache_dir=CACHE_DIR,
            use_auth_token=hf_token
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
            use_auth_token=hf_token
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
    
    try:
        # Load model if not already loaded
        if model is None:
            load_model()
        
        # Extract inputs
        inputs = event.get("input", {})
        query = inputs.get("query")
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