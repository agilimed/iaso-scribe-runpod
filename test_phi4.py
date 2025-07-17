#!/usr/bin/env python3
"""Test the Phi-4 endpoint"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def test_phi4():
    """Test Phi-4 medical reasoning"""
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    # Test medical transcription
    test_text = """
    Patient is a 45-year-old male presenting with chest pain that started 
    2 hours ago. The pain is described as pressure-like, radiating to the 
    left arm. Patient has a history of hypertension and diabetes. Currently 
    taking metformin 500mg twice daily and lisinopril 10mg once daily. 
    Blood pressure is 150/90, heart rate is 95. Patient appears anxious
    and diaphoretic. No known drug allergies.
    """
    
    payload = {
        "input": {
            "text": test_text.strip(),
            "prompt_type": "medical_insights",
            "max_tokens": 1024
        }
    }
    
    print("🤖 Testing Phi-4 Medical Reasoning...")
    print("=" * 50)
    print("Input: Medical transcription")
    print("Expected: Detailed medical insights with reasoning")
    print("=" * 50)
    
    # Update this to use PHI4_ENDPOINT_ID when you create the new endpoint
    endpoint_id = os.environ.get('PHI4_ENDPOINT_ID', os.environ.get('RUNPOD_ENDPOINT_ID'))
    
    start_time = time.time()
    response = requests.post(
        f"https://api.runpod.ai/v2/{endpoint_id}/runsync",
        headers=headers,
        json=payload,
        timeout=300  # 5 minutes for model loading + generation
    )
    elapsed = time.time() - start_time
    
    print(f"\nAPI Response time: {elapsed:.1f}s")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get("status") == "COMPLETED":
            output = result.get("output", {})
            print("\n✅ Success!")
            
            # Processing metrics
            print(f"\n⏱️  Processing Metrics:")
            print(f"  - Generation time: {output.get('processing_time', 0):.2f}s")
            print(f"  - Tokens generated: {output.get('tokens_generated', 0)}")
            print(f"  - Speed: {output.get('tokens_per_second', 0)} tokens/s")
            
            # Check if GPU was used (high tokens/s indicates GPU)
            if output.get('tokens_per_second', 0) > 20:
                print("  - 🚀 GPU acceleration: Working!")
            else:
                print("  - ⚠️  GPU acceleration: May not be working")
            
            # Medical insights
            print(f"\n📋 Medical Insights:")
            print("-" * 50)
            print(output.get("insights", "No insights generated"))
            
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
    test_phi4()