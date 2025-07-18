#!/usr/bin/env python3
"""
Simple IASOQL test with job waiting
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

# Load from the RunPod service .env file
load_dotenv('/Users/vivekkrishnan/dev/iaso/services/iaso-scribe/runpod/.env')

def wait_for_job(job_id, endpoint_id, api_key, max_wait=60):
    """Wait for job to complete"""
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            print(f"❌ Timeout after {max_wait}s")
            return None
            
        response = requests.get(
            f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            
            if status == 'COMPLETED':
                print(f"✅ Job completed in {elapsed:.1f}s")
                return result
            elif status == 'FAILED':
                print(f"❌ Job failed: {result.get('error')}")
                return result
            else:
                print(f"Status: {status} ({elapsed:.0f}s elapsed)", end='\r')
                time.sleep(2)
        else:
            print(f"❌ Error checking status: {response.status_code}")
            return None

def test_iasoql():
    """Test IASOQL with simple query"""
    
    api_key = os.environ.get('RUNPOD_API_KEY')
    endpoint_id = os.environ.get('IASOQL_ENDPOINT_ID')
    
    print(f"Testing IASOQL endpoint: {endpoint_id}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Simple query
    payload = {
        "input": {
            "text": "How many patients are in the system?",
            "query": "How many patients are in the system?"
        }
    }
    
    print("📤 Sending request...")
    
    # Submit job
    response = requests.post(
        f"https://api.runpod.ai/v2/{endpoint_id}/runsync",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get("status") == "IN_QUEUE":
            print(f"Job queued: {result.get('id')}")
            # Wait for completion
            final_result = wait_for_job(result['id'], endpoint_id, api_key)
            if final_result:
                print(json.dumps(final_result, indent=2))
        else:
            print(json.dumps(result, indent=2))
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_iasoql()