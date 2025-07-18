#!/usr/bin/env python3
"""
Example usage of IASO Medical Services via MCP
Shows both independent and orchestrated usage patterns
"""

import asyncio
import json
from typing import Dict, Any

# Example 1: Independent Service Usage
async def example_independent_usage():
    """Use services independently"""
    
    print("=== Example 1: Independent Service Usage ===\n")
    
    # Direct Whisper usage
    print("1. Transcribing audio with Whisper:")
    whisper_result = {
        "tool": "transcribe_audio",
        "arguments": {
            "audio_url": "https://example.com/medical-dictation.wav",
            "language": "en"
        }
    }
    print(f"Request: {json.dumps(whisper_result, indent=2)}")
    print("Response: Transcription completed\n")
    
    # Direct Phi-4 usage  
    print("2. Generating SOAP note with Phi-4:")
    phi4_result = {
        "tool": "generate_soap_note",
        "arguments": {
            "text": "Patient presents with chest pain for 2 hours...",
            "include_reasoning": True
        }
    }
    print(f"Request: {json.dumps(phi4_result, indent=2)}")
    print("Response: SOAP note generated\n")

# Example 2: Orchestrated Workflow
async def example_orchestrated_workflow():
    """Use orchestrator for complex workflows"""
    
    print("=== Example 2: Orchestrated Workflow ===\n")
    
    # Complete medical dictation processing
    print("1. Process complete medical dictation:")
    orchestrator_request = {
        "tool": "process_medical_dictation",
        "arguments": {
            "audio_url": "https://example.com/patient-visit.wav",
            "outputs": ["transcription", "soap_note", "clinical_summary", "medical_insights"],
            "metadata": {
                "provider": "Dr. Smith",
                "specialty": "Internal Medicine",
                "visit_type": "Follow-up"
            }
        }
    }
    print(f"Request: {json.dumps(orchestrator_request, indent=2)}")
    print("Response: All outputs generated through coordinated workflow\n")

# Example 3: Custom Workflow
async def example_custom_workflow():
    """Create custom multi-step workflow"""
    
    print("=== Example 3: Custom Workflow ===\n")
    
    custom_workflow = {
        "tool": "execute_custom_workflow",
        "arguments": {
            "inputs": {
                "audio_url": "https://example.com/complex-case.wav"
            },
            "workflow_steps": [
                {
                    "service": "whisper",
                    "tool": "transcribe_medical_dictation",
                    "parameters": {
                        "audio_url": "$audio_url",
                        "speaker_info": "Dr. Johnson, Cardiologist"
                    }
                },
                {
                    "service": "phi4",
                    "tool": "analyze_clinical_case",
                    "parameters": {
                        "case_text": "$step_1_result.transcription",
                        "analysis_type": "differential_diagnosis"
                    }
                },
                {
                    "service": "phi4",
                    "tool": "generate_medical_report",
                    "parameters": {
                        "clinical_data": "$step_2_result.analysis",
                        "report_type": "consultation",
                        "specialty": "cardiology"
                    }
                }
            ]
        }
    }
    print(f"Request: {json.dumps(custom_workflow, indent=2)}")
    print("Response: Multi-step workflow completed\n")

# Example 4: Service Discovery
async def example_service_discovery():
    """Discover available services and capabilities"""
    
    print("=== Example 4: Service Discovery ===\n")
    
    # Query all capabilities
    print("1. Query all available services:")
    discovery_request = {
        "tool": "query_service_capabilities",
        "arguments": {}
    }
    print(f"Request: {json.dumps(discovery_request, indent=2)}")
    
    # Query specific capability
    print("\n2. Find services for SOAP generation:")
    capability_request = {
        "tool": "query_service_capabilities",
        "arguments": {
            "capability": "soap_generation"
        }
    }
    print(f"Request: {json.dumps(capability_request, indent=2)}")

# Example 5: Real-world Medical Scribe Workflow
async def example_medical_scribe_workflow():
    """Complete medical scribe workflow"""
    
    print("=== Example 5: Medical Scribe Workflow ===\n")
    
    # Step 1: Record dictation (simulated)
    print("Step 1: Doctor dictates patient encounter")
    
    # Step 2: Process through orchestrator
    scribe_workflow = {
        "tool": "process_medical_dictation",
        "arguments": {
            "audio_url": "https://example.com/dr-smith-patient-johnson.wav",
            "outputs": ["transcription", "soap_note", "clinical_summary"],
            "metadata": {
                "encounter_id": "ENC-2025-001234",
                "patient_id": "PAT-567890",
                "provider": "Dr. Sarah Smith",
                "date": "2025-07-17",
                "visit_type": "New Patient Consultation",
                "specialty": "Internal Medicine"
            }
        }
    }
    
    print(f"Step 2: Process dictation:\n{json.dumps(scribe_workflow, indent=2)}")
    
    # Step 3: Results would include:
    print("\nStep 3: Results include:")
    print("- Accurate transcription with medical terminology")
    print("- Structured SOAP note ready for EHR")
    print("- Concise clinical summary for quick review")
    print("- All completed in under 30 seconds")

# Example 6: Integration Patterns
async def example_integration_patterns():
    """Show different integration patterns"""
    
    print("=== Example 6: Integration Patterns ===\n")
    
    print("1. EHR Integration Pattern:")
    print("   EHR System → IASO Orchestrator → Multiple Services → Structured Data → EHR")
    
    print("\n2. Mobile App Pattern:")
    print("   Mobile App → Whisper MCP → Transcription")
    print("   Mobile App → Phi-4 MCP → Clinical Insights")
    
    print("\n3. Voice Assistant Pattern:")
    print("   Voice Command → Orchestrator → Intelligent Routing → Response")
    
    print("\n4. Batch Processing Pattern:")
    print("   Multiple Audio Files → Orchestrator → Parallel Processing → Bulk Results")

async def main():
    """Run all examples"""
    print("IASO Medical Services MCP Examples\n")
    print("This demonstrates how medical AI services can be used")
    print("both independently and through intelligent orchestration.\n")
    
    await example_independent_usage()
    await example_orchestrated_workflow()
    await example_custom_workflow()
    await example_service_discovery()
    await example_medical_scribe_workflow()
    await example_integration_patterns()
    
    print("\n=== Key Benefits ===")
    print("1. Services work independently - use only what you need")
    print("2. Orchestrator provides intelligent coordination when needed")
    print("3. Standard MCP interface works with any MCP client")
    print("4. Easy to extend with new medical AI services")
    print("5. Supports both simple and complex medical workflows")

if __name__ == "__main__":
    asyncio.run(main())