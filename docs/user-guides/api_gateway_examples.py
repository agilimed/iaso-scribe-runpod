#!/usr/bin/env python3
"""
Example usage of the NexusCare AI Gateway
Demonstrates all processing modes and capabilities
"""

import asyncio
import httpx
import json
from typing import Dict, List
import websockets

# Configuration
API_BASE_URL = "http://localhost:8080"
WS_URL = "ws://localhost:8080/ws"

# Example JWT token (in production, get from auth service)
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

class NexusCareAPIClient:
    """Client for interacting with NexusCare AI Gateway"""
    
    def __init__(self, base_url: str = API_BASE_URL, token: str = AUTH_TOKEN):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    # Example 1: Clinical Only Mode
    async def extract_clinical_entities(self, text: str) -> Dict:
        """Extract medical entities from text"""
        print(f"\n=== Clinical Entity Extraction ===")
        print(f"Input: {text}")
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/chat",
            json={
                "message": text,
                "context": {"mode_hint": "clinical"}
            },
            headers=self.headers
        )
        
        result = response.json()
        print(f"Entities found: {json.dumps(result.get('response', {}).get('entities', []), indent=2)}")
        return result
    
    # Example 2: SQL Generation Only
    async def generate_sql(self, query: str) -> Dict:
        """Generate SQL from natural language"""
        print(f"\n=== SQL Generation ===")
        print(f"Query: {query}")
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/chat",
            json={
                "message": query,
                "context": {"mode_hint": "sql"}
            },
            headers=self.headers
        )
        
        result = response.json()
        sql = result.get('response', {}).get('sql', '')
        print(f"Generated SQL:\n{sql}")
        return result
    
    # Example 3: Clinical to SQL Mode
    async def clinical_informed_sql(self, query: str) -> Dict:
        """Generate SQL with clinical context"""
        print(f"\n=== Clinical-Informed SQL Generation ===")
        print(f"Query: {query}")
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/process",
            json={
                "text": query,
                "mode": "clinical_to_sql",
                "include_explanations": True
            },
            headers=self.headers
        )
        
        result = response.json()
        print(f"Clinical Entities: {result.get('clinical_entities', [])}")
        print(f"Generated SQL: {result.get('generated_sql', '')}")
        return result
    
    # Example 4: RAG-Enhanced Query
    async def rag_enhanced_query(self, query: str, collection: str = "medical_knowledge") -> Dict:
        """Query with RAG enhancement"""
        print(f"\n=== RAG-Enhanced Query ===")
        print(f"Query: {query}")
        print(f"Collection: {collection}")
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/process",
            json={
                "text": query,
                "mode": "rag_clinical",
                "enable_rag": True,
                "rag_collection": collection,
                "rag_top_k": 5
            },
            headers=self.headers
        )
        
        result = response.json()
        print(f"RAG Sources: {len(result.get('rag_sources', []))}")
        print(f"Enhanced Response: {json.dumps(result.get('clinical_summary'), indent=2)}")
        return result
    
    # Example 5: Full Pipeline
    async def full_pipeline_query(self, query: str) -> Dict:
        """Process query through full pipeline"""
        print(f"\n=== Full Pipeline Processing ===")
        print(f"Query: {query}")
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/process",
            json={
                "text": query,
                "mode": "full_pipeline",
                "enable_rag": True,
                "enable_medcat": True,
                "enable_sql_generation": True,
                "return_embeddings": True
            },
            headers=self.headers
        )
        
        result = response.json()
        print(f"Processing Time: {result.get('processing_time_ms')}ms")
        print(f"Services Used: Clinical={bool(result.get('clinical_entities'))}, "
              f"SQL={bool(result.get('generated_sql'))}, "
              f"RAG={bool(result.get('rag_context'))}")
        return result
    
    # Example 6: Create Agent
    async def create_medical_research_agent(self, research_query: str) -> Dict:
        """Create an autonomous research agent"""
        print(f"\n=== Creating Medical Research Agent ===")
        print(f"Research Topic: {research_query}")
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/agents",
            json={
                "task_type": "medical_research",
                "parameters": {
                    "query": research_query,
                    "max_sources": 10,
                    "include_clinical_trials": True
                }
            },
            headers=self.headers
        )
        
        result = response.json()
        print(f"Agent ID: {result.get('agent_id')}")
        print(f"Task ID: {result.get('task_id')}")
        return result

# WebSocket examples
class NexusCareWebSocketClient:
    """WebSocket client for real-time interactions"""
    
    def __init__(self, client_id: str = "demo-client"):
        self.client_id = client_id
        self.uri = f"{WS_URL}/{client_id}"
    
    async def chat_session(self):
        """Interactive chat session example"""
        print(f"\n=== WebSocket Chat Session ===")
        
        async with websockets.connect(self.uri) as websocket:
            # Receive welcome message
            welcome = json.loads(await websocket.recv())
            print(f"Connected! Session ID: {welcome.get('session_id')}")
            
            # Example conversation
            messages = [
                "What are the symptoms of diabetes?",
                "How is it diagnosed?",
                "Show me patients with diabetes and HbA1c > 7"
            ]
            
            for message in messages:
                print(f"\nUser: {message}")
                
                # Send message
                await websocket.send(json.dumps({
                    "type": "message",
                    "text": message
                }))
                
                # Receive response
                response = json.loads(await websocket.recv())
                print(f"Assistant: {json.dumps(response.get('data'), indent=2)}")
                
                await asyncio.sleep(1)  # Pause between messages

# Batch processing example
async def batch_process_example(client: NexusCareAPIClient):
    """Example of batch processing multiple items"""
    print(f"\n=== Batch Processing Example ===")
    
    clinical_notes = [
        "Patient presents with polyuria, polydipsia, and weight loss",
        "65-year-old male with hypertension and type 2 diabetes",
        "Recent lab results show HbA1c of 8.5%, fasting glucose 180 mg/dL"
    ]
    
    response = await client.client.post(
        f"{client.base_url}/api/v1/batch",
        json={
            "items": [{"text": note} for note in clinical_notes],
            "processing_type": "clinical_extraction",
            "parallel": True
        },
        headers=client.headers
    )
    
    results = response.json()
    print(f"Processed {results.get('processed')} items")

# Example queries for different scenarios
EXAMPLE_QUERIES = {
    "clinical_extraction": [
        "Patient has diabetes mellitus type 2 with peripheral neuropathy",
        "55-year-old female presents with chest pain and shortness of breath",
        "Recent diagnosis of hypertension, started on lisinopril 10mg daily"
    ],
    
    "sql_generation": [
        "Show all patients with diabetes",
        "Find patients with HbA1c greater than 7 in the last 6 months",
        "List medications prescribed for hypertension"
    ],
    
    "complex_queries": [
        "Which diabetic patients have poor glucose control and missed their last appointment?",
        "Find patients with multiple chronic conditions who might benefit from care coordination",
        "Show medication adherence rates for patients with both diabetes and hypertension"
    ],
    
    "research_queries": [
        "What are the latest treatment guidelines for type 2 diabetes?",
        "Compare effectiveness of different hypertension medications",
        "Review clinical outcomes for patients on SGLT2 inhibitors"
    ]
}

async def run_comprehensive_examples():
    """Run all examples to demonstrate capabilities"""
    client = NexusCareAPIClient()
    
    try:
        # 1. Clinical entity extraction
        await client.extract_clinical_entities(
            EXAMPLE_QUERIES["clinical_extraction"][0]
        )
        
        # 2. SQL generation
        await client.generate_sql(
            EXAMPLE_QUERIES["sql_generation"][1]
        )
        
        # 3. Clinical-informed SQL
        await client.clinical_informed_sql(
            EXAMPLE_QUERIES["complex_queries"][0]
        )
        
        # 4. RAG-enhanced query
        await client.rag_enhanced_query(
            EXAMPLE_QUERIES["research_queries"][0]
        )
        
        # 5. Full pipeline
        await client.full_pipeline_query(
            EXAMPLE_QUERIES["complex_queries"][1]
        )
        
        # 6. Create research agent
        await client.create_medical_research_agent(
            EXAMPLE_QUERIES["research_queries"][1]
        )
        
        # 7. Batch processing
        await batch_process_example(client)
        
    finally:
        await client.close()
    
    # 8. WebSocket chat
    ws_client = NexusCareWebSocketClient()
    await ws_client.chat_session()

# Performance testing example
async def performance_test():
    """Test gateway performance with concurrent requests"""
    print(f"\n=== Performance Test ===")
    
    client = NexusCareAPIClient()
    
    async def timed_request(query: str, mode: str):
        start = asyncio.get_event_loop().time()
        await client.client.post(
            f"{client.base_url}/api/v1/process",
            json={"text": query, "mode": mode},
            headers=client.headers
        )
        return asyncio.get_event_loop().time() - start
    
    # Run concurrent requests
    queries = EXAMPLE_QUERIES["sql_generation"][:3]
    tasks = []
    
    for query in queries:
        for mode in ["clinical_only", "insights_only", "full_pipeline"]:
            tasks.append(timed_request(query, mode))
    
    times = await asyncio.gather(*tasks)
    
    print(f"Completed {len(tasks)} requests")
    print(f"Average time: {sum(times)/len(times):.2f}s")
    print(f"Min time: {min(times):.2f}s")
    print(f"Max time: {max(times):.2f}s")
    
    await client.close()

if __name__ == "__main__":
    print("NexusCare AI Gateway Examples")
    print("=============================")
    
    # Run all examples
    asyncio.run(run_comprehensive_examples())
    
    # Run performance test
    # asyncio.run(performance_test())