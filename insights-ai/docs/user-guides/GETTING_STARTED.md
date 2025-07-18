# Getting Started with IASO AI Services

Welcome to IASO AI Services! This guide will help you integrate your application with our healthcare AI platform in just a few steps.

## What is IASO?

IASO is a healthcare AI platform that provides:
- **Natural Language to SQL** - Convert questions to database queries
- **Clinical Entity Extraction** - Extract medical concepts from text
- **Healthcare RAG** - Retrieve relevant medical knowledge
- **Conversational Analytics** - Chat-based data exploration

## Quick Start (5 minutes)

### 1. Get Your API Credentials

Contact your IASO administrator to obtain:
- API endpoint URL (e.g., `https://your-org.iaso-ai.com`)
- API key or JWT token
- Tenant ID (for multi-tenant setups)

### 2. Make Your First API Call

```bash
# Simple health check
curl -X GET https://your-org.iaso-ai.com/health

# Your first query
curl -X POST https://your-org.iaso-ai.com/api/v1/query \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many patients were admitted last month?",
    "mode": "insights_only"
  }'
```

### 3. Choose Your Integration Method

#### Option A: Simple REST API (Recommended for most)
```python
import requests

# Configure your client
IASO_API_URL = "https://your-org.iaso-ai.com"
API_KEY = "your-api-key"

# Make a query
response = requests.post(
    f"{IASO_API_URL}/api/v1/query",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "query": "Show me diabetic patients over 65",
        "mode": "clinical_to_sql",
        "include_explanation": True
    }
)

result = response.json()
print(f"SQL: {result['sql']}")
print(f"Explanation: {result['explanation']}")
```

#### Option B: WebSocket for Real-time Chat
```javascript
const ws = new WebSocket('wss://your-org.iaso-ai.com/ws/chat');

ws.on('open', () => {
    ws.send(JSON.stringify({
        type: 'auth',
        token: 'YOUR_API_KEY'
    }));
    
    ws.send(JSON.stringify({
        type: 'message',
        content: 'What are the top diagnoses this week?'
    }));
});

ws.on('message', (data) => {
    const response = JSON.parse(data);
    console.log('AI Response:', response);
});
```

#### Option C: Batch Processing
```python
# Process multiple queries efficiently
batch_request = {
    "items": [
        {"query": "Total admissions today", "mode": "insights_only"},
        {"query": "Patients with chest pain", "mode": "clinical_to_sql"},
        {"query": "Average length of stay", "mode": "insights_only"}
    ]
}

response = requests.post(
    f"{IASO_API_URL}/api/v1/batch",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json=batch_request
)
```

## Common Use Cases

### 1. Healthcare Analytics Dashboard
```python
# Get key metrics for your dashboard
queries = [
    "Current bed occupancy rate",
    "Emergency department wait times",
    "30-day readmission rate",
    "Patient satisfaction scores"
]

for query in queries:
    result = iaso_client.query(query, mode="insights_only")
    # Use result['sql'] with your database
    # Display result['data'] in your dashboard
```

### 2. Clinical Decision Support
```python
# Extract clinical concepts and get relevant guidelines
patient_note = "72-year-old male with chest pain and shortness of breath"

# Extract clinical entities
entities = iaso_client.process(
    patient_note, 
    mode="clinical_only"
)

# Get relevant clinical guidelines
guidelines = iaso_client.search(
    query=f"guidelines for {entities['conditions'][0]}",
    collection="medical_knowledge"
)
```

### 3. Natural Language Report Generation
```python
# Generate insights from your data
context = {
    "report_type": "monthly_summary",
    "department": "cardiology"
}

report = iaso_client.generate_report(
    "Create a monthly summary of cardiology department performance",
    context=context
)
```

## Processing Modes Explained

| Mode | Use Case | Example |
|------|----------|---------|
| `clinical_only` | Extract medical entities | "Extract conditions from: patient has diabetes and hypertension" |
| `insights_only` | Generate SQL queries | "Show me all patients admitted yesterday" |
| `clinical_to_sql` | SQL with medical context | "Find patients with uncontrolled diabetes" (understands HbA1c > 9%) |
| `rag_clinical` | Search + entity extraction | "What are the symptoms of COVID-19?" |
| `rag_insights` | Search + SQL generation | "Show admissions like the 2020 flu season" |
| `full_pipeline` | Complete processing | Complex multi-step analysis |

## Authentication Options

### API Key (Simplest)
```bash
curl -H "X-API-Key: your-api-key" https://your-org.iaso-ai.com/api/v1/query
```

### JWT Token (Recommended)
```bash
curl -H "Authorization: Bearer your-jwt-token" https://your-org.iaso-ai.com/api/v1/query
```

### OAuth2 (Enterprise)
```python
# Using OAuth2 flow
from authlib.integrations.requests_client import OAuth2Session

client = OAuth2Session(
    client_id='your-client-id',
    client_secret='your-client-secret',
    redirect_uri='https://your-app.com/callback'
)

token = client.fetch_token('https://your-org.iaso-ai.com/oauth/token')
```

## Error Handling

```python
try:
    response = iaso_client.query("Show patient count")
    
    if response.status_code == 200:
        result = response.json()
    elif response.status_code == 429:
        # Rate limited - wait and retry
        time.sleep(60)
    elif response.status_code == 401:
        # Refresh authentication
        refresh_token()
    else:
        # Log error
        logger.error(f"API error: {response.status_code}")
        
except requests.RequestException as e:
    # Network error - implement retry logic
    logger.error(f"Network error: {e}")
```

## Rate Limits

| Authentication Type | Requests/Hour | Concurrent Requests |
|-------------------|---------------|-------------------|
| API Key | 1,000 | 10 |
| JWT Token | 10,000 | 50 |
| OAuth2 | Custom | Custom |

## SDK Installation

### Python
```bash
pip install iaso-ai-sdk
```

```python
from iaso import IasoClient

client = IasoClient(
    api_key="your-api-key",
    base_url="https://your-org.iaso-ai.com"
)

result = client.query("Show me today's admissions")
```

### JavaScript/TypeScript
```bash
npm install @iaso/ai-sdk
```

```typescript
import { IasoClient } from '@iaso/ai-sdk';

const client = new IasoClient({
    apiKey: 'your-api-key',
    baseUrl: 'https://your-org.iaso-ai.com'
});

const result = await client.query("Show me today's admissions");
```

## Testing Your Integration

### 1. Test Environment
```bash
# Use the test endpoint
export IASO_API_URL="https://test.iaso-ai.com"
export IASO_API_KEY="test-key-provided-by-admin"
```

### 2. Sample Test Queries
```python
# Test different modes
test_queries = [
    ("List all patients", "insights_only"),
    ("Extract: diabetes with neuropathy", "clinical_only"),
    ("Patients with high blood pressure", "clinical_to_sql"),
]

for query, mode in test_queries:
    result = client.query(query, mode=mode)
    assert result['status'] == 'success'
```

### 3. Verify Results
```python
# Verify SQL is valid
sql = result['sql']
# Test against your database schema

# Verify clinical entities
entities = result['entities']
assert 'conditions' in entities
assert 'medications' in entities
```

## Security Best Practices

1. **Never expose API keys in client-side code**
   ```javascript
   // BAD - Don't do this
   const apiKey = 'sk-1234567890';
   
   // GOOD - Use environment variables
   const apiKey = process.env.IASO_API_KEY;
   ```

2. **Implement request signing for production**
   ```python
   import hmac
   import hashlib
   
   signature = hmac.new(
       secret_key.encode(),
       request_body.encode(),
       hashlib.sha256
   ).hexdigest()
   ```

3. **Use tenant isolation for multi-tenant apps**
   ```python
   headers = {
       "Authorization": f"Bearer {token}",
       "X-Tenant-ID": "tenant-123"
   }
   ```

## Monitoring & Debugging

### Enable Debug Mode
```python
client = IasoClient(debug=True)
# Logs all requests and responses
```

### Request IDs
```python
# Every response includes a request ID
result = client.query("Show admissions")
print(f"Request ID: {result['request_id']}")
# Use this ID when contacting support
```

### Health Checks
```python
# Monitor service health
health = client.health_check()
assert health['status'] == 'healthy'
assert health['services']['clinical_ai'] == 'up'
assert health['services']['iasoql'] == 'up'
```

## Next Steps

1. **Explore Advanced Features**
   - [Conversational Analytics API Guide](../CONVERSATIONAL_ANALYTICS_API.md)
   - [Clinical AI API Reference](../CLINICAL_AI_API_REFERENCE.md)
   - [API Gateway Architecture](../API_GATEWAY_ARCHITECTURE.md)

2. **Join Our Community**
   - Developer Forum: https://community.iaso-ai.com
   - GitHub: https://github.com/iaso-ai
   - Support: support@iaso-ai.com

3. **Get Certified**
   - Take our free online course
   - Become an IASO Certified Developer

## Need Help?

- 📧 Email: support@iaso-ai.com
- 💬 Slack: iaso-community.slack.com
- 📚 Full Docs: https://docs.iaso-ai.com
- 🎟️ Support Tickets: https://support.iaso-ai.com

---

**Ready to build something amazing?** Start with the code examples above and have your first AI-powered healthcare query running in minutes!