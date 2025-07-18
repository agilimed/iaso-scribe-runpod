#!/usr/bin/env python3
"""
Phi-4 Medical Reasoning MCP Server
Exposes Phi-4 medical AI capabilities via Model Context Protocol
"""

import asyncio
import json
import os
import re
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel

# RunPod configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
PHI4_ENDPOINT_ID = os.getenv("PHI4_ENDPOINT_ID", "tmmwa4q8ax5sg4")
RUNPOD_API_URL = f"https://api.runpod.ai/v2/{PHI4_ENDPOINT_ID}"

class Phi4MCPServer:
    """MCP Server for Phi-4 medical reasoning service"""
    
    def __init__(self):
        self.server = Server("phi4-medical-reasoning")
        self.setup_tools()
    
    def parse_response_tags(self, response: str) -> Dict[str, str]:
        """Parse <think> and <solution> tags from response"""
        think_match = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
        solution_match = re.search(r'<solution>(.*?)</solution>', response, re.DOTALL)
        
        return {
            "reasoning": think_match.group(1).strip() if think_match else "",
            "solution": solution_match.group(1).strip() if solution_match else response,
            "has_structured_output": bool(think_match and solution_match)
        }
    
    def setup_tools(self):
        """Register available tools"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="generate_soap_note",
                    description="Generate a SOAP note from medical transcription or clinical notes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Medical transcription or clinical notes"
                            },
                            "include_reasoning": {
                                "type": "boolean",
                                "description": "Include step-by-step clinical reasoning",
                                "default": False
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="create_clinical_summary",
                    description="Create a comprehensive clinical summary from medical documentation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Medical documentation to summarize"
                            },
                            "max_words": {
                                "type": "integer",
                                "description": "Maximum words for summary (e.g., 750)",
                                "default": None
                            },
                            "focus_areas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific areas to focus on",
                                "default": []
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="extract_medical_insights",
                    description="Extract key medical insights and clinical findings",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Medical text to analyze"
                            },
                            "insight_types": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["symptoms", "medications", "diagnoses", "procedures", "lab_results", "risk_factors"]
                                },
                                "description": "Types of insights to extract"
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="analyze_clinical_case",
                    description="Provide comprehensive analysis of a clinical case",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "case_text": {
                                "type": "string",
                                "description": "Clinical case description"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["differential_diagnosis", "treatment_plan", "risk_assessment", "full_analysis"],
                                "default": "full_analysis"
                            }
                        },
                        "required": ["case_text"]
                    }
                ),
                Tool(
                    name="generate_medical_report",
                    description="Generate a structured medical report from clinical data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "clinical_data": {
                                "type": "string",
                                "description": "Clinical data to include in report"
                            },
                            "report_type": {
                                "type": "string",
                                "enum": ["consultation", "discharge", "progress", "procedure"],
                                "default": "consultation"
                            },
                            "specialty": {
                                "type": "string",
                                "description": "Medical specialty context"
                            }
                        },
                        "required": ["clinical_data"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if name == "generate_soap_note":
                result = await self.generate_soap_note(arguments)
            elif name == "create_clinical_summary":
                result = await self.create_clinical_summary(arguments)
            elif name == "extract_medical_insights":
                result = await self.extract_medical_insights(arguments)
            elif name == "analyze_clinical_case":
                result = await self.analyze_clinical_case(arguments)
            elif name == "generate_medical_report":
                result = await self.generate_medical_report(arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
    
    async def call_runpod_endpoint(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call RunPod Phi-4 endpoint"""
        headers = {
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{RUNPOD_API_URL}/runsync",
                headers=headers,
                json={"input": payload}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "COMPLETED":
                    return result["output"]
                elif result.get("status") in ["IN_QUEUE", "IN_PROGRESS"]:
                    # Poll for completion
                    job_id = result.get("id")
                    return await self.poll_job_status(client, job_id, headers)
                else:
                    return {"error": f"Job failed: {result}"}
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
    
    async def poll_job_status(self, client: httpx.AsyncClient, job_id: str, headers: Dict) -> Dict[str, Any]:
        """Poll job status until completion"""
        max_attempts = 60
        for _ in range(max_attempts):
            await asyncio.sleep(2)
            
            response = await client.get(
                f"{RUNPOD_API_URL}/status/{job_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "COMPLETED":
                    return result["output"]
                elif result.get("status") == "FAILED":
                    return {"error": f"Job failed: {result}"}
        
        return {"error": "Job timed out"}
    
    async def generate_soap_note(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SOAP note from medical text"""
        try:
            payload = {
                "text": args["text"],
                "prompt_type": "soap",
                "max_tokens": 2048,
                "temperature": 0.7
            }
            
            result = await self.call_runpod_endpoint(payload)
            
            if "error" in result:
                return result
            
            # Parse structured response
            parsed = self.parse_response_tags(result.get("insights", ""))
            
            response = {
                "soap_note": parsed["solution"],
                "clinical_reasoning": parsed["reasoning"] if args.get("include_reasoning") else None,
                "structured_output": parsed["has_structured_output"],
                "processing_time": result.get("processing_time", 0),
                "model": "phi-4-reasoning-plus",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Remove None values
            return {k: v for k, v in response.items() if v is not None}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def create_clinical_summary(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create clinical summary"""
        try:
            # Adjust max_tokens based on requested word count
            max_tokens = 4096
            if args.get("max_words"):
                # Rough estimate: 1.3 tokens per word
                max_tokens = min(int(args["max_words"] * 1.3), 8192)
            
            payload = {
                "text": args["text"],
                "prompt_type": "summary",
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            result = await self.call_runpod_endpoint(payload)
            
            if "error" in result:
                return result
            
            # Parse structured response
            parsed = self.parse_response_tags(result.get("insights", ""))
            summary = parsed["solution"]
            
            # Count words
            word_count = len(summary.split())
            
            return {
                "summary": summary,
                "word_count": word_count,
                "clinical_reasoning": parsed["reasoning"] if parsed["has_structured_output"] else None,
                "focus_areas": args.get("focus_areas", []),
                "processing_time": result.get("processing_time", 0),
                "model": "phi-4-reasoning-plus",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def extract_medical_insights(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Extract medical insights"""
        try:
            payload = {
                "text": args["text"],
                "prompt_type": "medical_insights",
                "max_tokens": 2048,
                "temperature": 0.7
            }
            
            result = await self.call_runpod_endpoint(payload)
            
            if "error" in result:
                return result
            
            # Parse structured response
            parsed = self.parse_response_tags(result.get("insights", ""))
            
            # Structure the insights
            insights_text = parsed["solution"]
            
            return {
                "insights": insights_text,
                "requested_types": args.get("insight_types", []),
                "clinical_reasoning": parsed["reasoning"] if parsed["has_structured_output"] else None,
                "processing_time": result.get("processing_time", 0),
                "model": "phi-4-reasoning-plus",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def analyze_clinical_case(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze clinical case"""
        try:
            # Build custom prompt based on analysis type
            analysis_prompts = {
                "differential_diagnosis": "Focus on differential diagnoses and diagnostic reasoning",
                "treatment_plan": "Focus on treatment options and management plan",
                "risk_assessment": "Focus on risk factors and prognostic considerations",
                "full_analysis": "Provide comprehensive analysis including diagnosis, treatment, and prognosis"
            }
            
            custom_text = f"{args['case_text']}\n\nAnalysis focus: {analysis_prompts.get(args.get('analysis_type', 'full_analysis'))}"
            
            payload = {
                "text": custom_text,
                "prompt_type": "medical_insights",
                "max_tokens": 3072,
                "temperature": 0.7
            }
            
            result = await self.call_runpod_endpoint(payload)
            
            if "error" in result:
                return result
            
            # Parse structured response
            parsed = self.parse_response_tags(result.get("insights", ""))
            
            return {
                "analysis": parsed["solution"],
                "analysis_type": args.get("analysis_type", "full_analysis"),
                "clinical_reasoning": parsed["reasoning"] if parsed["has_structured_output"] else None,
                "processing_time": result.get("processing_time", 0),
                "model": "phi-4-reasoning-plus",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def generate_medical_report(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate medical report"""
        try:
            # Customize prompt based on report type
            report_context = f"Generate a {args.get('report_type', 'consultation')} report"
            if args.get('specialty'):
                report_context += f" for {args['specialty']}"
            
            custom_text = f"{report_context}:\n\n{args['clinical_data']}"
            
            payload = {
                "text": custom_text,
                "prompt_type": "summary",
                "max_tokens": 4096,
                "temperature": 0.7
            }
            
            result = await self.call_runpod_endpoint(payload)
            
            if "error" in result:
                return result
            
            # Parse structured response
            parsed = self.parse_response_tags(result.get("insights", ""))
            
            return {
                "report": parsed["solution"],
                "report_type": args.get("report_type", "consultation"),
                "specialty": args.get("specialty"),
                "clinical_reasoning": parsed["reasoning"] if parsed["has_structured_output"] else None,
                "processing_time": result.get("processing_time", 0),
                "model": "phi-4-reasoning-plus",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
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
    server = Phi4MCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()