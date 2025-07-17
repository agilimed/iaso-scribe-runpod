#!/usr/bin/env python3
"""
Test Phi-4 by providing a silent audio file (bypass Whisper issues)
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def test_phi_with_silent_audio():
    """Test with a very short silent audio to minimize Whisper processing"""
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    # Use a very short audio sample that will transcribe to minimal text
    # This is a 1-second silent WAV file
    silent_wav_base64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA="
    
    payload = {
        "input": {
            "audio": silent_wav_base64,
            "generate_insights": True
        }
    }
    
    print("🤖 Testing Phi-4 with minimal Whisper load...")
    print("=" * 50)
    print("Strategy: Use silent audio to bypass Whisper issues")
    print("Focus: Test if Phi-4 GPU acceleration works")
    print("=" * 50)
    
    start = time.time()
    response = requests.post(
        f"https://api.runpod.ai/v2/{os.environ.get('RUNPOD_ENDPOINT_ID')}/runsync",
        headers=headers,
        json=payload,
        timeout=180
    )
    elapsed = time.time() - start
    
    print(f"\nResponse time: {elapsed:.1f}s")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get("status") == "COMPLETED":
            output = result.get("output", {})
            print("\n✅ Request completed!")
            
            # Check transcription (should be empty or minimal)
            transcription = output.get('transcription', '')
            print(f"\nTranscription: '{transcription}' (length: {len(transcription)})")
            
            # Check timing
            times = output.get('processing_time', {})
            print(f"\n⏱️  Timing Breakdown:")
            print(f"  - Transcription: {times.get('transcription', 0):.2f}s")
            if 'insights' in times:
                print(f"  - Medical Insights: {times.get('insights', 0):.2f}s")
            print(f"  - Total: {times.get('total', 0):.2f}s")
            
            # Even with empty transcription, handler might generate insights
            insights = output.get('medical_insights', '')
            if insights:
                print(f"\n🤖 Insights generated: {len(insights)} chars")
                
        elif result.get("status") == "FAILED":
            print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")
            error_details = result.get('output', {})
            if error_details:
                print(f"Error type: {error_details.get('error_type', 'Unknown')}")
                print(f"Details: {json.dumps(error_details, indent=2)}")
        else:
            print(f"\nStatus: {result.get('status')}")
            print(json.dumps(result, indent=2))
    else:
        print(f"\n❌ HTTP Error: {response.text}")

if __name__ == "__main__":
    print("🚀 Phi-4 GPU Test (Silent Audio)")
    test_phi_with_silent_audio()