#!/usr/bin/env python3
"""Check status of a Phi-4 job"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def check_job(job_id=None):
    """Check job status and poll until complete"""
    if not job_id:
        job_id = "sync-2d1432c1-7695-43e3-a630-72d075800d5a-e1"
    
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    endpoint_id = os.environ.get('PHI4_ENDPOINT_ID')
    url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    
    print(f"Checking job: {job_id}")
    print("Polling for results...")
    
    for attempt in range(60):  # Poll for up to 5 minutes
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            
            if status == 'COMPLETED':
                print("\n✅ Job completed!")
                output = result.get('output', {})
                
                # Show metrics
                print(f"\n⏱️  Processing Metrics:")
                print(f"  - Generation time: {output.get('processing_time', 0):.2f}s")
                print(f"  - Tokens generated: {output.get('tokens_generated', 0)}")
                print(f"  - Speed: {output.get('tokens_per_second', 0)} tokens/s")
                
                # Show insights
                print(f"\n📋 Medical Insights:")
                print("-" * 50)
                print(output.get("insights", "No insights generated"))
                break
                
            elif status == 'FAILED':
                print(f"\n❌ Job failed!")
                print(json.dumps(result.get('output', {}), indent=2))
                break
            else:
                print(f"Status: {status} (attempt {attempt + 1}/60)", end='\r')
                time.sleep(5)
        else:
            print(f"Error: {response.status_code}")
            break

if __name__ == "__main__":
    check_job()