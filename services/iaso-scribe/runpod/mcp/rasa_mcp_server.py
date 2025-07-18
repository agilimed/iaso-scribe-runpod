#!/usr/bin/env python3
"""
RASA Medical Dialog MCP Server
Exposes RASA conversational AI capabilities via Model Context Protocol
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel

# RASA configuration
RASA_SERVER_URL = os.getenv("RASA_SERVER_URL", "http://localhost:5005")
RASA_ACTION_SERVER_URL = os.getenv("RASA_ACTION_SERVER_URL", "http://localhost:5055")

class ConversationRequest(BaseModel):
    """Request model for conversation interaction"""
    message: str
    sender_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
class ConversationContext(BaseModel):
    """Conversation context model"""
    patient_id: Optional[str] = None
    conversation_type: Optional[str] = None  # symptom_check, appointment, medication, etc.
    clinical_context: Optional[Dict[str, Any]] = None

class RASAMCPServer:
    """MCP Server for RASA medical dialog management"""
    
    def __init__(self):
        self.server = Server("rasa-medical-dialog")
        self.setup_tools()
        self.sessions = {}  # Track conversation sessions
    
    def setup_tools(self):
        """Register available tools"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="send_message",
                    description="Send a message to RASA and get response",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "User message to process"
                            },
                            "sender_id": {
                                "type": "string",
                                "description": "Unique conversation/user ID"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional context (patient_id, phone_number, etc.)"
                            }
                        },
                        "required": ["message"]
                    }
                ),
                Tool(
                    name="start_conversation",
                    description="Start a new medical conversation session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "conversation_type": {
                                "type": "string",
                                "enum": ["symptom_check", "appointment", "medication", "prenatal", "general"],
                                "description": "Type of medical conversation"
                            },
                            "patient_id": {
                                "type": "string",
                                "description": "Patient identifier"
                            },
                            "initial_context": {
                                "type": "object",
                                "description": "Initial clinical context"
                            }
                        },
                        "required": ["conversation_type"]
                    }
                ),
                Tool(
                    name="get_conversation_state",
                    description="Get current conversation state and context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sender_id": {
                                "type": "string",
                                "description": "Conversation ID"
                            }
                        },
                        "required": ["sender_id"]
                    }
                ),
                Tool(
                    name="extract_medical_entities",
                    description="Extract medical entities from a conversation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to extract entities from"
                            },
                            "entity_types": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["symptom", "medication", "condition", "body_part", "severity"]
                                },
                                "description": "Types of entities to extract"
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="trigger_action",
                    description="Trigger a specific RASA custom action",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "action_assess_symptoms",
                                    "action_schedule_appointment",
                                    "action_check_drug_interactions",
                                    "action_medication_adherence_check",
                                    "action_prenatal_risk_assessment",
                                    "action_generate_soap_note"
                                ],
                                "description": "Action to trigger"
                            },
                            "sender_id": {
                                "type": "string",
                                "description": "Conversation ID"
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Additional parameters for the action"
                            }
                        },
                        "required": ["action", "sender_id"]
                    }
                ),
                Tool(
                    name="analyze_conversation",
                    description="Analyze a completed conversation for insights",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sender_id": {
                                "type": "string",
                                "description": "Conversation ID to analyze"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["summary", "entities", "intents", "sentiment", "clinical_notes"],
                                "default": "summary"
                            }
                        },
                        "required": ["sender_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if name == "send_message":
                result = await self.send_message(arguments)
            elif name == "start_conversation":
                result = await self.start_conversation(arguments)
            elif name == "get_conversation_state":
                result = await self.get_conversation_state(arguments)
            elif name == "extract_medical_entities":
                result = await self.extract_medical_entities(arguments)
            elif name == "trigger_action":
                result = await self.trigger_action(arguments)
            elif name == "analyze_conversation":
                result = await self.analyze_conversation(arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
    
    async def send_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to RASA and get response"""
        try:
            message = args["message"]
            sender_id = args.get("sender_id") or str(uuid.uuid4())
            metadata = args.get("metadata", {})
            
            # Prepare RASA request
            payload = {
                "sender": sender_id,
                "message": message,
                "metadata": metadata
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{RASA_SERVER_URL}/webhooks/rest/webhook",
                    json=payload
                )
                
                if response.status_code == 200:
                    bot_messages = response.json()
                    
                    # Track session
                    if sender_id not in self.sessions:
                        self.sessions[sender_id] = {
                            "started_at": datetime.utcnow().isoformat(),
                            "messages": []
                        }
                    
                    self.sessions[sender_id]["messages"].append({
                        "user": message,
                        "bot": bot_messages,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Extract relevant information
                    return {
                        "sender_id": sender_id,
                        "responses": bot_messages,
                        "session_active": True,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {"error": f"RASA error: {response.status_code}"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def start_conversation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new conversation session"""
        try:
            conversation_type = args["conversation_type"]
            patient_id = args.get("patient_id")
            initial_context = args.get("initial_context", {})
            
            # Generate session ID
            sender_id = str(uuid.uuid4())
            
            # Initialize session
            self.sessions[sender_id] = {
                "conversation_type": conversation_type,
                "patient_id": patient_id,
                "started_at": datetime.utcnow().isoformat(),
                "initial_context": initial_context,
                "messages": []
            }
            
            # Send initial message based on conversation type
            initial_messages = {
                "symptom_check": "I'd like to help you with your symptoms. Can you describe what you're experiencing?",
                "appointment": "I can help you schedule an appointment. What type of appointment do you need?",
                "medication": "I'm here to help with your medication questions. What would you like to know?",
                "prenatal": "Hello! I'm calling for your prenatal check-in. How are you feeling today?",
                "general": "Hello! How can I assist you with your healthcare needs today?"
            }
            
            initial_message = initial_messages.get(conversation_type, initial_messages["general"])
            
            # Send restart action to RASA to clear any previous state
            await self._restart_conversation(sender_id)
            
            # Send initial context as metadata
            response = await self.send_message({
                "message": "/start",  # RASA intent to start conversation
                "sender_id": sender_id,
                "metadata": {
                    "conversation_type": conversation_type,
                    "patient_id": patient_id,
                    **initial_context
                }
            })
            
            return {
                "sender_id": sender_id,
                "conversation_type": conversation_type,
                "status": "started",
                "initial_message": initial_message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_conversation_state(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get current conversation state"""
        try:
            sender_id = args["sender_id"]
            
            # Get tracker state from RASA
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{RASA_SERVER_URL}/conversations/{sender_id}/tracker"
                )
                
                if response.status_code == 200:
                    tracker = response.json()
                    
                    # Extract relevant state information
                    return {
                        "sender_id": sender_id,
                        "slots": tracker.get("slots", {}),
                        "latest_message": tracker.get("latest_message", {}),
                        "events": len(tracker.get("events", [])),
                        "active": tracker.get("active", False),
                        "latest_action": tracker.get("latest_action_name"),
                        "session_data": self.sessions.get(sender_id, {}),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {"error": f"Failed to get tracker: {response.status_code}"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def extract_medical_entities(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Extract medical entities using RASA NLU"""
        try:
            text = args["text"]
            entity_types = args.get("entity_types", [])
            
            # Parse message through RASA NLU
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{RASA_SERVER_URL}/model/parse",
                    json={"text": text}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Filter entities by type if specified
                    entities = result.get("entities", [])
                    if entity_types:
                        entities = [e for e in entities if e["entity"] in entity_types]
                    
                    # Group entities by type
                    grouped_entities = {}
                    for entity in entities:
                        entity_type = entity["entity"]
                        if entity_type not in grouped_entities:
                            grouped_entities[entity_type] = []
                        grouped_entities[entity_type].append({
                            "value": entity["value"],
                            "confidence": entity.get("confidence", 1.0),
                            "start": entity.get("start"),
                            "end": entity.get("end")
                        })
                    
                    return {
                        "text": text,
                        "intent": {
                            "name": result.get("intent", {}).get("name"),
                            "confidence": result.get("intent", {}).get("confidence")
                        },
                        "entities": grouped_entities,
                        "entity_count": len(entities),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {"error": f"NLU parsing failed: {response.status_code}"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def trigger_action(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a custom RASA action"""
        try:
            action = args["action"]
            sender_id = args["sender_id"]
            parameters = args.get("parameters", {})
            
            # Get current tracker state
            tracker_response = await self._get_tracker(sender_id)
            if "error" in tracker_response:
                return tracker_response
            
            # Trigger the action
            payload = {
                "name": action,
                "policy": "action_trigger",
                "confidence": 1.0,
                "parameters": parameters
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{RASA_SERVER_URL}/conversations/{sender_id}/execute",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Get updated tracker to see action results
                    updated_tracker = await self._get_tracker(sender_id)
                    
                    return {
                        "action": action,
                        "status": "executed",
                        "messages": result.get("messages", []),
                        "slots_changed": self._compare_slots(
                            tracker_response.get("slots", {}),
                            updated_tracker.get("slots", {})
                        ),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {"error": f"Action execution failed: {response.status_code}"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def analyze_conversation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a conversation for insights"""
        try:
            sender_id = args["sender_id"]
            analysis_type = args.get("analysis_type", "summary")
            
            # Get conversation history
            tracker = await self._get_tracker(sender_id)
            if "error" in tracker:
                return tracker
            
            events = tracker.get("events", [])
            
            if analysis_type == "summary":
                return self._analyze_summary(events, tracker)
            elif analysis_type == "entities":
                return self._analyze_entities(events)
            elif analysis_type == "intents":
                return self._analyze_intents(events)
            elif analysis_type == "sentiment":
                return self._analyze_sentiment(events)
            elif analysis_type == "clinical_notes":
                return await self._generate_clinical_notes(sender_id, events, tracker)
            else:
                return {"error": f"Unknown analysis type: {analysis_type}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    # Helper methods
    async def _restart_conversation(self, sender_id: str):
        """Restart conversation for a sender"""
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{RASA_SERVER_URL}/conversations/{sender_id}/tracker/events",
                json={"event": "restart"}
            )
    
    async def _get_tracker(self, sender_id: str) -> Dict[str, Any]:
        """Get tracker state for a conversation"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{RASA_SERVER_URL}/conversations/{sender_id}/tracker"
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Failed to get tracker: {response.status_code}"}
    
    def _compare_slots(self, old_slots: Dict, new_slots: Dict) -> Dict[str, Any]:
        """Compare slot values to find changes"""
        changes = {}
        for key, new_value in new_slots.items():
            old_value = old_slots.get(key)
            if old_value != new_value:
                changes[key] = {
                    "old": old_value,
                    "new": new_value
                }
        return changes
    
    def _analyze_summary(self, events: List[Dict], tracker: Dict) -> Dict[str, Any]:
        """Generate conversation summary"""
        user_messages = []
        bot_messages = []
        intents = []
        
        for event in events:
            if event.get("event") == "user":
                user_messages.append(event.get("text", ""))
                if event.get("parse_data", {}).get("intent"):
                    intents.append(event["parse_data"]["intent"]["name"])
            elif event.get("event") == "bot":
                bot_messages.append(event.get("text", ""))
        
        slots = tracker.get("slots", {})
        
        return {
            "conversation_summary": {
                "total_turns": len(user_messages),
                "user_messages": len(user_messages),
                "bot_messages": len(bot_messages),
                "unique_intents": list(set(intents)),
                "slots_filled": {k: v for k, v in slots.items() if v is not None},
                "latest_intent": intents[-1] if intents else None,
                "conversation_complete": tracker.get("active", True) is False
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _analyze_entities(self, events: List[Dict]) -> Dict[str, Any]:
        """Extract all entities from conversation"""
        all_entities = {}
        
        for event in events:
            if event.get("event") == "user" and event.get("parse_data"):
                entities = event["parse_data"].get("entities", [])
                for entity in entities:
                    entity_type = entity["entity"]
                    if entity_type not in all_entities:
                        all_entities[entity_type] = []
                    all_entities[entity_type].append(entity["value"])
        
        # Deduplicate
        for entity_type in all_entities:
            all_entities[entity_type] = list(set(all_entities[entity_type]))
        
        return {
            "entities_extracted": all_entities,
            "entity_types": list(all_entities.keys()),
            "total_entities": sum(len(v) for v in all_entities.values()),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _analyze_intents(self, events: List[Dict]) -> Dict[str, Any]:
        """Analyze intent patterns in conversation"""
        intent_sequence = []
        intent_confidence = []
        
        for event in events:
            if event.get("event") == "user" and event.get("parse_data"):
                intent = event["parse_data"].get("intent", {})
                if intent:
                    intent_sequence.append(intent["name"])
                    intent_confidence.append(intent.get("confidence", 0))
        
        avg_confidence = sum(intent_confidence) / len(intent_confidence) if intent_confidence else 0
        
        return {
            "intent_analysis": {
                "sequence": intent_sequence,
                "unique_intents": list(set(intent_sequence)),
                "average_confidence": round(avg_confidence, 3),
                "low_confidence_count": sum(1 for c in intent_confidence if c < 0.7),
                "intent_transitions": self._get_intent_transitions(intent_sequence)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_intent_transitions(self, intents: List[str]) -> List[Dict[str, str]]:
        """Get intent transition patterns"""
        transitions = []
        for i in range(len(intents) - 1):
            transitions.append({
                "from": intents[i],
                "to": intents[i + 1]
            })
        return transitions
    
    def _analyze_sentiment(self, events: List[Dict]) -> Dict[str, Any]:
        """Basic sentiment analysis (would integrate with sentiment service)"""
        # This is a placeholder - in production, integrate with a sentiment analysis service
        return {
            "sentiment_analysis": {
                "overall_sentiment": "neutral",
                "sentiment_progression": [],
                "negative_segments": [],
                "requires_escalation": False
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _generate_clinical_notes(self, sender_id: str, events: List[Dict], tracker: Dict) -> Dict[str, Any]:
        """Generate clinical notes from conversation"""
        # This would typically call the action server to generate SOAP notes
        try:
            result = await self.trigger_action({
                "action": "action_generate_soap_note",
                "sender_id": sender_id,
                "parameters": {}
            })
            
            return {
                "clinical_notes": {
                    "soap_note_generated": result.get("status") == "executed",
                    "notes": result.get("messages", []),
                    "slots": tracker.get("slots", {})
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to generate clinical notes: {str(e)}"}
    
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
    server = RASAMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()