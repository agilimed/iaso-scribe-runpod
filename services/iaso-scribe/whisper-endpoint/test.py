#!/usr/bin/env python3
"""Test Whisper endpoint"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_whisper():
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "audio": "https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav",
            "return_segments": True
        }
    }
    
    print("Testing Whisper endpoint...")
    response = requests.post(
        f"https://api.runpod.ai/v2/{os.environ.get('WHISPER_ENDPOINT_ID')}/runsync",
        headers=headers,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    test_whisper()