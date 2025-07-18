#!/usr/bin/env python3
"""
Test IASOQL RunPod endpoint - following the working Phi-4 pattern
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def test_iasoql_query():
    """Test IASOQL with complex healthcare query"""
    
    # Complex healthcare query
    COMPLEX_QUERY = "Show me Male patient who smoke and have a history of heart disease and have an appointment booked in next 12 weeks"
    
    print("🏥 Testing IASOQL with Complex Healthcare Query")
    print("=" * 80)
    print(f"Query: {COMPLEX_QUERY}")
    print("-" * 80)
    
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    endpoint_id = os.environ.get('IASOQL_ENDPOINT_ID')
    
    if not endpoint_id:
        print("❌ IASOQL_ENDPOINT_ID not found in environment")
        return
    
    # Schema context for FHIR ClickHouse
    schema_context = """
Database: nexuscare_analytics
Table: fhir_current

Key columns:
- tenant_id: String
- resource_type: String (Patient, Observation, Condition, MedicationRequest, Appointment, etc.)
- resource: JSON (full FHIR resource)
- resource_id: String
- sign: Int8 (1 = current, -1 = deleted)
- created_at: DateTime

Key FHIR resource paths:
- Patient gender: JSONExtractString(resource, '$.gender')
- Patient birthDate: JSONExtractString(resource, '$.birthDate')
- Condition code: JSONExtractString(resource, '$.code.coding[0].display')
- Observation (smoking): JSONExtractString(resource, '$.valueCodeableConcept.coding[0].code')
- Appointment start: JSONExtractString(resource, '$.start')
- Appointment patient: JSONExtractString(resource, '$.participant[?(@.actor.reference)].actor.reference')

Common codes:
- Heart disease: ICD-10 codes I20-I25, SNOMED 53741008
- Smoking status: LOINC 72166-2, SNOMED 77176002 (smoker)
"""
    
    payload = {
        "input": {
            "query": COMPLEX_QUERY,
            "schema_context": schema_context,
            "tenant_id": "demo_tenant"
        }
    }
    
    print("📤 Sending request to IASOQL endpoint...")
    
    try:
        # Submit request using runsync
        response = requests.post(
            f"https://api.runpod.ai/v2/{endpoint_id}/runsync",
            headers=headers,
            json=payload,
            timeout=300
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "COMPLETED":
                output = result.get("output", {})
                
                if output.get("status") == "success":
                    sql = output.get("sql", "")
                    metadata = output.get("metadata", {})
                    
                    print(f"\n✅ SQL generated successfully!")
                    print(f"📊 Model: {metadata.get('model', 'unknown')}")
                    print(f"⏱️  Processing time: {result.get('executionTime', 'N/A')}ms")
                    
                    print("\n" + "="*80)
                    print("📄 GENERATED SQL:")
                    print("="*80)
                    print(sql)
                    print("="*80)
                    
                    # Check for expected elements in the SQL
                    expected_elements = [
                        "Patient",
                        "gender",
                        "male",
                        "Condition",
                        "heart",
                        "Observation",
                        "smok",
                        "Appointment",
                        "12 week"
                    ]
                    
                    missing = []
                    for element in expected_elements:
                        if element.lower() not in sql.lower():
                            missing.append(element)
                    
                    if missing:
                        print(f"\n⚠️  Potentially missing elements: {', '.join(missing)}")
                    else:
                        print("\n✅ All expected elements present in SQL!")
                    
                    # Save output
                    with open("iasoql_test_output.json", "w") as f:
                        json.dump({
                            "query": COMPLEX_QUERY,
                            "sql": sql,
                            "metadata": metadata,
                            "execution_time": result.get('executionTime'),
                            "full_response": result
                        }, f, indent=2)
                    print("\n💾 Full output saved to iasoql_test_output.json")
                    
                else:
                    print(f"\n❌ Generation failed: {output.get('error', 'Unknown error')}")
                    print(f"Full output: {json.dumps(output, indent=2)}")
                    
            else:
                print(f"\n❌ Job status: {result.get('status')}")
                if result.get("error"):
                    print(f"Error: {result['error']}")
                print(f"Full response: {json.dumps(result, indent=2)}")
                
        else:
            print(f"\n❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
            # Try to parse error response
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check environment
    api_key = os.environ.get('RUNPOD_API_KEY')
    endpoint_id = os.environ.get('IASOQL_ENDPOINT_ID')
    
    print("Environment check:")
    print(f"- RUNPOD_API_KEY: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"- IASOQL_ENDPOINT_ID: {'✅ Set' if endpoint_id else '❌ Missing'} ({endpoint_id})")
    print()
    
    if api_key and endpoint_id:
        test_iasoql_query()
    else:
        print("❌ Please set required environment variables in .env file")