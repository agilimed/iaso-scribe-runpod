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

# Model configuration
MODEL_NAME = os.environ.get("MODEL_NAME", "iasoql-7b")  # Your proprietary model
MODEL_PATH = os.environ.get("MODEL_PATH", "/runpod-volume/models")  # RunPod network volume
S3_MODEL_PATH = os.environ.get("S3_MODEL_PATH", "")  # S3 path to your model
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Global model instance
model = None
tokenizer = None

def download_model_from_s3():
    """Download model from S3 if not exists locally"""
    import boto3
    
    local_model_path = os.path.join(MODEL_PATH, MODEL_NAME)
    
    # Check if model already exists
    if os.path.exists(local_model_path) and os.path.exists(os.path.join(local_model_path, "config.json")):
        logger.info(f"Model already exists at {local_model_path}")
        return local_model_path
    
    if not S3_MODEL_PATH:
        logger.error("S3_MODEL_PATH not set and model not found locally")
        raise ValueError("Model not found. Please set S3_MODEL_PATH environment variable")
    
    logger.info(f"Downloading model from S3: {S3_MODEL_PATH}")
    
    try:
        # Create S3 client with credentials (required since bucket is not public)
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            s3 = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
        else:
            # Use IAM role if no credentials provided
            s3 = boto3.client('s3', region_name=AWS_REGION)
        
        # Parse S3 path
        if S3_MODEL_PATH.startswith("s3://"):
            s3_path = S3_MODEL_PATH[5:]
        else:
            s3_path = S3_MODEL_PATH
        
        # For directory-style model path
        if s3_path.endswith("/"):
            s3_path = s3_path[:-1]
        
        bucket_name, prefix = s3_path.split("/", 1)
        
        # Create model directory
        os.makedirs(local_model_path, exist_ok=True)
        
        # List all files in the model directory
        logger.info(f"Listing files in bucket: {bucket_name}, prefix: {prefix}/")
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=f"{prefix}/")
        
        # Download each file
        files_downloaded = 0
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    # Skip directories
                    if key.endswith('/'):
                        continue
                    
                    # Get relative path
                    relative_path = key[len(prefix)+1:]  # Remove prefix and slash
                    local_file_path = os.path.join(local_model_path, relative_path)
                    
                    # Create subdirectories if needed
                    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                    
                    # Download file
                    logger.info(f"Downloading {relative_path}...")
                    s3.download_file(bucket_name, key, local_file_path)
                    files_downloaded += 1
        
        logger.info(f"Downloaded {files_downloaded} files successfully")
        return local_model_path
        
    except Exception as e:
        logger.error(f"Error downloading model from S3: {e}")
        raise

def load_model():
    """Load IASOQL model with optimizations"""
    global model, tokenizer
    
    logger.info(f"Loading model: {MODEL_NAME}")
    logger.info(f"Device: {DEVICE}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    
    try:
        # Download model from S3 if needed
        local_model_path = download_model_from_s3()
        
        # Load tokenizer
        logger.info(f"Loading tokenizer from {local_model_path}")
        tokenizer = AutoTokenizer.from_pretrained(local_model_path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model with optimizations
        logger.info(f"Loading model from {local_model_path}")
        model = AutoModelForCausalLM.from_pretrained(
            local_model_path,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True
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