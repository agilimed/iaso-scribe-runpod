#!/usr/bin/env python3
"""
Simple test for RunPod endpoint
"""

import requests
import json
import os
import time

ENDPOINT_ID = "rntxttrdl8uv3i"
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "your-api-key-here")

def test_whisper_only():
    """Test just Whisper without Phi-4 to isolate the issue."""
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Simple test - no medical insights
    payload = {
        "input": {
            "audio": "https://www2.cs.uic.edu/~i101/SoundFiles/CantinaBand60.wav",
            "generate_insights": False  # Don't use Phi-4
        }
    }
    
    print("🎤 Testing Whisper transcription (no Phi-4)...")
    print(f"Audio: {payload['input']['audio']}")
    print("Sending request...")
    
    start = time.time()
    response = requests.post(
        f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync",
        headers=headers,
        json=payload
    )
    elapsed = time.time() - start
    
    print(f"\nResponse time: {elapsed:.1f}s")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
        
        if result.get("status") == "COMPLETED":
            output = result.get("output", {})
            print("\n✅ Success!")
            print(f"Transcription: {output.get('transcription', 'N/A')}")
        elif result.get("status") == "FAILED":
            print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")
    else:
        print(f"\n❌ HTTP Error: {response.text}")

if __name__ == "__main__":
    print("🚀 Simple RunPod Test")
    print("=" * 50)
    test_whisper_only()