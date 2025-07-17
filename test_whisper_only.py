#!/usr/bin/env python3
"""
Test Whisper-only transcription (without Phi-4 insights)
"""

import requests
import json
import os

ENDPOINT_ID = "rntxttrdl8uv3i"
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY")

def test_whisper_only():
    """Test transcription without medical insights generation."""
    print("🎤 Testing Whisper transcription only (no Phi-4)...")
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Disable insights generation to avoid downloading Phi-4
    test_payload = {
        "input": {
            "audio": "https://www2.cs.uic.edu/~i101/SoundFiles/StarWars60.wav",
            "language": "en",
            "generate_insights": False,  # This avoids Phi-4 download
            "return_segments": True
        }
    }
    
    print("Sending request (insights disabled)...")
    
    try:
        response = requests.post(
            f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync",
            headers=headers,
            json=test_payload,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2))
            
            if result.get("status") == "COMPLETED" and "output" in result:
                output = result["output"]
                print("\n✅ Transcription successful!")
                print(f"Text: {output.get('transcription', 'N/A')}")
                print(f"Language: {output.get('language', 'N/A')}")
                print(f"Duration: {output.get('duration', 'N/A')}s")
                
                if "segments" in output:
                    print("\nSegments:")
                    for i, seg in enumerate(output["segments"][:3]):  # First 3 segments
                        print(f"  [{seg['start']:.2f}s - {seg['end']:.2f}s]: {seg['text']}")
                    if len(output["segments"]) > 3:
                        print(f"  ... and {len(output['segments']) - 3} more segments")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 IASO Scribe - Whisper-only Test")
    print("=" * 50)
    
    if not RUNPOD_API_KEY:
        print("❌ Please set RUNPOD_API_KEY environment variable")
    else:
        test_whisper_only()