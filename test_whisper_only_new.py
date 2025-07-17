#!/usr/bin/env python3
"""
Test just Whisper transcription without Phi-4
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "rntxttrdl8uv3i")
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "your-api-key-here")

def test_whisper_only_sync():
    """Test just Whisper without Phi-4 insights using synchronous endpoint"""
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Use a shorter audio sample
    payload = {
        "input": {
            "audio": "https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav",
            "generate_insights": False  # Disable Phi-4 to test Whisper alone
        }
    }
    
    print("🎤 Testing Whisper-only transcription...")
    print(f"Endpoint: https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync")
    print("Sending request...")
    
    start = time.time()
    response = requests.post(
        f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync",
        headers=headers,
        json=payload,
        timeout=300  # 5 minute timeout
    )
    elapsed = time.time() - start
    
    print(f"\nResponse time: {elapsed:.1f}s")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get("status") == "COMPLETED":
            output = result.get("output", {})
            print("\n✅ Success!")
            print(f"Transcription: {output.get('transcription', 'N/A')}")
            print(f"Language: {output.get('language', 'N/A')}")
            print(f"Duration: {output.get('duration', 'N/A')}s")
            print(f"Processing time: {output.get('processing_time', {})}")
        else:
            print(f"\nStatus: {result.get('status')}")
            if result.get("error"):
                print(f"Error: {result.get('error')}")
    else:
        print(f"\n❌ HTTP Error: {response.text}")

if __name__ == "__main__":
    print("🚀 RunPod Whisper-Only Test")
    print("=" * 50)
    test_whisper_only_sync()