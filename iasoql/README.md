# IASOQL RunPod Deployment

Healthcare-specific SQL generation model optimized for ClickHouse queries on FHIR data.

## Overview

IASOQL is a hybrid SQL generation system that combines:
- **Template matching** for common healthcare queries
- **LLM-based generation** for complex queries
- **FHIR-aware schema understanding**
- **ClickHouse JSON function expertise**

## Features

### Template-Based Queries
Fast, reliable SQL generation for common patterns:
- Patient counts by condition
- Recent lab results
- Active medications
- Upcoming appointments
- Vital signs

### LLM Fallback
When templates don't match, uses fine-tuned model for:
- Complex aggregations
- Multi-table joins
- Temporal queries
- Custom analytics

## Deployment

### RunPod Setup

1. Go to [RunPod Console](https://www.runpod.io/console/serverless)
2. Click "New Endpoint"
3. Configure:
   - **Name**: `iasoql-healthcare`
   - **Container Image**: Custom (upload this folder)
   - **GPU Type**: RTX 3090 or better (24GB VRAM minimum)
   - **GPU Count**: 1
   - **Min Workers**: 0 (scales to zero)
   - **Max Workers**: 2
   - **Container Disk**: 20GB
   - **Volume Disk**: 20GB (for model caching)

4. Environment Variables (REQUIRED):
   ```
   MODEL_NAME=iasoql-7b
   MODEL_PATH=/runpod-volume/models
   S3_MODEL_PATH=s3://your-bucket/path/to/iasoql-model.tar.gz
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-west-2
   ```

### Model Storage Options

#### Option 1: S3 Download (Recommended)
The handler will automatically download your proprietary IASOQL model from S3 on first run:
- Model is cached in the RunPod network volume
- Subsequent starts use the cached model
- Update S3_MODEL_PATH to point to your model archive

#### Option 2: Pre-baked Docker Image
Include the model in the Docker image during build:
1. Place model files in `iasoql/model/` directory
2. Update Dockerfile to COPY the model
3. This increases image size but eliminates download time

### Testing

After deployment:

```bash
export RUNPOD_API_KEY=your_api_key
export IASOQL_ENDPOINT_ID=your_endpoint_id

./test_iasoql.py
```

## API Usage

### Request Format

```json
{
  "input": {
    "query": "How many patients have diabetes?",
    "schema_context": "...",
    "tenant_id": "demo_tenant",
    "rag_context": "Optional context from RAG",
    "examples": []
  }
}
```

### Response Format

```json
{
  "sql": "SELECT COUNT(DISTINCT ...) FROM ...",
  "source": "template",  // or "llm"
  "confidence": "high",
  "metadata": {
    "model": "codellama/CodeLlama-7b-Instruct-hf",
    "template_name": "count_patients_by_condition"
  }
}
```

## Example Queries

### Simple Count
**Query**: "How many patients have diabetes?"
```sql
SELECT COUNT(DISTINCT JSONExtractString(resource, '$.subject.reference')) as patient_count
FROM nexuscare_analytics.fhir_current
WHERE tenant_id = 'demo_tenant'
  AND sign = 1
  AND resource_type = 'Condition'
  AND JSONExtractString(resource, '$.code.coding[0].display') ILIKE '%diabetes%'
```

### Recent Labs
**Query**: "Show recent lab results for patient 123"
```sql
SELECT 
  JSONExtractString(resource, '$.code.display') as test_name,
  JSONExtractFloat(resource, '$.valueQuantity.value') as value,
  JSONExtractString(resource, '$.valueQuantity.unit') as unit,
  JSONExtractString(resource, '$.effectiveDateTime') as test_date
FROM nexuscare_analytics.fhir_current
WHERE tenant_id = 'demo_tenant'
  AND sign = 1
  AND resource_type = 'Observation'
  AND JSONExtractString(resource, '$.subject.reference') = 'Patient/123'
ORDER BY parseDateTimeBestEffort(JSONExtractString(resource, '$.effectiveDateTime')) DESC
LIMIT 20
```

## Performance

- **Template queries**: <100ms
- **LLM queries**: 2-5 seconds
- **Cold start**: 10-15 seconds (model loading)
- **Concurrent requests**: Up to 3 workers

## Cost Optimization

- **Scales to zero** when idle
- **Template matching** reduces LLM usage
- **Efficient tokenization** for healthcare terms
- **Batch processing** support

## Integration

### With IasoChat
```python
# In RASA actions
sql_result = await generate_healthcare_sql(
    query="recent medications for patient",
    patient_id=patient_id,
    use_rag_context=True
)
```

### With RAG System
RAG context improves SQL accuracy by providing:
- Relevant patient information
- Clinical codes (LOINC, ICD-10)
- Reference ranges
- Temporal context

## Monitoring

Check RunPod dashboard for:
- Request latency
- GPU utilization
- Error rates
- Cost tracking

## Troubleshooting

### Common Issues

1. **Timeout errors**: Increase timeout or reduce query complexity
2. **Invalid SQL**: Check schema context is correct
3. **Template not matching**: Verify query format matches patterns
4. **High latency**: Check if model is cold starting

### Debug Mode

Set environment variable:
```
DEBUG=true
```

This will log:
- Template matching attempts
- Prompt construction
- Token usage
- Generation parameters