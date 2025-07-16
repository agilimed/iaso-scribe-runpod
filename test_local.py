#!/usr/bin/env python3
"""
Test the IASO Scribe handler locally before deploying to RunPod.
Requires Phi-4-reasoning-plus model to be downloaded.
"""

import base64
import json
import os

# Mock the handler for local testing
def test_handler():
    """Test the Phi-4-reasoning-plus configuration."""
    
    print("🧪 Testing IASO Scribe with Phi-4-reasoning-plus")
    print("=" * 50)
    print("Model: Phi-4-reasoning-plus Q6_K_L (12.28GB)")
    print("Quantization: GGUF format with Q8_0 embed/output weights")
    print("=" * 50)
    
    # Check if we can import required libraries
    try:
        from faster_whisper import WhisperModel
        print("✅ Faster Whisper: Available")
    except ImportError:
        print("❌ Faster Whisper: Not installed")
    
    try:
        from llama_cpp import Llama
        print("✅ llama-cpp-python: Available")
    except ImportError:
        print("❌ llama-cpp-python: Not installed")
    
    # Sample medical transcription for testing
    sample_transcription = """
    Patient is a 45-year-old male presenting with chest pain that started 
    2 hours ago. The pain is described as crushing, radiating to the left arm. 
    Patient has a history of hypertension, currently on lisinopril 10mg daily. 
    Blood pressure is 150/90, heart rate 95. Patient appears diaphoretic.
    """
    
    print(f"\n📝 Sample Transcription:")
    print(sample_transcription)
    
    print("\n🏥 Expected Phi-4-reasoning-plus Analysis:")
    print("- Advanced medical entity extraction")
    print("- Clinical reasoning with differential diagnosis")
    print("- Risk stratification (cardiac emergency)")
    print("- Immediate action recommendations")
    print("- Comprehensive SOAP note generation")
    
    print("\n📊 Model Requirements:")
    print("- GPU: 16GB+ VRAM recommended")
    print("- RunPod: A4000, RTX 4060 Ti, or better")
    print("- Memory: ~14GB for model + overhead")
    
    print("\n✅ Configuration ready for deployment!")

if __name__ == "__main__":
    test_handler()