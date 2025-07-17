#!/usr/bin/env python3
"""Get results from a completed job"""

import requests
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def get_job_result(job_id):
    """Fetch completed job results"""
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    endpoint_id = os.environ.get('PHI4_ENDPOINT_ID')
    url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    
    print(f"Fetching results for job: {job_id}")
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get('status') == 'COMPLETED':
            output = result.get('output', {})
            
            # Show metrics
            print(f"\n⏱️  Processing Metrics:")
            print(f"  - Generation time: {output.get('processing_time', 0):.2f}s")
            print(f"  - Tokens generated: {output.get('tokens_generated', 0)}")
            print(f"  - Speed: {output.get('tokens_per_second', 0)} tokens/s")
            
            # Save the summary
            summary = output.get("insights", "No insights generated")
            
            # Save to file
            with open("obstetric_summary_result.txt", "w") as f:
                f.write("OBSTETRIC NOTE SUMMARY\n")
                f.write("=" * 80 + "\n\n")
                f.write(summary)
                f.write("\n\n" + "=" * 80 + "\n")
                f.write(f"Tokens: {output.get('tokens_generated', 0)}\n")
                f.write(f"Time: {output.get('processing_time', 0):.2f}s\n")
                f.write(f"Speed: {output.get('tokens_per_second', 0)} tokens/s\n")
            
            print(f"\n✅ Summary saved to obstetric_summary_result.txt")
            
            # Also print summary
            print("\n" + "="*80)
            print("📄 MEDICAL SUMMARY:")
            print("="*80)
            print(summary)
            
        else:
            print(f"Job status: {result.get('status')}")
            print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    job_id = sys.argv[1] if len(sys.argv) > 1 else "sync-3a20e3d8-6f37-4320-ab85-a5a9ad1e2ae0-e1"
    get_job_result(job_id)