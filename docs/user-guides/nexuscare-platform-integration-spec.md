# NexusCare Platform → IASO AI Services Integration Specification

## Current Status

### ✅ Infrastructure Ready
- **Qdrant Vector DB**: Running at `localhost:6333` with 5 collections configured
- **Collections Created**: `fhir_resources`, `medical_knowledge`, `query_patterns`, `clinical_contexts`, `terminology_cache`
- **Sample Data**: 4 documents loaded for testing

### ❌ AI Services Need Deployment
- **BGE-M3 Embeddings Service**: Not running (should be on gRPC port 50051)
- **Clinical AI Service**: Not running (should be on port 8002)
- **FHIR RAG Processor**: Not running (should be on port 50052)

## Integration Architecture

```
NexusCare Platform → IASO AI Services → Qdrant Vector DB
                   ↓
              [Authentication Layer]
                   ↓
           [Load Balancer/Gateway]
                   ↓
    [Embeddings gRPC:50051] [Clinical AI] [RAG Processor]
                   ↓
              [Qdrant HTTP:6333]
```

### Confirmed Backend Communication Protocols
- **Qdrant**: HTTP REST API (`@qdrant/js-client-rest` → `http://localhost:6333`)
- **Embeddings Service**: gRPC (`@grpc/grpc-js` → `localhost:50051`)

## Integration Options (Recommended Order)

### Option 1: Direct FHIR Event Streaming (RECOMMENDED)
**Best for**: Real-time updates, automatic processing

```typescript
// In your NexusCare platform
export class FHIREventPublisher {
  async publishFHIRChange(resource: any, operation: 'create' | 'update' | 'delete') {
    const event = {
      id: uuid.v4(),
      timestamp: new Date().toISOString(),
      tenant_id: resource.meta?.extension?.find(e => e.url === 'tenant')?.valueString,
      operation,
      resource_type: resource.resourceType,
      resource_id: resource.id,
      patient_id: this.extractPatientId(resource),
      resource: resource
    };
    
    // Option A: Kafka (if available)
    await this.kafkaProducer.send({
      topic: 'fhir.resources.changes',
      messages: [{ value: JSON.stringify(event) }]
    });
    
    // Option B: Direct API call to RAG Processor
    await fetch('http://iaso-rag-processor:50052/process-fhir-event', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.IASO_API_KEY}`
      },
      body: JSON.stringify(event)
    });
  }
}
```

### Option 2: Batch FHIR Upload (GOOD FOR MIGRATION)
**Best for**: Initial data migration, bulk updates

```typescript
export class FHIRBatchUploader {
  async uploadFHIRBatch(resources: any[]) {
    const chunks = this.chunkArray(resources, 100); // Process in batches of 100
    
    for (const chunk of chunks) {
      const response = await fetch('http://iaso-api-gateway:8080/api/v1/fhir/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.IASO_API_KEY}`,
          'X-Tenant-ID': this.tenantId
        },
        body: JSON.stringify({
          resources: chunk,
          options: {
            generate_embeddings: true,
            update_existing: true,
            chunk_types: ['granular_fact', 'resource_summary']
          }
        })
      });
      
      if (!response.ok) {
        throw new Error(`Batch upload failed: ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log(`Processed ${result.processed_count} resources`);
    }
  }
}
```

### Option 3: Direct Qdrant Integration (SIMPLEST)
**Best for**: Custom implementations, specific use cases

```typescript
export class DirectQdrantClient {
  private qdrantUrl = 'http://qdrant:6333';
  private embeddingsClient: EmbeddingsServiceClient; // gRPC client
  
  async storeResource(resource: any, tenantId: string) {
    // 1. Generate embeddings via gRPC
    const text = this.resourceToText(resource);
    const embeddingRequest = {
      texts: [text],
      model: 'bge-m3'
    };
    const embeddingResponse = await this.embeddingsClient.generateEmbeddings(embeddingRequest);
    const embeddings = embeddingResponse.embeddings;
    
    // 2. Store in Qdrant
    const point = {
      id: `${resource.resourceType}:${resource.id}`,
      vector: embeddings[0],
      payload: {
        tenant_id: tenantId,
        resource_type: resource.resourceType,
        resource_id: resource.id,
        patient_id: this.extractPatientId(resource),
        timestamp: new Date().toISOString(),
        resource_text: text,
        metadata: this.extractMetadata(resource)
      }
    };
    
    await fetch(`${this.qdrantUrl}/collections/fhir_resources/points`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ points: [point] })
    });
  }
}
```

## Required Environment Variables

Add these to your NexusCare platform environment:

```env
# IASO AI Services
IASO_API_URL=http://iaso-api-gateway:8080
IASO_API_KEY=your_secure_api_key_here
IASO_EMBEDDINGS_GRPC_URL=localhost:50051
IASO_CLINICAL_AI_URL=http://iaso-clinical:8002
IASO_RAG_PROCESSOR_URL=http://iaso-rag-processor:50052

# Qdrant (if using direct integration)
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=your_qdrant_key_here

# Service timeouts
IASO_SERVICE_TIMEOUT=30000
IASO_BATCH_SIZE=100
IASO_RETRY_ATTEMPTS=3
```

## Authentication & Security

### Option A: API Key Authentication
```typescript
const headers = {
  'Authorization': `Bearer ${process.env.IASO_API_KEY}`,
  'X-Tenant-ID': tenantId,
  'Content-Type': 'application/json'
};
```

### Option B: Service Account (Google Cloud)
```typescript
import { GoogleAuth } from 'google-auth-library';

const auth = new GoogleAuth({
  credentials: JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_KEY),
  scopes: ['https://www.googleapis.com/auth/cloud-platform']
});

const accessToken = await auth.getAccessToken();
const headers = {
  'Authorization': `Bearer ${accessToken}`,
  'X-Tenant-ID': tenantId
};
```

## Step-by-Step Deployment Guide

### 1. Deploy IASO AI Services

```bash
# Deploy to your Kubernetes cluster
kubectl apply -f infrastructure/kubernetes/gke-deployment/applications/

# Or use Docker Compose for local development
cd infrastructure/development/rag/
docker-compose up -d
```

### 2. Configure NexusCare Platform

```typescript
// Add to your services/ai/ directory
export class IASOServiceClient {
  private apiUrl: string;
  private apiKey: string;
  
  constructor() {
    this.apiUrl = process.env.IASO_API_URL!;
    this.apiKey = process.env.IASO_API_KEY!;
  }
  
  async enhancedQuery(query: string, tenantId: string): Promise<QueryResult> {
    const response = await fetch(`${this.apiUrl}/api/v1/rag/enhanced-query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'X-Tenant-ID': tenantId,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query,
        options: {
          include_clinical_context: true,
          max_results: 20,
          similarity_threshold: 0.7
        }
      })
    });
    
    return response.json();
  }
}
```

### 3. Integrate with Existing Services

```typescript
// Update your existing conversational analytics
export class EnhancedConversationalService {
  private iasoClient: IASOServiceClient;
  
  async processQuery(query: string, tenantId: string) {
    // 1. Get RAG context from IASO
    const ragContext = await this.iasoClient.enhancedQuery(query, tenantId);
    
    // 2. Use existing IASOQL with enhanced context
    const sqlResult = await this.iasoqlService.generateSQL(query, {
      clinicalContext: ragContext.clinical_context,
      relevantPatients: ragContext.relevant_patients,
      suggestedCodes: ragContext.suggested_codes
    });
    
    // 3. Return enhanced results
    return {
      sql: sqlResult.sql,
      clinicalInterpretation: ragContext.interpretation,
      relatedContext: ragContext.related_documents
    };
  }
}
```

## API Endpoints Specification

### FHIR RAG Processor (gRPC)
```protobuf
service FHIRRAGProcessor {
  rpc ProcessFHIREvent(FHIREvent) returns (ProcessResult);
  rpc SearchSimilar(SearchRequest) returns (SearchResponse);
  rpc GetClinicalContext(ContextRequest) returns (ContextResponse);
}
```

### API Gateway (REST)
```yaml
paths:
  /api/v1/fhir/batch:
    post:
      summary: Upload FHIR resources in batch
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                resources: 
                  type: array
                  items: {$ref: '#/components/schemas/FHIRResource'}
                options:
                  type: object
                  properties:
                    generate_embeddings: {type: boolean}
                    update_existing: {type: boolean}
                    chunk_types: {type: array, items: {type: string}}
  
  /api/v1/rag/enhanced-query:
    post:
      summary: Query with RAG enhancement
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                query: {type: string}
                options:
                  type: object
                  properties:
                    include_clinical_context: {type: boolean}
                    max_results: {type: integer}
                    similarity_threshold: {type: number}
```

## Data Flow Examples

### Real-time FHIR Processing
```
Patient Resource Created → NexusCare Platform → FHIR Event → IASO RAG Processor
                                                              ↓
Resource Templates → Chunking → BGE-M3 Embeddings → Qdrant Storage
```

### Enhanced Query Processing
```
Natural Language Query → IASO API Gateway → Semantic Search (Qdrant)
                                          ↓
Clinical Context Assembly → IASOQL Enhanced Prompt → ClickHouse SQL
                                          ↓
Results + Clinical Interpretation → NexusCare Platform UI
```

## Performance Considerations

### Batch Processing Recommendations
- **Batch Size**: 100 resources per request
- **Rate Limiting**: 10 requests/second per tenant
- **Timeout**: 30 seconds per batch
- **Retry**: 3 attempts with exponential backoff

### Caching Strategy
```typescript
// Cache embeddings for frequently accessed resources
const embeddingCache = new Map<string, number[]>();

async function getCachedEmbedding(text: string): Promise<number[]> {
  const hash = crypto.createHash('sha256').update(text).digest('hex');
  
  if (embeddingCache.has(hash)) {
    return embeddingCache.get(hash)!;
  }
  
  const embedding = await this.generateEmbedding(text);
  embeddingCache.set(hash, embedding);
  return embedding;
}
```

## Monitoring & Observability

### Required Metrics
```typescript
// Add to your monitoring stack
const iasoMetrics = {
  'iaso.requests.total': counter,
  'iaso.requests.duration': histogram,
  'iaso.embeddings.generated': counter,
  'iaso.qdrant.operations': counter,
  'iaso.errors.total': counter
};
```

### Health Checks
```typescript
app.get('/health/iaso', async (req, res) => {
  const checks = await Promise.allSettled([
    fetch(`${process.env.IASO_API_URL}/health`),
    fetch(`${process.env.QDRANT_URL}/health`),
    fetch(`${process.env.IASO_EMBEDDINGS_URL}/health`)
  ]);
  
  const healthy = checks.every(check => 
    check.status === 'fulfilled' && check.value.ok
  );
  
  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'healthy' : 'unhealthy',
    services: {
      api_gateway: checks[0].status === 'fulfilled',
      qdrant: checks[1].status === 'fulfilled',
      embeddings: checks[2].status === 'fulfilled'
    }
  });
});
```

## Next Steps

1. **Deploy IASO Services**: Choose deployment method (Kubernetes recommended)
2. **Configure Authentication**: Set up service accounts or API keys
3. **Test Integration**: Start with Option 3 (Direct Qdrant) for simplicity
4. **Migrate Data**: Use Option 2 (Batch Upload) for existing FHIR resources
5. **Enable Real-time**: Implement Option 1 (Event Streaming) for ongoing updates
6. **Monitor Performance**: Add metrics and alerting

## Support & Troubleshooting

### Common Issues
- **Connection Timeouts**: Increase `IASO_SERVICE_TIMEOUT`
- **Rate Limiting**: Reduce batch size or add delays
- **Memory Issues**: Use streaming for large datasets
- **Authentication Errors**: Verify API keys and service accounts

### Debug Endpoints
```bash
# Check service status
curl http://iaso-api-gateway:8080/health

# Test embeddings (gRPC - use grpcurl or backend client)
grpcurl -plaintext -d '{"texts": ["test"], "model": "bge-m3"}' \
  localhost:50051 embeddings.EmbeddingsService/GenerateEmbeddings

# Query Qdrant directly
curl http://qdrant:6333/collections/fhir_resources/points/search \
  -H "Content-Type: application/json" \
  -d '{"vector": [0.1, 0.2, ...], "limit": 5}'
```