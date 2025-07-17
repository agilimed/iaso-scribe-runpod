#!/usr/bin/env python3
"""
Test just Phi-4 model without Whisper
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def test_phi_only():
    """Test Phi-4 medical insights generation directly"""
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    # Provide a pre-transcribed medical text
    test_transcription = """
    Patient is a 45-year-old male presenting with chest pain that started 
    2 hours ago. The pain is described as pressure-like, radiating to the 
    left arm. Patient has a history of hypertension and diabetes. Currently 
    taking metformin 500mg twice daily and lisinopril 10mg once daily. 
    Blood pressure is 150/90, heart rate is 95.
    """
    
    payload = {
        "input": {
            "transcription": test_transcription,
            "skip_whisper": True,  # Skip Whisper, use provided transcription
            "generate_insights": True
        }
    }
    
    print("🤖 Testing Phi-4 only (no Whisper)...")
    print("=" * 50)
    print("Input: Pre-transcribed medical text")
    print("Expected: Medical insights in <30s with GPU")
    print("=" * 50)
    
    start = time.time()
    response = requests.post(
        f"https://api.runpod.ai/v2/{os.environ.get('RUNPOD_ENDPOINT_ID')}/runsync",
        headers=headers,
        json=payload,
        timeout=180  # 3 minute timeout
    )
    elapsed = time.time() - start
    
    print(f"\nResponse time: {elapsed:.1f}s")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get("status") == "COMPLETED":
            output = result.get("output", {})
            print("\n✅ Success!")
            
            # Check insights
            insights = output.get('medical_insights', '')
            if insights:
                print(f"\n🤖 Medical Insights Generated: Yes")
                print(f"Length: {len(insights)} characters")
                print(f"\nInsights preview:")
                print("-" * 50)
                print(insights[:500] + "..." if len(insights) > 500 else insights)
                
                # Check timing
                times = output.get('processing_time', {})
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
    print("🚀 IASO Scribe Phi-4 Isolation Test")
    test_phi_only()