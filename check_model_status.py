#!/usr/bin/env python3
"""
Check if models are properly downloaded to network volume
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def check_job_until_complete(job_id, max_attempts=60):
    """Poll job status until complete or timeout"""
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
    }
    
    for attempt in range(max_attempts):
        response = requests.get(
            f"https://api.runpod.ai/v2/{os.environ.get('RUNPOD_ENDPOINT_ID')}/status/{job_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status")
            print(f"\rAttempt {attempt + 1}: Status = {status}", end="", flush=True)
            
            if status == "COMPLETED":
                print("\n✅ Job completed!")
                return result
            elif status == "FAILED":
                print(f"\n❌ Job failed: {result.get('error', 'Unknown error')}")
                return result
        
        time.sleep(5)
    
    print("\n⏱️ Timeout after 5 minutes")
    return None

# Submit async job
headers = {
    "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
    "Content-Type": "application/json"
}

payload = {
    "input": {
        "audio": "https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav",
        "generate_insights": True
    }
}

print("🚀 Submitting job to test Phi-4...")
response = requests.post(
    f"https://api.runpod.ai/v2/{os.environ.get('RUNPOD_ENDPOINT_ID')}/run",
    headers=headers,
    json=payload
)

if response.status_code == 200:
    job_id = response.json().get("id")
    print(f"📋 Job ID: {job_id}")
    print("⏳ Monitoring progress...")
    
    result = check_job_until_complete(job_id)
    if result and result.get("status") == "COMPLETED":
        output = result.get("output", {})
        print(f"\nTranscription: {output.get('transcription', 'N/A')}")
        print(f"\nTiming:")
        times = output.get('processing_time', {})
        print(f"  - Transcription: {times.get('transcription', 0):.2f}s")
        print(f"  - Insights: {times.get('insights', 0):.2f}s")
        print(f"  - Total: {times.get('total', 0):.2f}s")
        print(f"\n🤖 Medical Insights:\n{'-'*50}")
        print(output.get('medical_insights', 'No insights generated'))
else:
    print(f"Failed to submit job: {response.status_code}")