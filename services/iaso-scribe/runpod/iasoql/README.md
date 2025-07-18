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

### Quick Deployment Steps

1. **Upload Model to HuggingFace** (if not already done):
   ```bash
   # Set your HuggingFace token
   export HUGGINGFACE_TOKEN=your_hf_token_here
   
   # Upload model from S3 to HuggingFace
   python upload_to_huggingface.py
   ```

2. **Build and Push Docker Image**:
   ```bash
   docker build -t iasoql-healthcare .
   docker tag iasoql-healthcare:latest <your-registry>/iasoql-healthcare:latest
   docker push <your-registry>/iasoql-healthcare:latest
   ```

3. **Deploy to RunPod**:
   - Go to [RunPod Console](https://www.runpod.io/console/serverless)
   - Click "New Endpoint"
   - Configure:
     - **Name**: `iasoql-healthcare`
     - **Container Image**: `<your-registry>/iasoql-healthcare:latest`
     - **GPU Type**: RTX 3090 or better (24GB VRAM minimum)
     - **GPU Count**: 1
     - **Min Workers**: 0 (scales to zero)
     - **Max Workers**: 2
     - **Container Disk**: 20GB
     - **Volume Disk**: 50GB (for model caching)
   
   - **Environment Variables**:
     ```
     HUGGINGFACE_TOKEN=your_hf_token_here
     ```

### Model Information

IASOQL is hosted on HuggingFace at `vivkris/iasoql-7B` (private repository).

The model:
- Is derived from XiYanSQL-QwenCoder-7B-2504 (Apache 2.0 licensed)
- Fine-tuned specifically for healthcare SQL generation
- Optimized for ClickHouse queries on FHIR data
- Requires HuggingFace token for access

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