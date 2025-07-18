#!/usr/bin/env python3
"""
Test script for IASOQL RunPod deployment
"""

import httpx
import asyncio
import json
import os
from datetime import datetime

# Configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
IASOQL_ENDPOINT_ID = os.getenv("IASOQL_ENDPOINT_ID")

if not RUNPOD_API_KEY:
    print("❌ Please set RUNPOD_API_KEY environment variable")
    exit(1)

if not IASOQL_ENDPOINT_ID:
    print("❌ Please set IASOQL_ENDPOINT_ID environment variable")
    print("After deploying to RunPod, get the endpoint ID from the console")
    exit(1)

# Test queries
TEST_QUERIES = [
    {
        "name": "Count patients with diabetes",
        "query": "How many patients have diabetes?",
        "expected_keywords": ["COUNT", "Condition", "diabetes", "E11"]
    },
    {
        "name": "Recent lab results",
        "query": "Show recent lab results for patient 123 with high values",
        "expected_keywords": ["Observation", "Patient/123", "interpretation", "high"]
    },
    {
        "name": "Active medications",
        "query": "List all active medications for patients with hypertension",
        "expected_keywords": ["MedicationRequest", "active", "hypertension"]
    },
    {
        "name": "Appointments this week",
        "query": "Find all appointments scheduled for this week",
        "expected_keywords": ["Appointment", "start", "now()", "INTERVAL"]
    },
    {
        "name": "Complex aggregation",
        "query": "What is the average HbA1c value for diabetic patients in the last 3 months?",
        "expected_keywords": ["AVG", "Observation", "HbA1c", "diabetes", "3 MONTH"]
    }
]

async def test_iasoql_endpoint():
    """Test IASOQL endpoint with various queries"""
    
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
    
    print("🧪 Testing IASOQL Endpoint")
    print(f"Endpoint ID: {IASOQL_ENDPOINT_ID}")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for test in TEST_QUERIES:
            print(f"\n📝 Test: {test['name']}")
            print(f"Query: {test['query']}")
            
            payload = {
                "input": {
                    "query": test["query"],
                    "schema_context": schema_context,
                    "tenant_id": "demo_tenant"
                }
            }
            
            try:
                start_time = datetime.now()
                response = await client.post(url, headers=headers, json=payload)
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds()
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("status") == "COMPLETED":
                        output = result.get("output", {})
                        sql = output.get("sql", "")
                        source = output.get("source", "unknown")
                        
                        print(f"✅ Success! (Duration: {duration:.2f}s)")
                        print(f"Source: {source}")
                        print(f"Generated SQL:")
                        print("-" * 40)
                        print(sql)
                        print("-" * 40)
                        
                        # Check for expected keywords
                        sql_upper = sql.upper()
                        missing_keywords = []
                        for keyword in test["expected_keywords"]:
                            if keyword.upper() not in sql_upper:
                                missing_keywords.append(keyword)
                        
                        if missing_keywords:
                            print(f"⚠️  Warning: Expected keywords not found: {missing_keywords}")
                        else:
                            print("✅ All expected keywords found")
                        
                    else:
                        print(f"❌ Job failed: {result.get('status')}")
                        print(f"Error: {result.get('error', 'Unknown error')}")
                        
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 80)
    print("✅ Testing complete!")

async def test_template_matching():
    """Test template matching functionality"""
    
    print("\n🔍 Testing Template Matching")
    print("=" * 80)
    
    url = f"https://api.runpod.ai/v2/{IASOQL_ENDPOINT_ID}/runsync"
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Queries that should match templates
    template_queries = [
        "count patients with asthma",
        "recent lab results for patient 456",
        "active medications for patient 789",
        "upcoming appointments",
        "recent vitals for patient 321"
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for query in template_queries:
            print(f"\nQuery: {query}")
            
            payload = {
                "input": {
                    "query": query,
                    "tenant_id": "demo_tenant"
                }
            }
            
            try:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    output = result.get("output", {})
                    source = output.get("source", "unknown")
                    
                    if source == "template":
                        print(f"✅ Matched template!")
                    else:
                        print(f"📊 Used LLM generation")
                        
            except Exception as e:
                print(f"❌ Error: {str(e)}")

# Run tests
if __name__ == "__main__":
    asyncio.run(test_iasoql_endpoint())
    asyncio.run(test_template_matching())