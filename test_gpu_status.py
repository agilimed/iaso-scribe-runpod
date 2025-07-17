#!/usr/bin/env python3
"""
Test GPU status and Phi-4 with medical insights
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def test_with_insights():
    """Test full pipeline with GPU acceleration"""
    
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    # Test with medical insights enabled
    payload = {
        "input": {
            "audio": "https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav",
            "generate_insights": True,
            "stream": False  # Test without streaming first
        }
    }
    
    print("🏥 Testing IASO Scribe with GPU acceleration...")
    print("=" * 50)
    print("Audio: JFK speech (11 seconds)")
    print("Features: Whisper transcription + Phi-4 medical insights")
    print("Expected: <10s for transcription, <20s for insights (with GPU)")
    print("=" * 50)
    
    start = time.time()
    response = requests.post(
        f"https://api.runpod.ai/v2/{os.environ.get('RUNPOD_ENDPOINT_ID')}/runsync",
        headers=headers,
        json=payload,
        timeout=120  # 2 minute timeout
    )
    elapsed = time.time() - start
    
    print(f"\nResponse time: {elapsed:.1f}s")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get("status") == "COMPLETED":
            output = result.get("output", {})
            print("\n✅ Success!")
            
            # Check transcription
            print(f"\n📝 Transcription:")
            print(f"{output.get('transcription', 'N/A')}")
            
            # Check timing
            times = output.get('processing_time', {})
            print(f"\n⏱️  Timing Breakdown:")
            print(f"  - Transcription: {times.get('transcription', 0):.2f}s")
            print(f"  - Medical Insights: {times.get('insights', 0):.2f}s")
            print(f"  - Total: {times.get('total', 0):.2f}s")
            
            # Check insights
            insights = output.get('medical_insights', '')
            print(f"\n🤖 Medical Insights Generated: {'Yes' if insights else 'No'}")
            if insights:
                print(f"  Length: {len(insights)} characters")
                print(f"  Preview: {insights[:200]}...")
                
                # Check if GPU was used
                insights_time = times.get('insights', 0)
                if insights_time < 30:
                    print(f"\n🚀 GPU Acceleration: Likely working! (Insights in {insights_time:.1f}s)")
                else:
                    print(f"\n⚠️  GPU Acceleration: May not be working (Insights took {insights_time:.1f}s)")
            
        elif result.get("status") == "FAILED":
            print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")
            print(f"Output: {json.dumps(result.get('output', {}), indent=2)}")
        else:
            print(f"\nStatus: {result.get('status')}")
            print(json.dumps(result, indent=2))
    else:
        print(f"\n❌ HTTP Error: {response.text}")

if __name__ == "__main__":
    print("🚀 IASO Scribe GPU Status Test")
    test_with_insights()