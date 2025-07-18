#!/usr/bin/env python3
"""Test Phi-4 endpoint"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_phi4():
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "text": """Patient is a 45-year-old male presenting with chest pain that started 
            2 hours ago. The pain is described as pressure-like, radiating to the 
            left arm. Patient has a history of hypertension and diabetes. Currently 
            taking metformin 500mg twice daily and lisinopril 10mg once daily. 
            Blood pressure is 150/90, heart rate is 95.""",
            "prompt_type": "medical_insights"
        }
    }
    
    print("Testing Phi-4 endpoint...")
    response = requests.post(
        f"https://api.runpod.ai/v2/{os.environ.get('PHI4_ENDPOINT_ID')}/runsync",
        headers=headers,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    test_phi4()