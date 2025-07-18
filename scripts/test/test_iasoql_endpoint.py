#!/usr/bin/env python3
"""
Test IASOQL RunPod endpoint with streaming support
"""

import httpx
import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
IASOQL_ENDPOINT_ID = os.getenv("IASOQL_ENDPOINT_ID")

if not RUNPOD_API_KEY:
    print("❌ Please set RUNPOD_API_KEY in .env file")
    exit(1)

if not IASOQL_ENDPOINT_ID:
    print("❌ Please set IASOQL_ENDPOINT_ID in .env file")
    exit(1)

# Test queries
TEST_QUERIES = [
    {
        "name": "Complex healthcare query",
        "query": "Show me Male patient who smoke and have a history of heart disease and have an appointment booked in next 12 weeks",
    },
    {
        "name": "Simple patient count",
        "query": "How many patients are in the system?",
    },
    {
        "name": "Diabetes patient count",
        "query": "How many patients have been diagnosed with diabetes?",
    },
    {
        "name": "Recent lab results",
        "query": "Show me the most recent lab results for patient ID 123",
    },
    {
        "name": "Active medications",
        "query": "List all active medications for patients over 65 years old",
    },
    {
        "name": "Complex aggregation",
        "query": "What is the average HbA1c value for diabetic patients in the last 3 months?",
    }
]

async def test_health_endpoint():
    """Test the health endpoint"""
    url = f"https://api.runpod.ai/v2/{IASOQL_ENDPOINT_ID}/health"
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
    }
    
    print("🏥 Testing health endpoint...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            print(f"Health check status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Endpoint is healthy!")
                return True
            else:
                print(f"❌ Health check failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error checking health: {e}")
            return False

async def test_iasoql_sync(query: str, name: str):
    """Test IASOQL endpoint with synchronous request"""
    url = f"https://api.runpod.ai/v2/{IASOQL_ENDPOINT_ID}/runsync"
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    schema_context = """
Database: nexuscare_analytics
Table: fhir_current

Key columns:
- tenant_id: String
- resource_type: String (Patient, Observation, Condition, MedicationRequest, etc.)
- resource: JSON (full FHIR resource)
- sign: Int8 (1 = current, -1 = deleted)
- created_at: DateTime

Use ClickHouse JSON functions:
- JSONExtractString(resource, '$.path')
- JSONExtractFloat(resource, '$.path')
- JSONExtractBool(resource, '$.path')
"""
    
    payload = {
        "input": {
            "query": query,
            "schema_context": schema_context,
            "tenant_id": "demo_tenant"
        }
    }
    
    print(f"\n📝 Test: {name}")
    print(f"Query: {query}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            start_time = datetime.now()
            response = await client.post(url, headers=headers, json=payload)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "COMPLETED":
                    output = result.get("output", {})
                    
                    if output.get("status") == "success":
                        sql = output.get("sql", "")
                        metadata = output.get("metadata", {})
                        
                        print(f"✅ Success! (Duration: {duration:.2f}s)")
                        print(f"Model: {metadata.get('model', 'unknown')}")
                        print(f"Generated SQL:")
                        print("-" * 60)
                        print(sql)
                        print("-" * 60)
                    else:
                        print(f"❌ Generation failed: {output.get('error', 'Unknown error')}")
                else:
                    print(f"❌ Job failed: {result.get('status')}")
                    if result.get("error"):
                        print(f"Error: {result['error']}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

async def test_iasoql_stream(query: str, name: str):
    """Test IASOQL endpoint with streaming (if supported)"""
    # Note: IASOQL doesn't support streaming like Whisper/Phi-4
    # since SQL generation is typically a single response
    # But we'll check if RunPod adds streaming support in the future
    
    url = f"https://api.runpod.ai/v2/{IASOQL_ENDPOINT_ID}/run"
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "query": query,
            "tenant_id": "demo_tenant"
        }
    }
    
    print(f"\n🔄 Testing async/streaming for: {name}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Submit job
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get("id")
                
                if job_id:
                    print(f"Job ID: {job_id}")
                    
                    # Poll for status
                    status_url = f"https://api.runpod.ai/v2/{IASOQL_ENDPOINT_ID}/status/{job_id}"
                    
                    while True:
                        status_response = await client.get(status_url, headers=headers)
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get("status")
                            
                            print(f"Status: {status}")
                            
                            if status == "COMPLETED":
                                output = status_data.get("output", {})
                                if output.get("sql"):
                                    print("✅ SQL generated!")
                                break
                            elif status in ["FAILED", "CANCELLED"]:
                                print(f"❌ Job {status}")
                                break
                                
                        await asyncio.sleep(1)
                else:
                    print("❌ No job ID returned")
            else:
                print(f"❌ Failed to submit job: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error in streaming test: {e}")

async def main():
    """Run all tests"""
    print("🧪 Testing IASOQL RunPod Endpoint")
    print(f"Endpoint ID: {IASOQL_ENDPOINT_ID}")
    print("=" * 80)
    
    # Test health
    healthy = await test_health_endpoint()
    
    if not healthy:
        print("\n⚠️  Endpoint may not be ready. Waiting 30 seconds...")
        await asyncio.sleep(30)
        await test_health_endpoint()
    
    # Test synchronous queries
    print("\n" + "=" * 80)
    print("SYNCHRONOUS TESTS")
    print("=" * 80)
    
    for test in TEST_QUERIES:
        await test_iasoql_sync(test["query"], test["name"])
        await asyncio.sleep(2)  # Small delay between requests
    
    # Test streaming (if supported)
    print("\n" + "=" * 80)
    print("ASYNC/STREAMING TESTS")
    print("=" * 80)
    
    # Just test one query for streaming
    await test_iasoql_stream(TEST_QUERIES[0]["query"], TEST_QUERIES[0]["name"])
    
    print("\n" + "=" * 80)
    print("✅ Testing complete!")

if __name__ == "__main__":
    asyncio.run(main())