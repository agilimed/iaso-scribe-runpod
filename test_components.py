#!/usr/bin/env python3
"""
Test individual components to isolate the issue
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_whisper_only():
    """Test just Whisper without Phi-4"""
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "audio": "https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav",
            "generate_insights": False  # Disable Phi-4
        }
    }
    
    print("🎤 Testing Whisper only (no Phi-4)...")
    response = requests.post(
        f"https://api.runpod.ai/v2/{os.environ.get('RUNPOD_ENDPOINT_ID')}/runsync",
        headers=headers,
        json=payload,
        timeout=60
    )
    
    result = response.json()
    if result.get("status") == "COMPLETED":
        print("✅ Whisper works!")
        print(f"Transcription: {result['output']['transcription']}")
        print(f"Time: {result['output']['processing_time']['transcription']:.2f}s")
    else:
        print(f"❌ Whisper failed: {result.get('error', 'Unknown')}")
        print(f"Status: {result.get('status')}")

if __name__ == "__main__":
    test_whisper_only()