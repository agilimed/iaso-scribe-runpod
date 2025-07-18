#!/usr/bin/env python3
"""
Comprehensive test suite for all IASO MCP tools
Tests each tool individually and in combination
"""

import asyncio
import os
import json
from typing import Dict, Any, List
from datetime import datetime

# Import MCP servers directly for testing
from whisper_mcp_server import WhisperMCPServer
from phi4_mcp_server import Phi4MCPServer
from iaso_orchestrator import IASOOrchestrator

# Test data
TEST_AUDIO_URL = "https://github.com/openai/whisper/raw/main/tests/jfk.flac"
MEDICAL_AUDIO_URL = "https://example.com/medical-dictation.wav"  # Placeholder

# Sample medical texts for testing
SAMPLE_OBSTETRIC_NOTE = """
Patient Name: Jane Smith
Date: July 17, 2025
MRN: 123456

Chief Complaint: Routine prenatal visit at 28 weeks gestation.

History of Present Illness: Ms. Smith is a 28-year-old G2P1 at 28 weeks gestation by LMP. 
She reports feeling well with good fetal movement. Denies vaginal bleeding, leaking fluid, 
contractions, headaches, visual changes, or epigastric pain. Reports mild lower back discomfort 
and occasional Braxton Hicks contractions.

Physical Examination:
- BP: 118/72
- Weight: 165 lbs (pre-pregnancy: 145 lbs)
- Fundal height: 28 cm
- FHR: 145 bpm, regular

Assessment: Uncomplicated pregnancy at 28 weeks.

Plan:
- Continue prenatal vitamins
- Glucose tolerance test ordered
- RhoGAM if Rh negative
- Return in 2 weeks
"""

SAMPLE_CARDIOLOGY_NOTE = """
Patient is a 67-year-old male with history of coronary artery disease, status post CABG in 2018, 
presenting for follow-up. Reports improved exercise tolerance since last visit. Currently walking 
30 minutes daily without chest pain or dyspnea. Denies orthopnea, PND, or lower extremity edema.

Current medications: Aspirin 81mg daily, Atorvastatin 40mg daily, Metoprolol 50mg BID, 
Lisinopril 10mg daily.

Vital Signs: BP 128/76, HR 68 regular, RR 16, O2 sat 98% on RA
Cardiac Exam: Regular rate and rhythm, no murmurs, rubs, or gallops. No JVD.
Lungs: Clear to auscultation bilaterally
Extremities: No edema, pulses 2+ throughout

Recent Echo: EF 55%, mild LVH, no significant valvular disease
"""

class MCPTestSuite:
    """Comprehensive test suite for MCP services"""
    
    def __init__(self):
        self.results = []
        self.test_count = 0
        self.passed_count = 0
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        self.test_count += 1
        if passed:
            self.passed_count += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}")
        
        if details:
            print(f"   {details}")
        
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_whisper_tools(self):
        """Test all Whisper MCP tools"""
        print("\n=== Testing Whisper MCP Tools ===")
        
        # Test transcribe_audio
        try:
            result = await self.call_whisper_tool("transcribe_audio", {
                "audio_url": TEST_AUDIO_URL,
                "language": "en"
            })
            
            has_transcription = "transcription" in result and result["transcription"]
            self.log_test(
                "Whisper: transcribe_audio",
                has_transcription,
                f"Transcribed {len(result.get('transcription', ''))} characters"
            )
        except Exception as e:
            self.log_test("Whisper: transcribe_audio", False, str(e))
        
        # Test transcribe_medical_dictation
        try:
            result = await self.call_whisper_tool("transcribe_medical_dictation", {
                "audio_url": TEST_AUDIO_URL,
                "speaker_info": "Dr. Test, Internal Medicine"
            })
            
            has_segments = "segments" in result and result["segments"]
            self.log_test(
                "Whisper: transcribe_medical_dictation",
                has_segments,
                f"Returned {len(result.get('segments', []))} segments"
            )
        except Exception as e:
            self.log_test("Whisper: transcribe_medical_dictation", False, str(e))
        
        # Test detect_audio_language
        try:
            result = await self.call_whisper_tool("detect_audio_language", {
                "audio_url": TEST_AUDIO_URL
            })
            
            has_language = "detected_language" in result
            self.log_test(
                "Whisper: detect_audio_language",
                has_language,
                f"Detected: {result.get('detected_language', 'unknown')}"
            )
        except Exception as e:
            self.log_test("Whisper: detect_audio_language", False, str(e))
    
    async def test_phi4_tools(self):
        """Test all Phi-4 MCP tools"""
        print("\n=== Testing Phi-4 MCP Tools ===")
        
        # Test generate_soap_note
        try:
            result = await self.call_phi4_tool("generate_soap_note", {
                "text": SAMPLE_OBSTETRIC_NOTE,
                "include_reasoning": True
            })
            
            has_soap = "soap_note" in result and result["soap_note"]
            has_reasoning = "clinical_reasoning" in result
            self.log_test(
                "Phi-4: generate_soap_note",
                has_soap,
                f"Generated SOAP with {'reasoning' if has_reasoning else 'no reasoning'}"
            )
        except Exception as e:
            self.log_test("Phi-4: generate_soap_note", False, str(e))
        
        # Test create_clinical_summary
        try:
            result = await self.call_phi4_tool("create_clinical_summary", {
                "text": SAMPLE_CARDIOLOGY_NOTE,
                "max_words": 150
            })
            
            has_summary = "summary" in result and result["summary"]
            word_count = result.get("word_count", 0)
            self.log_test(
                "Phi-4: create_clinical_summary",
                has_summary and word_count <= 200,
                f"Generated {word_count} word summary"
            )
        except Exception as e:
            self.log_test("Phi-4: create_clinical_summary", False, str(e))
        
        # Test extract_medical_insights
        try:
            result = await self.call_phi4_tool("extract_medical_insights", {
                "text": SAMPLE_CARDIOLOGY_NOTE,
                "insight_types": ["medications", "diagnoses", "symptoms"]
            })
            
            has_insights = "insights" in result and result["insights"]
            self.log_test(
                "Phi-4: extract_medical_insights",
                has_insights,
                "Extracted medical insights"
            )
        except Exception as e:
            self.log_test("Phi-4: extract_medical_insights", False, str(e))
        
        # Test analyze_clinical_case
        try:
            result = await self.call_phi4_tool("analyze_clinical_case", {
                "case_text": SAMPLE_OBSTETRIC_NOTE,
                "analysis_type": "risk_assessment"
            })
            
            has_analysis = "analysis" in result and result["analysis"]
            self.log_test(
                "Phi-4: analyze_clinical_case",
                has_analysis,
                "Performed risk assessment"
            )
        except Exception as e:
            self.log_test("Phi-4: analyze_clinical_case", False, str(e))
        
        # Test generate_medical_report
        try:
            result = await self.call_phi4_tool("generate_medical_report", {
                "clinical_data": SAMPLE_CARDIOLOGY_NOTE,
                "report_type": "progress",
                "specialty": "Cardiology"
            })
            
            has_report = "report" in result and result["report"]
            self.log_test(
                "Phi-4: generate_medical_report",
                has_report,
                "Generated progress report"
            )
        except Exception as e:
            self.log_test("Phi-4: generate_medical_report", False, str(e))
    
    async def test_orchestrator_tools(self):
        """Test orchestrator tools"""
        print("\n=== Testing Orchestrator Tools ===")
        
        # Test process_medical_dictation
        try:
            result = await self.call_orchestrator_tool("process_medical_dictation", {
                "audio_url": TEST_AUDIO_URL,
                "outputs": ["transcription", "soap_note"],
                "metadata": {
                    "provider": "Dr. Test",
                    "encounter_id": "TEST-001"
                }
            })
            
            is_complete = result.get("status") == "completed"
            has_results = "results" in result
            self.log_test(
                "Orchestrator: process_medical_dictation",
                is_complete and has_results,
                f"Processed {result.get('workflow_steps', 0)} steps"
            )
        except Exception as e:
            self.log_test("Orchestrator: process_medical_dictation", False, str(e))
        
        # Test query_service_capabilities
        try:
            result = await self.call_orchestrator_tool("query_service_capabilities", {})
            
            has_services = "services" in result
            has_capabilities = "capabilities" in result
            self.log_test(
                "Orchestrator: query_service_capabilities",
                has_services and has_capabilities,
                f"Found {len(result.get('services', {}))} services"
            )
        except Exception as e:
            self.log_test("Orchestrator: query_service_capabilities", False, str(e))
        
        # Test execute_custom_workflow
        try:
            result = await self.call_orchestrator_tool("execute_custom_workflow", {
                "inputs": {"text": SAMPLE_OBSTETRIC_NOTE},
                "workflow_steps": [
                    {
                        "service": "phi4",
                        "tool": "generate_soap_note",
                        "parameters": {"text": "$text"}
                    }
                ]
            })
            
            is_complete = result.get("status") == "completed"
            self.log_test(
                "Orchestrator: execute_custom_workflow",
                is_complete,
                "Executed custom workflow"
            )
        except Exception as e:
            self.log_test("Orchestrator: execute_custom_workflow", False, str(e))
    
    async def test_end_to_end_workflows(self):
        """Test complete end-to-end workflows"""
        print("\n=== Testing End-to-End Workflows ===")
        
        # Test audio → transcription → SOAP workflow
        try:
            # Simulate the workflow since we need real audio
            print("\n--- Audio → Transcription → SOAP Workflow ---")
            
            # Step 1: Transcribe (simulated)
            transcription = "Patient reports chest pain for 2 hours, crushing sensation, radiating to left arm."
            
            # Step 2: Generate SOAP from transcription
            result = await self.call_phi4_tool("generate_soap_note", {
                "text": f"Patient states: {transcription}",
                "include_reasoning": False
            })
            
            has_soap = "soap_note" in result
            self.log_test(
                "E2E: Audio → SOAP workflow",
                has_soap,
                "Complete workflow simulated"
            )
        except Exception as e:
            self.log_test("E2E: Audio → SOAP workflow", False, str(e))
        
        # Test multi-service orchestration
        try:
            print("\n--- Multi-Service Orchestration ---")
            
            # Create a complex workflow
            result = await self.call_orchestrator_tool("analyze_patient_encounter", {
                "encounter_data": {
                    "clinical_notes": SAMPLE_CARDIOLOGY_NOTE,
                    "encounter_type": "follow_up"
                },
                "analysis_goals": ["summary", "medications", "diagnoses"]
            })
            
            is_complete = result.get("status") == "completed"
            self.log_test(
                "E2E: Multi-service orchestration",
                is_complete,
                "Complex analysis completed"
            )
        except Exception as e:
            self.log_test("E2E: Multi-service orchestration", False, str(e))
    
    # Helper methods to call services
    async def call_whisper_tool(self, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a Whisper tool directly"""
        server = WhisperMCPServer()
        
        # Mock the call through the service
        if tool == "transcribe_audio":
            return await server.transcribe_audio(args)
        elif tool == "transcribe_medical_dictation":
            return await server.transcribe_medical_dictation(args)
        elif tool == "detect_audio_language":
            return await server.detect_language(args)
        
        return {"error": f"Unknown tool: {tool}"}
    
    async def call_phi4_tool(self, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a Phi-4 tool directly"""
        server = Phi4MCPServer()
        
        # Mock the call through the service
        if tool == "generate_soap_note":
            return await server.generate_soap_note(args)
        elif tool == "create_clinical_summary":
            return await server.create_clinical_summary(args)
        elif tool == "extract_medical_insights":
            return await server.extract_medical_insights(args)
        elif tool == "analyze_clinical_case":
            return await server.analyze_clinical_case(args)
        elif tool == "generate_medical_report":
            return await server.generate_medical_report(args)
        
        return {"error": f"Unknown tool: {tool}"}
    
    async def call_orchestrator_tool(self, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call an orchestrator tool directly"""
        orchestrator = IASOOrchestrator()
        
        # Mock the call through the service
        if tool == "process_medical_dictation":
            return await orchestrator.process_medical_dictation(args)
        elif tool == "analyze_patient_encounter":
            return await orchestrator.analyze_patient_encounter(args)
        elif tool == "query_service_capabilities":
            return await orchestrator.query_capabilities(args)
        elif tool == "execute_custom_workflow":
            return await orchestrator.execute_custom_workflow(args)
        
        return {"error": f"Unknown tool: {tool}"}
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        print(f"Total tests: {self.test_count}")
        print(f"Passed: {self.passed_count}")
        print(f"Failed: {self.test_count - self.passed_count}")
        print(f"Success rate: {(self.passed_count / self.test_count * 100):.1f}%")
        
        # Show failed tests
        failed_tests = [r for r in self.results if not r["passed"]]
        if failed_tests:
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total": self.test_count,
                    "passed": self.passed_count,
                    "failed": self.test_count - self.passed_count,
                    "timestamp": datetime.now().isoformat()
                },
                "results": self.results
            }, f, indent=2)
        
        print("\nDetailed results saved to test_results.json")

async def main():
    """Run all tests"""
    print("IASO MCP Comprehensive Test Suite")
    print("=" * 50)
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check environment
    if not os.getenv("RUNPOD_API_KEY"):
        print("\n⚠️  Warning: RUNPOD_API_KEY not set. Some tests may fail.")
        print("Set with: export RUNPOD_API_KEY=your_api_key")
    
    # Run test suite
    suite = MCPTestSuite()
    
    # Run all test categories
    await suite.test_whisper_tools()
    await suite.test_phi4_tools()
    await suite.test_orchestrator_tools()
    await suite.test_end_to_end_workflows()
    
    # Print summary
    suite.print_summary()

if __name__ == "__main__":
    asyncio.run(main())