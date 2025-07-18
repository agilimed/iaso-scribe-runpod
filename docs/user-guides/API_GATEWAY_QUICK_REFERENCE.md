# API Gateway Quick Reference

## 🚀 Quick Start

```bash
# Start all services
./scripts/start_all_services.sh

# Test the gateway
python scripts/test_api_gateway.py

# Access API docs
open http://localhost:8080/docs
```

## 📊 Processing Modes at a Glance

| Mode | When to Use | Services Used | Response Time |
|------|-------------|---------------|---------------|
| **Clinical Only** | Extract medical entities | Clinical AI | ~200ms |
| **Insights Only** | Generate SQL queries | IasoQL | ~300ms |
| **Clinical→SQL** | SQL with medical context | Clinical AI + IasoQL | ~500ms |
| **RAG+Clinical** | Context-aware entity extraction | Qdrant + Clinical AI | ~400ms |
| **RAG+Insights** | SQL with examples | Qdrant + IasoQL | ~400ms |
| **Full Pipeline** | Complex queries | All services | ~800ms |

## 🔌 Service Endpoints

### Core Services
- **API Gateway**: `http://localhost:8080`
- **Clinical AI**: `http://localhost:8002`
- **Terminology**: `http://localhost:8001`
- **IasoQL**: `http://localhost:8008`
- **Embeddings**: `http://localhost:8050`
- **SLM Service**: `http://localhost:8007`
- **Qdrant**: `http://localhost:6333`

### Health Checks
```bash
curl http://localhost:8080/health
curl http://localhost:8002/health
curl http://localhost:8008/health
```

## 📝 Common API Calls

### 1. Simple Chat Query
```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the symptoms of diabetes?"
  }'
```

### 2. Extract Clinical Entities
```bash
curl -X POST http://localhost:8080/api/v1/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient has type 2 diabetes with neuropathy",
    "mode": "clinical_only"
  }'
```

### 3. Generate SQL Query
```bash
curl -X POST http://localhost:8080/api/v1/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Show all diabetic patients with HbA1c > 7",
    "mode": "insights_only"
  }'
```

### 4. Clinical-Informed SQL
```bash
curl -X POST http://localhost:8080/api/v1/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Find patients with poor diabetes control",
    "mode": "clinical_to_sql"
  }'
```

### 5. RAG-Enhanced Query
```bash
curl -X POST http://localhost:8080/api/v1/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Latest diabetes treatment guidelines",
    "mode": "rag_clinical",
    "enable_rag": true,
    "rag_collection": "medical_knowledge"
  }'
```

### 6. Create Agent
```bash
curl -X POST http://localhost:8080/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "medical_research",
    "parameters": {
      "query": "Compare ACE inhibitors for hypertension"
    }
  }'
```

## 🔄 WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8080/ws/my-client-id');

ws.onopen = () => {
    console.log('Connected to AI Gateway');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// Send a message
ws.send(JSON.stringify({
    type: 'message',
    text: 'What is the normal HbA1c range?'
}));
```

## 🏗️ Qdrant Collections

| Collection | Purpose | Embedding Model | Dimensions |
|------------|---------|-----------------|------------|
| `fhir_resources` | FHIR patient data | BGE-M3 | 1024 |
| `medical_knowledge` | Medical literature | BGE-M3 | 1024 |
| `query_patterns` | Successful queries | BGE-M3 | 1024 |
| `clinical_contexts` | Clinical notes | ClinicalBERT | 768 |

## 🔧 Configuration

### Environment Variables
```env
# Required
CLINICAL_AI_URL=http://localhost:8002
IASOQL_URL=http://localhost:8008
QDRANT_URL=http://localhost:6333
JWT_SECRET=your-secret-key

# Optional
REDIS_URL=redis://localhost:6379
KAFKA_BROKERS=localhost:9092
CACHE_TTL=3600
RATE_LIMIT=1000/hour
```

### Docker Compose
```yaml
version: '3.8'
services:
  api-gateway:
    image: nexuscare/api-gateway:latest
    ports:
      - "8080:8080"
    environment:
      - CLINICAL_AI_URL=http://clinical-ai:8002
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - clinical-ai
      - qdrant
      - redis
```

## 🧪 Testing

### Unit Test
```python
async def test_clinical_extraction():
    client = NexusCareAPIClient()
    response = await client.extract_clinical_entities(
        "Patient has diabetes"
    )
    assert len(response['entities']) > 0
```

### Integration Test
```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_api_gateway.py::test_full_pipeline
```

### Load Test
```bash
# Using locust
locust -f load_tests.py --host=http://localhost:8080 --users=100 --spawn-rate=10
```

## 📊 Monitoring

### Key Metrics
- Request latency by mode
- Service availability
- Cache hit rate
- Qdrant query performance
- WebSocket connections

### Logs
```bash
# Gateway logs
tail -f logs/api-gateway.log

# All service logs
tail -f logs/*.log

# Filter errors
grep ERROR logs/*.log
```

## 🚨 Common Issues

### Service Not Responding
```bash
# Check service health
curl http://localhost:8002/health

# Restart service
./scripts/stop_all_services.sh
./scripts/start_all_services.sh
```

### Slow Response Times
1. Check cache configuration
2. Verify Qdrant indexes
3. Monitor service CPU/memory
4. Enable request batching

### Authentication Errors
1. Verify JWT token is valid
2. Check JWT_SECRET matches
3. Ensure token has required claims

## 🎯 Best Practices

1. **Choose the Right Mode**
   - Start with simpler modes
   - Use full pipeline only when needed
   - Cache frequently used queries

2. **Optimize Performance**
   - Batch similar requests
   - Use streaming for large responses
   - Enable caching appropriately

3. **Handle Errors Gracefully**
   - Implement retry logic
   - Use fallback modes
   - Log errors for debugging

4. **Security**
   - Always use authentication
   - Validate input data
   - Don't expose sensitive info

## 📚 Further Reading

- [Full Implementation Guide](./API_GATEWAY_IMPLEMENTATION_GUIDE.md)
- [Architecture Overview](./API_GATEWAY_ARCHITECTURE.md)
- [Flow Diagrams](./API_GATEWAY_FLOW_DIAGRAMS.md)
- [Example Usage](../examples/api_gateway_usage.py)