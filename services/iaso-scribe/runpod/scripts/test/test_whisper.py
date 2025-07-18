#!/usr/bin/env python3
"""Test the Whisper-only endpoint"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def test_whisper():
    """Test Whisper transcription with JFK audio"""
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "audio": "https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav",
            "return_segments": True
        }
    }
    
    print("🎤 Testing Whisper Medium endpoint...")
    print("=" * 50)
    print("Audio: JFK speech (11 seconds)")
    print("Expected: Fast transcription with GPU acceleration")
    print("=" * 50)
    
    start_time = time.time()
    response = requests.post(
        f"https://api.runpod.ai/v2/{os.environ.get('RUNPOD_ENDPOINT_ID')}/runsync",
        headers=headers,
        json=payload,
        timeout=120
    )
    elapsed = time.time() - start_time
    
    print(f"\nAPI Response time: {elapsed:.1f}s")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get("status") == "COMPLETED":
            output = result.get("output", {})
            print("\n✅ Success!")
            
            # Transcription
            print(f"\n📝 Transcription:")
            print(f'"{output.get("transcription", "N/A")}"')
            
            # Language detection
            print(f"\n🌐 Language: {output.get('language', 'N/A')}")
            print(f"📏 Duration: {output.get('duration', 0):.1f}s")
            
            # Processing time
            print(f"\n⏱️  Processing time: {output.get('processing_time', 0):.2f}s")
            
            # Check if GPU was used (fast processing indicates GPU)
            if output.get('processing_time', 999) < 5:
                print("🚀 GPU acceleration: Working! (< 5s for 11s audio)")
            else:
                print("⚠️  GPU acceleration: May not be working")
            
            # Segments if available
            if output.get("segments"):
                print(f"\n📊 Segments: {len(output['segments'])} segments detected")
                for i, seg in enumerate(output['segments'][:3]):  # Show first 3
                    print(f"   [{seg['start']:.1f}s - {seg['end']:.1f}s]: {seg['text']}")
                if len(output['segments']) > 3:
                    print(f"   ... and {len(output['segments']) - 3} more segments")
                    
        elif result.get("status") == "FAILED":
            print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")
            if result.get("output"):
                print(f"Details: {json.dumps(result['output'], indent=2)}")
        else:
            print(f"\n⏳ Status: {result.get('status')}")
            print(json.dumps(result, indent=2))
    else:
        print(f"\n❌ HTTP Error {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_whisper()