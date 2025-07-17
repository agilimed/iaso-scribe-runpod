#!/usr/bin/env python3
"""
Test Phi-4 with Mental Health Note - 750 word summary
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def wait_for_job_completion(job_id, endpoint_id, headers, max_wait=300):
    """Poll job status until completion"""
    print(f"\n⏳ Waiting for job {job_id} to complete...")
    
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            print(f"\n❌ Timeout after {max_wait}s")
            return None
            
        response = requests.get(
            f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            
            if status == 'COMPLETED':
                print(f"\n✅ Job completed in {elapsed:.1f}s")
                return result
            elif status == 'FAILED':
                print(f"\n❌ Job failed")
                return result
            else:
                print(f"Status: {status} ({elapsed:.0f}s elapsed)", end='\r')
                time.sleep(2)
        else:
            print(f"\n❌ Error checking status: {response.status_code}")
            return None

def test_mental_health_summary():
    """Test Phi-4 with mental health consultation note"""
    
    # Read the mental health consultation note
    with open('Mental_Health_Consultation_Note.txt', 'r') as f:
        mental_health_note = f.read()
    
    print("🧠 Testing Phi-4 with Mental Health Consultation Note")
    print("=" * 80)
    print(f"Note length: {len(mental_health_note)} characters")
    print("Target: 750-word clinical summary")
    print("-" * 80)
    
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    endpoint_id = os.environ.get('PHI4_ENDPOINT_ID')
    
    # Use the summary prompt type
    payload = {
        "input": {
            "text": mental_health_note,
            "prompt_type": "summary",
            "max_tokens": 1200,  # ~750 words
            "temperature": 0.7
        }
    }
    
    print("📤 Sending request to Phi-4 endpoint...")
    
    try:
        # Submit job
        response = requests.post(
            f"https://api.runpod.ai/v2/{endpoint_id}/runsync",
            headers=headers,
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            initial_result = response.json()
            
            # Check if job is queued or in progress
            if initial_result.get("status") in ["IN_QUEUE", "IN_PROGRESS"]:
                job_id = initial_result.get("id")
                print(f"Job ID: {job_id}")
                
                # Wait for completion
                result = wait_for_job_completion(job_id, endpoint_id, headers)
                if not result:
                    return
            else:
                result = initial_result
            
            if result.get("status") == "COMPLETED":
                output = result["output"]
                
                print(f"\n✅ Summary generated successfully!")
                print(f"⏱️  Processing time: {output.get('processing_time', 'N/A')}")
                print(f"📊 Tokens generated: {output.get('tokens_generated', 'N/A')}")
                print(f"⚡ Speed: {output.get('tokens_per_second', 'N/A')} tokens/s")
                
                summary = output.get("insights", "")
                
                # Count words
                word_count = len(summary.split())
                print(f"📝 Word count: {word_count}")
                
                print("\n" + "="*80)
                print("📄 MENTAL HEALTH CONSULTATION SUMMARY:")
                print("="*80)
                print(summary)
                print("="*80)
                
                # Save clean summary
                with open("mental_health_summary_750.txt", "w") as f:
                    f.write("MENTAL HEALTH CONSULTATION SUMMARY\n")
                    f.write("="*80 + "\n")
                    f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Word count: {word_count} words\n")
                    f.write("="*80 + "\n\n")
                    f.write(summary)
                    f.write("\n\n" + "="*80 + "\n")
                    f.write("METRICS:\n")
                    f.write(f"- Original note: {len(mental_health_note)} characters\n")
                    f.write(f"- Summary: {word_count} words\n")
                    f.write(f"- Tokens: {output.get('tokens_generated', 'N/A')}\n")
                    f.write(f"- Processing time: {output.get('processing_time', 'N/A')}s\n")
                    f.write(f"- Speed: {output.get('tokens_per_second', 'N/A')} tokens/s\n")
                print("💾 Summary saved to mental_health_summary_750.txt")
                
            else:
                print(f"❌ Job failed:")
                print(json.dumps(result, indent=2))
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mental_health_summary()