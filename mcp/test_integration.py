#!/usr/bin/env python3
"""
Integration test for IASO MCP services
Tests the complete workflow: audio → transcription → SOAP note
"""

import asyncio
import os
import json
from typing import Dict, Any
import httpx
from datetime import datetime

# Test configuration
TEST_AUDIO_URL = "https://github.com/openai/whisper/raw/main/tests/jfk.flac"  # Sample audio
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
WHISPER_ENDPOINT_ID = os.getenv("WHISPER_ENDPOINT_ID", "rntxttrdl8uv3i")
PHI4_ENDPOINT_ID = os.getenv("PHI4_ENDPOINT_ID", "tmmwa4q8ax5sg4")

class IntegrationTester:
    """Test the complete MCP integration"""
    
    def __init__(self):
        self.api_key = RUNPOD_API_KEY
        if not self.api_key:
            raise ValueError("RUNPOD_API_KEY environment variable not set")
    
    async def test_whisper_service(self) -> Dict[str, Any]:
        """Test Whisper transcription service"""
        print("\n=== Testing Whisper Service ===")
        
        url = f"https://api.runpod.ai/v2/{WHISPER_ENDPOINT_ID}/runsync"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": {
                "audio": TEST_AUDIO_URL,
                "language": "en",
                "return_segments": False,
                "vad_filter": True
            }
        }
        
        print(f"Calling Whisper endpoint: {WHISPER_ENDPOINT_ID}")
        print(f"Audio URL: {TEST_AUDIO_URL}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            start_time = datetime.now()
            response = await client.post(url, headers=headers, json=payload)
            end_time = datetime.now()
            
            print(f"Response status: {response.status_code}")
            print(f"Response time: {(end_time - start_time).total_seconds():.2f}s")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "COMPLETED":
                    output = result.get("output", {})
                    print(f"Transcription: {output.get('transcription', '')[:100]}...")
                    print(f"Language detected: {output.get('language', 'unknown')}")
                    print(f"Audio duration: {output.get('duration', 0):.2f}s")
                    print(f"Processing time: {output.get('processing_time', 0):.2f}s")
                    return output
                else:
                    print(f"Job failed: {result}")
                    return {}
            else:
                print(f"HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                return {}
    
    async def test_phi4_service(self, text: str) -> Dict[str, Any]:
        """Test Phi-4 medical reasoning service"""
        print("\n=== Testing Phi-4 Service ===")
        
        url = f"https://api.runpod.ai/v2/{PHI4_ENDPOINT_ID}/runsync"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Create a medical context from the transcription
        medical_text = f"""Patient presents with the following statement: "{text}"
        
Please generate a SOAP note based on this information."""
        
        payload = {
            "input": {
                "text": medical_text,
                "prompt_type": "soap",
                "max_tokens": 2048,
                "temperature": 0.7
            }
        }
        
        print(f"Calling Phi-4 endpoint: {PHI4_ENDPOINT_ID}")
        print(f"Input text: {medical_text[:100]}...")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            start_time = datetime.now()
            response = await client.post(url, headers=headers, json=payload)
            end_time = datetime.now()
            
            print(f"Response status: {response.status_code}")
            print(f"Response time: {(end_time - start_time).total_seconds():.2f}s")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "COMPLETED":
                    output = result.get("output", {})
                    insights = output.get("insights", "")
                    
                    # Check for tag-based output
                    import re
                    think_match = re.search(r'<think>(.*?)</think>', insights, re.DOTALL)
                    solution_match = re.search(r'<solution>(.*?)</solution>', insights, re.DOTALL)
                    
                    if think_match and solution_match:
                        print("\n--- Clinical Reasoning ---")
                        print(think_match.group(1).strip()[:200] + "...")
                        print("\n--- SOAP Note ---")
                        print(solution_match.group(1).strip())
                    else:
                        print("\n--- Generated Output ---")
                        print(insights[:500] + "..." if len(insights) > 500 else insights)
                    
                    print(f"\nProcessing time: {output.get('processing_time', 0):.2f}s")
                    print(f"Tokens generated: {output.get('tokens_generated', 'N/A')}")
                    return output
                else:
                    print(f"Job failed: {result}")
                    return {}
            else:
                print(f"HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                return {}
    
    async def test_orchestrated_workflow(self) -> None:
        """Test the complete orchestrated workflow"""
        print("\n=== Testing Orchestrated Workflow ===")
        print("Workflow: Audio → Transcription → SOAP Note\n")
        
        # Step 1: Transcribe audio
        transcription_result = await self.test_whisper_service()
        
        if not transcription_result:
            print("❌ Whisper service failed")
            return
        
        transcription = transcription_result.get("transcription", "")
        if not transcription:
            print("❌ No transcription received")
            return
        
        print(f"\n✅ Transcription successful: {len(transcription)} characters")
        
        # Step 2: Generate SOAP note
        soap_result = await self.test_phi4_service(transcription)
        
        if not soap_result:
            print("❌ Phi-4 service failed")
            return
        
        print("\n✅ SOAP note generation successful")
        
        # Summary
        print("\n=== Workflow Summary ===")
        print(f"1. Audio transcribed in {transcription_result.get('processing_time', 0):.2f}s")
        print(f"2. SOAP note generated in {soap_result.get('processing_time', 0):.2f}s")
        print(f"3. Total workflow time: {transcription_result.get('processing_time', 0) + soap_result.get('processing_time', 0):.2f}s")
        print("\n✅ Complete workflow successful!")
    
    async def test_medical_dictation(self) -> None:
        """Test with a simulated medical dictation"""
        print("\n=== Testing Medical Dictation Workflow ===")
        
        # Simulate a medical dictation transcription
        medical_dictation = """
        This is Dr. Smith recording a patient encounter for John Doe, medical record number 12345.
        
        The patient is a 45-year-old male presenting today with complaints of chest pain that started 
        approximately 2 hours ago. The pain is described as a crushing sensation in the center of the 
        chest, radiating to the left arm. Patient rates the pain as 8 out of 10. He also reports 
        associated shortness of breath and diaphoresis.
        
        Past medical history is significant for hypertension and type 2 diabetes. Current medications 
        include metformin 1000mg twice daily and lisinopril 10mg daily. No known drug allergies.
        
        On examination, blood pressure is 165/95, pulse 110, respiratory rate 22, temperature 98.6.
        Patient appears anxious and diaphoretic. Cardiac exam reveals regular rhythm without murmurs.
        Lungs are clear to auscultation bilaterally.
        
        Given the presentation, I'm concerned about acute coronary syndrome. Will order EKG, 
        troponin levels, and chest x-ray. Starting aspirin 325mg, initiating cardiac monitoring,
        and will consult cardiology for further evaluation.
        """
        
        print("Using simulated medical dictation...")
        print(f"Dictation preview: {medical_dictation[:150]}...")
        
        # Generate SOAP note from medical dictation
        soap_result = await self.test_phi4_service(medical_dictation)
        
        if soap_result:
            print("\n✅ Medical dictation → SOAP note conversion successful")
        else:
            print("\n❌ Medical dictation processing failed")

async def main():
    """Run all integration tests"""
    print("IASO MCP Integration Tests")
    print("=" * 50)
    
    tester = IntegrationTester()
    
    # Test individual services
    print("\n1. Testing individual services...")
    await tester.test_whisper_service()
    
    # Test complete workflow
    print("\n\n2. Testing complete workflow...")
    await tester.test_orchestrated_workflow()
    
    # Test medical dictation
    print("\n\n3. Testing medical dictation workflow...")
    await tester.test_medical_dictation()

if __name__ == "__main__":
    asyncio.run(main())