#!/usr/bin/env python3
"""
Test RunPod endpoint with async requests and status polling
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

def submit_job(audio_url, generate_insights=True):
    """Submit an async job to RunPod"""
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "audio": audio_url,
            "generate_insights": generate_insights
        }
    }
    
    # Use /run for async request instead of /runsync
    response = requests.post(
        f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        return result.get("id")
    else:
        print(f"Error submitting job: {response.status_code} - {response.text}")
        return None

def check_job_status(job_id):
    """Check the status of a job"""
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
    }
    
    response = requests.get(
        f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error checking status: {response.status_code}")
        return None

def test_with_polling():
    """Test with async request and poll for results"""
    print("🚀 RunPod Async Test")
    print("=" * 50)
    
    # Test audio file - using a more reliable source
    audio_url = "https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav"
    
    print(f"📤 Submitting job...")
    print(f"Audio: {audio_url}")
    
    # Submit async job
    job_id = submit_job(audio_url, generate_insights=False)  # Start without insights
    
    if not job_id:
        print("❌ Failed to submit job")
        return
    
    print(f"✅ Job submitted: {job_id}")
    print("⏳ Polling for results...")
    
    # Poll for status
    max_attempts = 60  # 5 minutes max
    poll_interval = 5  # seconds
    
    for attempt in range(max_attempts):
        status_response = check_job_status(job_id)
        
        if status_response:
            status = status_response.get("status")
            print(f"\rStatus: {status} (attempt {attempt + 1}/{max_attempts})", end="", flush=True)
            
            if status == "COMPLETED":
                print("\n✅ Job completed!")
                output = status_response.get("output", {})
                print(json.dumps(output, indent=2))
                
                # Test with medical insights
                if not output.get("medical_insights"):
                    print("\n🔬 Now testing with medical insights...")
                    job_id_2 = submit_job(audio_url, generate_insights=True)
                    if job_id_2:
                        print(f"✅ Second job submitted: {job_id_2}")
                return
                
            elif status == "FAILED":
                print(f"\n❌ Job failed: {status_response.get('error', 'Unknown error')}")
                return
            
            elif status == "IN_QUEUE":
                print(f"\r📋 Job in queue... (attempt {attempt + 1}/{max_attempts})", end="", flush=True)
        
        time.sleep(poll_interval)
    
    print("\n⏱️ Timeout: Job did not complete within 5 minutes")

def test_stream_logs():
    """Try to get streaming logs if available"""
    print("\n📊 Checking for worker logs...")
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
    }
    
    # Try to get endpoint info
    response = requests.get(
        f"https://api.runpod.ai/v2/{ENDPOINT_ID}",
        headers=headers
    )
    
    if response.status_code == 200:
        print("Endpoint info:")
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_with_polling()
    # test_stream_logs()