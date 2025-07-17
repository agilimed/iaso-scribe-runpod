#!/usr/bin/env python3
"""
Test Phi-4 with tag separation for reasoning and solution
"""

import requests
import json
import os
import time
import re
from dotenv import load_dotenv

load_dotenv()

def parse_tagged_response(response_text):
    """Parse response to extract think and solution sections"""
    think_match = re.search(r'<think>(.*?)</think>', response_text, re.DOTALL)
    solution_match = re.search(r'<solution>(.*?)</solution>', response_text, re.DOTALL)
    
    think_content = think_match.group(1).strip() if think_match else ""
    solution_content = solution_match.group(1).strip() if solution_match else response_text
    
    return {
        "reasoning": think_content,
        "solution": solution_content,
        "has_tags": bool(think_match and solution_match)
    }

def test_tag_separation():
    """Test Phi-4 with a short medical note to see tag separation"""
    
    # Short test note
    test_note = """
    Patient: John Doe, 65-year-old male
    Chief Complaint: Chest pain for 2 hours
    
    History: Sudden onset substernal chest pain while climbing stairs, 
    radiating to left arm. Associated with shortness of breath and diaphoresis.
    
    PMH: Hypertension, Type 2 Diabetes
    Medications: Metoprolol 50mg daily, Metformin 1000mg BID
    
    Vitals: BP 165/95, HR 98, RR 22, O2 93% on RA
    EKG: ST elevation in leads II, III, aVF
    Troponin: 0.45 ng/mL (elevated)
    
    Assessment: STEMI
    Plan: Urgent cardiac catheterization, aspirin 325mg, heparin bolus
    """
    
    print("🏷️  Testing Phi-4 Tag Separation")
    print("=" * 80)
    
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    # Test with medical_insights prompt type
    payload = {
        "input": {
            "text": test_note,
            "prompt_type": "medical_insights",
            "max_tokens": 1000,
            "temperature": 0.7
        }
    }
    
    print("📤 Sending request with tag-based prompting...")
    
    try:
        response = requests.post(
            f"https://api.runpod.ai/v2/{os.environ.get('PHI4_ENDPOINT_ID')}/runsync",
            headers=headers,
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "COMPLETED":
                output = result["output"]
                raw_response = output.get("insights", "")
                
                print(f"\n✅ Response received!")
                print(f"📊 Tokens: {output.get('tokens_generated', 'N/A')}")
                print(f"⏱️  Time: {output.get('processing_time', 'N/A')}s")
                
                # Parse the tagged response
                parsed = parse_tagged_response(raw_response)
                
                if parsed["has_tags"]:
                    print("\n✅ Tags detected! Response properly structured.")
                    
                    print("\n" + "="*80)
                    print("🧠 REASONING (from <think> tags):")
                    print("="*80)
                    print(parsed["reasoning"])
                    
                    print("\n" + "="*80)
                    print("💡 SOLUTION (from <solution> tags):")
                    print("="*80)
                    print(parsed["solution"])
                else:
                    print("\n⚠️  No tags detected. Raw response:")
                    print(raw_response)
                
                # Save parsed output
                with open("tag_separation_demo.json", "w") as f:
                    json.dump({
                        "input": test_note,
                        "raw_response": raw_response,
                        "parsed": parsed,
                        "metrics": output
                    }, f, indent=2)
                print("\n💾 Output saved to tag_separation_demo.json")
                
            else:
                print(f"❌ Job failed: {result}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_tag_separation()