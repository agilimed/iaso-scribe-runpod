#!/usr/bin/env python3
"""
Check RunPod endpoint logs and worker status
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

def check_endpoint_status():
    """Check detailed endpoint status"""
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
    }
    
    # Check endpoint health
    print("🔍 Checking endpoint health...")
    response = requests.get(
        f"https://api.runpod.ai/v2/{ENDPOINT_ID}/health",
        headers=headers
    )
    
    if response.status_code == 200:
        health = response.json()
        print("\n📊 Endpoint Health:")
        print(json.dumps(health, indent=2))
        
        # Extract key metrics
        jobs = health.get("jobs", {})
        workers = health.get("workers", {})
        
        print("\n📈 Summary:")
        print(f"✅ Completed jobs: {jobs.get('completed', 0)}")
        print(f"❌ Failed jobs: {jobs.get('failed', 0)}")
        print(f"🔄 In progress: {jobs.get('inProgress', 0)}")
        print(f"📋 In queue: {jobs.get('inQueue', 0)}")
        print(f"🔁 Retried: {jobs.get('retried', 0)}")
        
        print(f"\n👷 Workers:")
        print(f"Ready: {workers.get('ready', 0)}")
        print(f"Running: {workers.get('running', 0)}")
        print(f"Idle: {workers.get('idle', 0)}")
        print(f"Initializing: {workers.get('initializing', 0)}")
        print(f"Unhealthy: {workers.get('unhealthy', 0)}")
        
        # Calculate failure rate
        total_jobs = jobs.get('completed', 0) + jobs.get('failed', 0)
        if total_jobs > 0:
            failure_rate = (jobs.get('failed', 0) / total_jobs) * 100
            print(f"\n⚠️  Failure rate: {failure_rate:.1f}%")

def test_with_phi4():
    """Test with Phi-4 model enabled to see specific error"""
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Use a working audio URL
    payload = {
        "input": {
            "audio": "https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav",
            "generate_insights": True,  # Enable Phi-4
            "language": "en"
        }
    }
    
    print("\n\n🧪 Testing with Phi-4 insights enabled...")
    print("Audio: JFK speech sample (11 seconds)")
    print("Sending request...")
    
    start = time.time()
    response = requests.post(
        f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync",
        headers=headers,
        json=payload,
        timeout=300
    )
    elapsed = time.time() - start
    
    print(f"\nResponse time: {elapsed:.1f}s")
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\nFull response:")
        print(json.dumps(result, indent=2))
        
        if result.get("status") == "FAILED":
            print("\n❌ FAILED - Error details:")
            print(f"Error: {result.get('error', 'Unknown error')}")
            output = result.get('output', {})
            if output:
                print(f"Error type: {output.get('error_type', 'Unknown')}")
                print(f"Processing time: {output.get('processing_time', 'Unknown')}s")

if __name__ == "__main__":
    print("🚀 RunPod Endpoint Diagnostics")
    print("=" * 50)
    
    check_endpoint_status()
    test_with_phi4()