#!/usr/bin/env python3
"""
IASO Medical Services Orchestrator
Intelligent agent that coordinates multiple medical AI services
"""

import asyncio
import json
import os
import re
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from enum import Enum

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel

class ServiceCapability(Enum):
    """Available service capabilities"""
    TRANSCRIPTION = "transcription"
    MEDICAL_REASONING = "medical_reasoning"
    SOAP_GENERATION = "soap_generation"
    CLINICAL_SUMMARY = "clinical_summary"
    DIAGNOSIS = "diagnosis"
    LAB_ANALYSIS = "lab_analysis"
    PRESCRIPTION = "prescription"
    ICD_CODING = "icd_coding"
    DIALOG_MANAGEMENT = "dialog_management"
    ENTITY_EXTRACTION = "entity_extraction"
    CONVERSATION_ANALYSIS = "conversation_analysis"

class ServiceRegistry:
    """Registry of available medical services"""
    
    def __init__(self):
        self.services = {
            "whisper": {
                "name": "Whisper Transcription",
                "capabilities": [ServiceCapability.TRANSCRIPTION],
                "endpoint": "whisper_mcp_server",
                "status": "active"
            },
            "phi4": {
                "name": "Phi-4 Medical Reasoning",
                "capabilities": [
                    ServiceCapability.MEDICAL_REASONING,
                    ServiceCapability.SOAP_GENERATION,
                    ServiceCapability.CLINICAL_SUMMARY,
                    ServiceCapability.DIAGNOSIS
                ],
                "endpoint": "phi4_mcp_server",
                "status": "active"
            },
            "rasa": {
                "name": "RASA Medical Dialog",
                "capabilities": [
                    ServiceCapability.DIALOG_MANAGEMENT,
                    ServiceCapability.ENTITY_EXTRACTION,
                    ServiceCapability.CONVERSATION_ANALYSIS
                ],
                "endpoint": "rasa_mcp_server",
                "status": "active"
            }
            # Future services can be added here
        }
    
    def get_services_for_capability(self, capability: ServiceCapability) -> List[str]:
        """Get services that provide a specific capability"""
        return [
            service_id 
            for service_id, service in self.services.items()
            if capability in service["capabilities"] and service["status"] == "active"
        ]
    
    def get_service_info(self, service_id: str) -> Optional[Dict]:
        """Get information about a specific service"""
        return self.services.get(service_id)

class WorkflowPlanner:
    """Plans multi-step workflows based on requirements"""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
    
    def plan_workflow(self, inputs: Dict[str, Any], required_outputs: List[str]) -> List[Dict[str, Any]]:
        """Plan a workflow to achieve required outputs from given inputs"""
        steps = []
        available_data = set(inputs.keys())
        required_data = set(required_outputs)
        
        # Determine what we need to produce
        while required_data - available_data:
            for output in required_data - available_data:
                step = self._find_step_for_output(output, available_data)
                if step:
                    steps.append(step)
                    available_data.update(step["outputs"])
                else:
                    raise ValueError(f"Cannot produce required output: {output}")
        
        return steps
    
    def _find_step_for_output(self, output: str, available_data: Set[str]) -> Optional[Dict[str, Any]]:
        """Find a service step that can produce the required output"""
        
        # Mapping of outputs to capabilities and required inputs
        output_mappings = {
            "transcription": {
                "capability": ServiceCapability.TRANSCRIPTION,
                "required_inputs": ["audio_url"],
                "outputs": ["transcription", "language"]
            },
            "soap_note": {
                "capability": ServiceCapability.SOAP_GENERATION,
                "required_inputs": ["transcription"],
                "outputs": ["soap_note"]
            },
            "clinical_summary": {
                "capability": ServiceCapability.CLINICAL_SUMMARY,
                "required_inputs": ["transcription"],
                "outputs": ["clinical_summary"]
            },
            "medical_insights": {
                "capability": ServiceCapability.MEDICAL_REASONING,
                "required_inputs": ["transcription"],
                "outputs": ["medical_insights", "diagnoses", "medications"]
            }
        }
        
        mapping = output_mappings.get(output)
        if not mapping:
            return None
        
        # Check if we have required inputs
        if not all(inp in available_data for inp in mapping["required_inputs"]):
            # Try to get missing inputs first
            for inp in mapping["required_inputs"]:
                if inp not in available_data:
                    prerequisite = self._find_step_for_output(inp, available_data)
                    if prerequisite:
                        return prerequisite
            return None
        
        # Find service for this capability
        services = self.registry.get_services_for_capability(mapping["capability"])
        if not services:
            return None
        
        return {
            "service": services[0],
            "capability": mapping["capability"].value,
            "inputs": mapping["required_inputs"],
            "outputs": mapping["outputs"]
        }

class IASOOrchestrator:
    """Intelligent orchestrator for medical AI services"""
    
    def __init__(self):
        self.server = Server("iaso-medical-orchestrator")
        self.registry = ServiceRegistry()
        self.planner = WorkflowPlanner(self.registry)
        self.setup_tools()
    
    def setup_tools(self):
        """Register orchestrator tools"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="process_medical_dictation",
                    description="Process medical dictation from audio to structured documentation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "audio_url": {
                                "type": "string",
                                "description": "URL of medical dictation audio"
                            },
                            "outputs": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["transcription", "soap_note", "clinical_summary", "medical_insights"]
                                },
                                "description": "Desired outputs",
                                "default": ["transcription", "soap_note"]
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata (provider info, patient context, etc.)"
                            }
                        },
                        "required": ["audio_url"]
                    }
                ),
                Tool(
                    name="analyze_patient_encounter",
                    description="Comprehensive analysis of patient encounter data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "encounter_data": {
                                "type": "object",
                                "description": "Patient encounter data (can include text, vitals, labs, etc.)"
                            },
                            "analysis_goals": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific analysis goals"
                            }
                        },
                        "required": ["encounter_data"]
                    }
                ),
                Tool(
                    name="query_service_capabilities",
                    description="Query available services and their capabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "capability": {
                                "type": "string",
                                "description": "Specific capability to search for"
                            }
                        }
                    }
                ),
                Tool(
                    name="execute_custom_workflow",
                    description="Execute a custom workflow with specified steps",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "inputs": {
                                "type": "object",
                                "description": "Initial input data"
                            },
                            "workflow_steps": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "service": {"type": "string"},
                                        "tool": {"type": "string"},
                                        "parameters": {"type": "object"}
                                    }
                                },
                                "description": "Custom workflow steps"
                            }
                        },
                        "required": ["inputs", "workflow_steps"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if name == "process_medical_dictation":
                result = await self.process_medical_dictation(arguments)
            elif name == "analyze_patient_encounter":
                result = await self.analyze_patient_encounter(arguments)
            elif name == "query_service_capabilities":
                result = await self.query_capabilities(arguments)
            elif name == "execute_custom_workflow":
                result = await self.execute_custom_workflow(arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
    
    async def call_service(self, service_id: str, tool: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific service tool via RunPod API"""
        
        # Get service configuration
        service_config = self.registry.get_service_info(service_id)
        if not service_config:
            return {"error": f"Unknown service: {service_id}"}
        
        # Get API key and endpoint IDs from environment
        api_key = os.getenv("RUNPOD_API_KEY")
        if not api_key:
            return {"error": "RUNPOD_API_KEY not configured"}
        
        endpoint_id = None
        if service_id == "whisper":
            endpoint_id = os.getenv("WHISPER_ENDPOINT_ID", "rntxttrdl8uv3i")
        elif service_id == "phi4":
            endpoint_id = os.getenv("PHI4_ENDPOINT_ID", "tmmwa4q8ax5sg4")
        
        if not endpoint_id:
            return {"error": f"No endpoint ID configured for service: {service_id}"}
        
        # Prepare RunPod API call
        url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Map tool calls to RunPod input format
        payload = self._prepare_service_payload(service_id, tool, parameters)
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, headers=headers, json={"input": payload})
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "COMPLETED":
                        output = result.get("output", {})
                        # Extract relevant fields based on service
                        return self._extract_service_response(service_id, tool, output)
                    else:
                        return {"error": f"Job failed: {result}"}
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
                    
        except Exception as e:
            return {"error": f"Service call failed: {str(e)}"}
    
    def _prepare_service_payload(self, service_id: str, tool: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare payload for specific service"""
        
        if service_id == "whisper":
            if tool == "transcribe_audio":
                return {
                    "audio": parameters.get("audio_url"),
                    "language": parameters.get("language"),
                    "return_segments": parameters.get("return_segments", False),
                    "vad_filter": parameters.get("vad_filter", True)
                }
            elif tool == "transcribe_medical_dictation":
                return {
                    "audio": parameters.get("audio_url"),
                    "return_segments": True,
                    "vad_filter": True,
                    "language": "en"
                }
                
        elif service_id == "phi4":
            if tool == "generate_soap_note":
                return {
                    "text": parameters.get("text"),
                    "prompt_type": "soap",
                    "max_tokens": 2048,
                    "temperature": 0.7
                }
            elif tool == "create_clinical_summary":
                max_words = parameters.get("max_words", 500)
                max_tokens = min(int(max_words * 1.3), 8192)
                return {
                    "text": parameters.get("text"),
                    "prompt_type": "summary",
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
                
        return parameters
    
    def _extract_service_response(self, service_id: str, tool: str, output: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant fields from service response"""
        
        if service_id == "whisper":
            return {
                "transcription": output.get("transcription", ""),
                "language": output.get("language", "unknown"),
                "duration": output.get("duration", 0),
                "processing_time": output.get("processing_time", 0),
                "segments": output.get("segments") if tool == "transcribe_medical_dictation" else None
            }
            
        elif service_id == "phi4":
            # Handle both direct text and insights field
            text_output = output.get("insights") or output.get("text", "")
            
            if tool == "generate_soap_note":
                # Parse tags if present
                import re
                solution_match = re.search(r'<solution>(.*?)</solution>', text_output, re.DOTALL)
                soap_note = solution_match.group(1).strip() if solution_match else text_output
                
                return {
                    "soap_note": soap_note,
                    "processing_time": output.get("processing_time", 0)
                }
            else:
                return {
                    "result": text_output,
                    "processing_time": output.get("processing_time", 0)
                }
                
        return output
    
    async def process_medical_dictation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Process medical dictation through multiple services"""
        try:
            audio_url = args["audio_url"]
            desired_outputs = args.get("outputs", ["transcription", "soap_note"])
            metadata = args.get("metadata", {})
            
            # Plan workflow
            workflow = self.planner.plan_workflow(
                inputs={"audio_url": audio_url},
                required_outputs=desired_outputs
            )
            
            # Execute workflow
            results = {}
            context = {"audio_url": audio_url}
            
            for step in workflow:
                service_id = step["service"]
                
                # Determine which tool to call based on capability
                if step["capability"] == "transcription":
                    tool = "transcribe_audio"
                    params = {"audio_url": context["audio_url"]}
                elif step["capability"] == "soap_generation":
                    tool = "generate_soap_note"
                    params = {"text": context["transcription"]}
                elif step["capability"] == "clinical_summary":
                    tool = "create_clinical_summary"
                    params = {"text": context["transcription"]}
                else:
                    continue
                
                # Call service
                step_result = await self.call_service(service_id, tool, params)
                
                # Update context with results
                for output in step["outputs"]:
                    if output in step_result:
                        context[output] = step_result[output]
                        results[output] = step_result[output]
            
            return {
                "status": "completed",
                "workflow_steps": len(workflow),
                "results": results,
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    async def analyze_patient_encounter(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patient encounter with available services"""
        try:
            encounter_data = args["encounter_data"]
            analysis_goals = args.get("analysis_goals", ["diagnosis", "treatment_plan"])
            
            # Determine what services we need based on data and goals
            results = {}
            
            # If we have text data, use Phi-4 for analysis
            if "clinical_notes" in encounter_data or "transcription" in encounter_data:
                text = encounter_data.get("clinical_notes") or encounter_data.get("transcription")
                
                # Get medical insights
                insights_result = await self.call_service(
                    "phi4",
                    "extract_medical_insights",
                    {"text": text, "insight_types": ["symptoms", "diagnoses", "medications"]}
                )
                results["medical_insights"] = insights_result
                
                # Generate clinical summary if requested
                if "summary" in analysis_goals:
                    summary_result = await self.call_service(
                        "phi4",
                        "create_clinical_summary",
                        {"text": text}
                    )
                    results["clinical_summary"] = summary_result
            
            return {
                "status": "completed",
                "analysis_goals": analysis_goals,
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    async def query_capabilities(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Query available service capabilities"""
        capability_filter = args.get("capability")
        
        if capability_filter:
            # Find services with specific capability
            try:
                cap_enum = ServiceCapability(capability_filter)
                services = self.registry.get_services_for_capability(cap_enum)
                return {
                    "capability": capability_filter,
                    "available_services": [
                        self.registry.get_service_info(s) for s in services
                    ]
                }
            except ValueError:
                return {"error": f"Unknown capability: {capability_filter}"}
        else:
            # Return all services and capabilities
            return {
                "services": self.registry.services,
                "capabilities": [cap.value for cap in ServiceCapability]
            }
    
    async def execute_custom_workflow(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a custom workflow"""
        try:
            inputs = args["inputs"]
            workflow_steps = args["workflow_steps"]
            
            context = inputs.copy()
            results = []
            
            for i, step in enumerate(workflow_steps):
                service_id = step["service"]
                tool = step["tool"]
                
                # Resolve parameters from context
                params = {}
                for key, value in step.get("parameters", {}).items():
                    if isinstance(value, str) and value.startswith("$"):
                        # Reference to context variable
                        context_key = value[1:]
                        params[key] = context.get(context_key)
                    else:
                        params[key] = value
                
                # Call service
                step_result = await self.call_service(service_id, tool, params)
                
                # Store result
                results.append({
                    "step": i + 1,
                    "service": service_id,
                    "tool": tool,
                    "result": step_result
                })
                
                # Update context
                context[f"step_{i+1}_result"] = step_result
            
            return {
                "status": "completed",
                "workflow_steps": len(workflow_steps),
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

def main():
    """Main entry point"""
    orchestrator = IASOOrchestrator()
    asyncio.run(orchestrator.run())

if __name__ == "__main__":
    main()