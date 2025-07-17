#!/usr/bin/env python3
"""
Test the complete medical scribe workflow:
Audio → Whisper → Transcription → Phi-4 → SOAP Note + Summary
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def call_whisper(audio_url):
    """Step 1: Transcribe audio with Whisper"""
    print("\n📢 Step 1: Transcribing audio with Whisper...")
    
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "audio": audio_url,
            "return_segments": False
        }
    }
    
    response = requests.post(
        f"https://api.runpod.ai/v2/{os.environ.get('WHISPER_ENDPOINT_ID')}/runsync",
        headers=headers,
        json=payload,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "COMPLETED":
            transcription = result["output"]["transcription"]
            print(f"✅ Transcription complete ({result['output']['processing_time']:.1f}s)")
            return transcription
    
    print("❌ Transcription failed")
    return None

def call_phi4(text, prompt_type="soap"):
    """Step 2: Generate SOAP note or summary with Phi-4"""
    print(f"\n🤖 Step 2: Generating {prompt_type.upper()} with Phi-4...")
    
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "text": text,
            "prompt_type": prompt_type,
            "max_tokens": 4096
        }
    }
    
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
            print(f"✅ {prompt_type.upper()} generated ({output['processing_time']:.1f}s)")
            print(f"   Tokens: {output['tokens_generated']} @ {output['tokens_per_second']} tok/s")
            return output["insights"]
    
    print(f"❌ {prompt_type} generation failed")
    return None

def test_full_workflow():
    """Test the complete workflow"""
    print("🏥 IASO Medical Scribe Workflow Test")
    print("=" * 60)
    
    # Test with a medical sample (using JFK for now, replace with medical audio)
    audio_url = "https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav"
    
    # For real medical testing, use something like:
    # audio_url = "https://example.com/medical-dictation-sample.wav"
    
    # Step 1: Transcribe
    transcription = call_whisper(audio_url)
    if not transcription:
        return
    
    print(f"\n📝 Transcription:")
    print(f'"{transcription}"')
    
    # Step 2: Generate SOAP note
    soap_note = call_phi4(transcription, "soap")
    if soap_note:
        print(f"\n📋 SOAP Note:")
        print("-" * 60)
        print(soap_note)
    
    # Step 3: Generate summary
    summary = call_phi4(transcription, "summary")
    if summary:
        print(f"\n📄 Clinical Summary:")
        print("-" * 60)
        print(summary)

# Example with medical transcription
def test_with_medical_text():
    """Test with actual medical transcription"""
    print("\n🏥 Testing with Medical Transcription")
    print("=" * 60)
    
    # Sample medical dictation
    medical_text = """
    This is Doctor Smith. Patient is John Doe, medical record number 12345.
    Today's date is July 17th, 2024.
    
    Chief complaint is chest pain for the past 3 hours. Patient is a 45-year-old 
    male who presents with substernal chest pressure, rated 7 out of 10, radiating 
    to the left arm. Associated with diaphoresis and mild shortness of breath.
    
    Past medical history significant for hypertension and type 2 diabetes.
    Current medications include metformin 1000mg twice daily, lisinopril 20mg daily.
    Patient denies any drug allergies.
    
    On examination, blood pressure 160/95, pulse 92 and regular, respiratory rate 18,
    temperature 98.6. Patient appears anxious and diaphoretic. Cardiac exam reveals
    regular rate and rhythm, no murmurs. Lungs clear to auscultation bilaterally.
    
    EKG shows normal sinus rhythm with no acute ST changes. Troponin pending.
    
    Assessment: Acute chest pain, rule out acute coronary syndrome versus anxiety.
    
    Plan: Will obtain serial troponins and repeat EKG in one hour. Start aspirin
    325mg, give sublingual nitroglycerin for pain. If troponins negative and pain
    resolves, will consider discharge with cardiology follow-up. If positive or
    worsening symptoms, will admit for cardiac catheterization.
    """
    
    # Generate SOAP note
    soap_note = call_phi4(medical_text.strip(), "soap")
    if soap_note:
        print(f"\n📋 SOAP Note:")
        print("-" * 60)
        print(soap_note)
    
    # Generate summary
    summary = call_phi4(medical_text.strip(), "summary")
    if summary:
        print(f"\n📄 Clinical Summary:")
        print("-" * 60)
        print(summary)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "medical":
        test_with_medical_text()
    else:
        test_full_workflow()