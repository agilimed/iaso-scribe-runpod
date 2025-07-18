# IASOQL - Healthcare SQL Generation

IASOQL is a fine-tuned text-to-SQL model specifically designed for healthcare analytics on FHIR data stored in ClickHouse.

## Overview

IASOQL generates ClickHouse SQL queries from natural language questions about healthcare data. It's optimized for:
- FHIR resource queries
- Complex healthcare analytics
- Multi-table joins across patient data
- Temporal queries for medical timelines

## Model Details

- **Base Model**: XiYanSQL-QwenCoder-7B-2504 (Apache 2.0 licensed)
- **Fine-tuning**: Healthcare-specific SQL patterns and FHIR resources
- **Model Size**: 14.2GB
- **Location**: Private HuggingFace repo (vivkris/iasoql-7B)

## RunPod Deployment

- **Endpoint ID**: nefuor02sjocfd
- **GPU**: NVIDIA A40
- **API**: RunPod Serverless API

## Usage Examples

### Complex Healthcare Query
```python
query = "Show me Male patient who smoke and have a history of heart disease and have an appointment booked in next 12 weeks"

# Generated SQL:
WITH patient_ids AS (
    SELECT DISTINCT p.resource_id
    FROM nexuscare_analytics.fhir_current p
    WHERE p.resource_type = 'Patient'
    AND p.sign = 1
    AND JSONExtractString(p.resource, '$.gender') = 'male'
),
smoking_patients AS (
    SELECT DISTINCT JSONExtractString(o.resource, '$.subject.reference') as patient_ref
    FROM nexuscare_analytics.fhir_current o
    WHERE o.resource_type = 'Observation'
    AND o.sign = 1
    AND (
        JSONExtractString(o.resource, '$.code.coding[0].code') = '72166-2'
        OR JSONExtractString(o.resource, '$.valueCodeableConcept.coding[0].code') = '77176002'
    )
),
heart_disease_patients AS (
    SELECT DISTINCT JSONExtractString(c.resource, '$.subject.reference') as patient_ref
    FROM nexuscare_analytics.fhir_current c
    WHERE c.resource_type = 'Condition'
    AND c.sign = 1
    AND (
        JSONExtractString(c.resource, '$.code.coding[0].display') LIKE '%heart%'
        OR JSONExtractString(c.resource, '$.code.coding[0].code') LIKE 'I2%'
    )
),
upcoming_appointments AS (
    SELECT DISTINCT JSONExtractString(a.resource, '$.participant[0].actor.reference') as patient_ref
    FROM nexuscare_analytics.fhir_current a
    WHERE a.resource_type = 'Appointment'
    AND a.sign = 1
    AND parseDateTimeBestEffort(JSONExtractString(a.resource, '$.start')) BETWEEN now() AND now() + INTERVAL 12 WEEK
)
SELECT p.*
FROM nexuscare_analytics.fhir_current p
WHERE p.resource_id IN (SELECT resource_id FROM patient_ids)
AND concat('Patient/', p.resource_id) IN (SELECT patient_ref FROM smoking_patients)
AND concat('Patient/', p.resource_id) IN (SELECT patient_ref FROM heart_disease_patients)
AND concat('Patient/', p.resource_id) IN (SELECT patient_ref FROM upcoming_appointments)
```

## API Integration

```python
import httpx

async def generate_sql(query: str, schema_context: str = None):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync",
            headers={
                "Authorization": f"Bearer {RUNPOD_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "input": {
                    "query": query,
                    "schema_context": schema_context,
                    "tenant_id": "your_tenant_id"
                }
            }
        )
        return response.json()
```

## Schema Context

The model expects a schema context describing the FHIR data structure:

```
Database: nexuscare_analytics
Table: fhir_current

Key columns:
- tenant_id: String
- resource_type: String (Patient, Observation, Condition, etc.)
- resource: JSON (full FHIR resource)
- resource_id: String
- sign: Int8 (1 = current, -1 = deleted)
- created_at: DateTime

JSON paths for common FHIR fields:
- Patient gender: JSONExtractString(resource, '$.gender')
- Patient birthDate: JSONExtractString(resource, '$.birthDate')
- Condition code: JSONExtractString(resource, '$.code.coding[0].display')
- Observation value: JSONExtractString(resource, '$.valueCodeableConcept.coding[0].code')
```

## Testing

Test scripts available in `/scripts/test/`:
- `test_iasoql_endpoint.py` - Comprehensive endpoint testing
- `test_iasoql_working.py` - Basic functionality test

## Performance

- Average response time: 5-10 seconds
- Token generation speed: ~20 tokens/second
- Max context length: 8192 tokens