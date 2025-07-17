#!/usr/bin/env python3
"""
Check job status by ID
"""

import requests
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def check_job(job_id):
    """Check status of a specific job"""
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    # For sync jobs, append -e1 if not present
    if not job_id.endswith('-e1'):
        job_id = f"{job_id}-e1"
    
    url = f"https://api.runpod.ai/v2/{os.environ.get('RUNPOD_ENDPOINT_ID')}/status/{job_id}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {result.get('status')}")
        
        if result.get('status') == 'COMPLETED':
            output = result.get('output', {})
            print("\n✅ Job completed!")
            print(json.dumps(output, indent=2))
        elif result.get('status') == 'FAILED':
            print("\n❌ Job failed!")
            print(json.dumps(result.get('output', {}), indent=2))
        else:
            print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_job(sys.argv[1])
    else:
        # Default to the job from test_phi_direct
        check_job("sync-ad41ee71-b58f-4a01-90c1-c9262be35f12-e1")