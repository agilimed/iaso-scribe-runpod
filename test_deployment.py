#!/usr/bin/env python3
"""
Test script for IASO Scribe RunPod deployment
"""

import requests
import json
import time
import base64
import os

# Configuration
ENDPOINT_ID = "rntxttrdl8uv3i"
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "your-api-key-here")

# RunPod endpoints
HEALTH_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/health"
RUN_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"
RUNSYNC_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"
STATUS_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status"

# Headers
headers = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json"
}

def check_health():
    """Check endpoint health."""
    print("🔍 Checking endpoint health...")
    try:
        response = requests.get(HEALTH_URL, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.text:
            print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def check_status():
    """Check endpoint status."""
    print("\n📊 Checking endpoint status...")
    try:
        response = requests.get(STATUS_URL, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"Status check failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Status check failed: {e}")
    return None

def test_transcription():
    """Test with a sample audio file."""
    print("\n🎤 Testing transcription...")
    
    # Sample audio URL (Star Wars quote)
    test_payload = {
        "input": {
            "audio": "https://www2.cs.uic.edu/~i101/SoundFiles/StarWars60.wav",
            "language": "en",
            "generate_insights": True,
            "return_segments": True
        }
    }
    
    print("Sending test request...")
    print(f"Audio URL: {test_payload['input']['audio']}")
    
    try:
        # Use runsync for immediate response (up to 90 seconds)
        response = requests.post(RUNSYNC_URL, headers=headers, json=test_payload)
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if it's a completed response
            if "output" in result:
                output = result["output"]
                print("\n✅ Transcription successful!")
                print(f"Transcription: {output.get('transcription', 'N/A')[:200]}...")
                print(f"Language: {output.get('language', 'N/A')}")
                print(f"Duration: {output.get('duration', 'N/A')} seconds")
                
                if "medical_insights" in output:
                    print(f"\n🏥 Medical Insights:")
                    print(output["medical_insights"][:500] + "...")
                
                if "processing_time" in output:
                    print(f"\n⏱️  Processing Times:")
                    for key, value in output["processing_time"].items():
                        print(f"  - {key}: {value:.2f}s")
            
            elif "status" in result:
                # It's a job status response
                print(f"Job Status: {result['status']}")
                print(f"Job ID: {result.get('id', 'N/A')}")
                
                # For IN_PROGRESS jobs, you would need to poll
                if result['status'] == "IN_PROGRESS":
                    print("Job is still processing. Use the /status/{job_id} endpoint to check progress.")
                    
            return result
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    return None

def test_medical_audio():
    """Test with a medical context (using same audio but will generate medical insights)."""
    print("\n🏥 Testing medical transcription...")
    
    # You can replace this with an actual medical audio URL
    test_payload = {
        "input": {
            "audio": "https://www2.cs.uic.edu/~i101/SoundFiles/gettysburg10.wav",
            "language": "en",
            "generate_insights": True,
            "return_segments": False
        }
    }
    
    print("Note: Using generic audio, but Phi-4 will analyze it for potential medical context")
    
    try:
        response = requests.post(RUNSYNC_URL, headers=headers, json=test_payload)
        
        if response.status_code == 200:
            result = response.json()
            if "output" in result:
                output = result["output"]
                print("\n✅ Analysis complete!")
                print(f"Transcription: {output.get('transcription', 'N/A')[:200]}...")
                
                if "medical_insights" in output:
                    print(f"\n🏥 Medical Analysis:")
                    print(output["medical_insights"])
                    
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def main():
    """Run all tests."""
    print("🚀 IASO Scribe - RunPod Deployment Test")
    print("=" * 50)
    print(f"Endpoint ID: {ENDPOINT_ID}")
    print(f"API Key: {'Set' if RUNPOD_API_KEY != 'your-api-key-here' else 'Not Set'}")
    
    if RUNPOD_API_KEY == "your-api-key-here":
        print("\n⚠️  Please set your RunPod API key:")
        print("export RUNPOD_API_KEY='your-actual-api-key'")
        return
    
    # Check health
    if check_health():
        print("✅ Endpoint is healthy!")
    
    # Check status
    status = check_status()
    
    # Run tests
    print("\n" + "=" * 50)
    print("Running transcription tests...")
    print("=" * 50)
    
    # Test 1: Basic transcription
    test_transcription()
    
    # Test 2: Medical context
    test_medical_audio()
    
    print("\n✅ Testing complete!")
    print("\n📝 Note: First run will download models (~14GB), so it may timeout.")
    print("Subsequent runs will be much faster!")

if __name__ == "__main__":
    main()