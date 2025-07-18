"""
AWS Lambda handler for IasoScribe
"""

import json
import os
import sys
import base64
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from medical_whisper_handler import MedicalWhisperHandler

# Initialize handler (reused across invocations)
whisper_handler = None

def get_handler():
    """Get or create whisper handler"""
    global whisper_handler
    if whisper_handler is None:
        model_size = os.getenv("WHISPER_MODEL_SIZE", "medium")
        whisper_handler = MedicalWhisperHandler(
            model_size=model_size,
            device="cpu"  # Lambda doesn't have GPU
        )
    return whisper_handler

async def handler(event, context):
    """
    AWS Lambda handler function
    
    Expected event format:
    {
        "audio": "base64_encoded_audio" or "s3://bucket/key",
        "specialty": "cardiology",
        "language": "en",
        "generate_note": true,
        "note_template": "soap"
    }
    """
    try:
        # Get handler instance
        whisper = get_handler()
        
        # Extract parameters
        audio_input = event.get("audio")
        if not audio_input:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No audio provided"})
            }
        
        # Handle different audio input types
        if audio_input.startswith("s3://"):
            # Download from S3
            audio_path = download_from_s3(audio_input)
        elif audio_input.startswith("http"):
            # Download from URL
            audio_path = whisper.audio_preprocessor.download_audio(audio_input)
        else:
            # Assume base64 encoded
            audio_path = decode_base64_audio(audio_input)
        
        # Transcribe
        result = await whisper.transcribe_audio(
            audio_path=audio_path,
            specialty=event.get("specialty", "general"),
            language=event.get("language", "en"),
            enable_vad=event.get("enable_vad", True)
        )
        
        # Generate note if requested
        if event.get("generate_note", False):
            note = await whisper.generate_medical_note(
                transcript=result["transcript"],
                template=event.get("note_template", "soap"),
                specialty=event.get("specialty", "general"),
                entities=result.get("medical_entities")
            )
            result["structured_note"] = note
        
        # Clean up temporary file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        return {
            "statusCode": 200,
            "body": json.dumps(result),
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "type": type(e).__name__
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        }

def download_from_s3(s3_uri):
    """Download audio from S3"""
    import boto3
    
    # Parse S3 URI
    parts = s3_uri.replace("s3://", "").split("/", 1)
    bucket = parts[0]
    key = parts[1]
    
    # Download file
    s3 = boto3.client("s3")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        s3.download_fileobj(bucket, key, tmp)
        return tmp.name

def decode_base64_audio(base64_data):
    """Decode base64 audio to file"""
    # Remove data URL prefix if present
    if "," in base64_data:
        base64_data = base64_data.split(",")[1]
    
    # Decode
    audio_bytes = base64.b64decode(base64_data)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        return tmp.name