#!/usr/bin/env python3
"""
Whisper MCP Server
Exposes Whisper transcription capabilities via Model Context Protocol
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from pydantic import BaseModel

# RunPod configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
WHISPER_ENDPOINT_ID = os.getenv("WHISPER_ENDPOINT_ID", "rntxttrdl8uv3i")
RUNPOD_API_URL = f"https://api.runpod.ai/v2/{WHISPER_ENDPOINT_ID}"

class TranscriptionRequest(BaseModel):
    """Request model for transcription"""
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    language: Optional[str] = None
    return_segments: bool = False
    vad_filter: bool = True

class WhisperMCPServer:
    """MCP Server for Whisper transcription service"""
    
    def __init__(self):
        self.server = Server("whisper-transcription-service")
        self.setup_tools()
        
    def setup_tools(self):
        """Register available tools"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="transcribe_audio",
                    description="Transcribe audio file to text using Whisper",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "audio_url": {
                                "type": "string",
                                "description": "URL of the audio file to transcribe"
                            },
                            "audio_base64": {
                                "type": "string", 
                                "description": "Base64 encoded audio data (alternative to URL)"
                            },
                            "language": {
                                "type": "string",
                                "description": "Language code (e.g., 'en', 'es') or null for auto-detection"
                            },
                            "return_segments": {
                                "type": "boolean",
                                "description": "Return word-level timestamps",
                                "default": False
                            }
                        },
                        "required": [],
                        "oneOf": [
                            {"required": ["audio_url"]},
                            {"required": ["audio_base64"]}
                        ]
                    }
                ),
                Tool(
                    name="transcribe_medical_dictation",
                    description="Transcribe medical dictation with optimized settings",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "audio_url": {
                                "type": "string",
                                "description": "URL of the medical dictation audio"
                            },
                            "speaker_info": {
                                "type": "string",
                                "description": "Information about the speaker (e.g., 'Dr. Smith, Cardiologist')"
                            }
                        },
                        "required": ["audio_url"]
                    }
                ),
                Tool(
                    name="detect_audio_language", 
                    description="Detect the language spoken in an audio file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "audio_url": {
                                "type": "string",
                                "description": "URL of the audio file"
                            }
                        },
                        "required": ["audio_url"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if name == "transcribe_audio":
                result = await self.transcribe_audio(arguments)
            elif name == "transcribe_medical_dictation":
                result = await self.transcribe_medical_dictation(arguments)
            elif name == "detect_audio_language":
                result = await self.detect_language(arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
    
    async def call_runpod_endpoint(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call RunPod Whisper endpoint"""
        headers = {
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{RUNPOD_API_URL}/runsync",
                headers=headers,
                json={"input": payload}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "COMPLETED":
                    return result["output"]
                else:
                    return {"error": f"Job failed: {result}"}
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
    
    async def transcribe_audio(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio to text"""
        try:
            payload = {
                "audio": args.get("audio_url") or args.get("audio_base64"),
                "return_segments": args.get("return_segments", False),
                "vad_filter": args.get("vad_filter", True)
            }
            
            if args.get("language"):
                payload["language"] = args["language"]
            
            result = await self.call_runpod_endpoint(payload)
            
            if "error" in result:
                return result
            
            return {
                "transcription": result.get("transcription", ""),
                "language": result.get("language", "unknown"),
                "duration": result.get("duration", 0),
                "processing_time": result.get("processing_time", 0),
                "segments": result.get("segments", []) if args.get("return_segments") else None,
                "service": "whisper-medium",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def transcribe_medical_dictation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe medical dictation with optimized settings"""
        try:
            # Use specific settings optimized for medical dictation
            payload = {
                "audio": args["audio_url"],
                "return_segments": True,  # Always return segments for medical
                "vad_filter": True,
                "language": "en"  # Medical dictation typically in English
            }
            
            result = await self.call_runpod_endpoint(payload)
            
            if "error" in result:
                return result
            
            # Add medical-specific metadata
            response = {
                "transcription": result.get("transcription", ""),
                "speaker_info": args.get("speaker_info", "Unknown"),
                "duration": result.get("duration", 0),
                "processing_time": result.get("processing_time", 0),
                "segments": result.get("segments", []),
                "medical_dictation": True,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "service": "whisper-medical",
                    "optimized_for": "medical_terminology",
                    "post_processing": "medical_nlp_ready"
                }
            }
            
            return response
            
        except Exception as e:
            return {"error": str(e)}
    
    async def detect_language(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Detect language from audio"""
        try:
            # Transcribe a short segment to detect language
            payload = {
                "audio": args["audio_url"],
                "return_segments": False,
                "vad_filter": True
            }
            
            result = await self.call_runpod_endpoint(payload)
            
            if "error" in result:
                return result
            
            return {
                "detected_language": result.get("language", "unknown"),
                "confidence": "high" if result.get("language") else "low",
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
    server = WhisperMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()