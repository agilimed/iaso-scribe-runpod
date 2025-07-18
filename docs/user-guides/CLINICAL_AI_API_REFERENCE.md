# Clinical AI API Reference

## Overview

This document provides comprehensive API documentation for all Clinical AI services. Each service exposes RESTful APIs with JSON request/response formats and follows OpenAPI 3.0 specifications.

## Authentication

All services support the following authentication methods:

### JWT Bearer Token (Recommended)
```http
Authorization: Bearer <jwt-token>
```

### API Key (Legacy)
```http
X-API-Key: <api-key>
```

## Service Endpoints

### Base URLs
- **Clinical AI Service**: `http://localhost:8002` (Development) / `https://api.nexuscare.ai/clinical` (Production)
- **Terminology Service**: `http://localhost:8001` (Development) / `https://api.nexuscare.ai/terminology` (Production)
- **Knowledge Service**: `http://localhost:8004` (Development) / `https://api.nexuscare.ai/knowledge` (Production)
- **Template Service**: `http://localhost:8003` (Development) / `https://api.nexuscare.ai/templates` (Production)
- **SLM Service**: `http://localhost:8007` (Development) / `https://api.nexuscare.ai/slm` (Production)

---

## Clinical AI Service API

### Process Clinical Text

**Endpoint**: `POST /process`

**Description**: Process clinical text to extract medical entities, generate embeddings, and perform NLP analysis.

**Request Body**:
```json
{
  "text": "Patient presents with chest pain and shortness of breath. History of diabetes mellitus type 2.",
  "enable_medcat": true,
  "enable_clinical_bert": true,
  "enable_spacy": true,
  "perform_summarization": false,
  "return_embeddings": true,
  "fhir_mapping": true,
  "processing_options": {
    "chunk_size": 512,
    "overlap": 50,
    "aggregation_method": "weighted_average"
  }
}
```

**Response**:
```json
{
  "processed_text": "Patient presents with chest pain and shortness of breath. History of diabetes mellitus type 2.",
  "entities": [
    {
      "text": "chest pain",
      "label": "SYMPTOM",
      "start": 20,
      "end": 30,
      "confidence": 0.95,
      "cui": "C0008031",
      "semantic_type": "sosy",
      "fhir_code": {
        "system": "http://snomed.info/sct",
        "code": "29857009",
        "display": "Chest pain"
      }
    },
    {
      "text": "diabetes mellitus type 2",
      "label": "CONDITION",
      "start": 65,
      "end": 89,
      "confidence": 0.98,
      "cui": "C0011860",
      "semantic_type": "dsyn",
      "fhir_code": {
        "system": "http://snomed.info/sct",
        "code": "44054006",
        "display": "Diabetes mellitus type 2"
      }
    }
  ],
  "embeddings": {
    "clinical_bert": [0.1234, -0.5678, 0.9012, ...],
    "aggregation_method": "weighted_average",
    "dimension": 768
  },
  "spacy_analysis": {
    "sentences": 2,
    "tokens": 15,
    "pos_tags": ["NOUN", "VERB", ...],
    "dependencies": [...]
  },
  "processing_metadata": {
    "processing_time_ms": 1250,
    "model_versions": {
      "medcat": "1.16.0",
      "clinical_bert": "emilyalsentzer/Bio_ClinicalBERT",
      "spacy": "en_core_sci_lg"
    },
    "chunks_processed": 1
  }
}
```

### Generate ClinicalBERT Embeddings

**Endpoint**: `POST /clinical-bert/embeddings`

**Description**: Generate embeddings for clinical text using ClinicalBERT models.

**Request Body**:
```json
{
  "texts": [
    "Patient has diabetes",
    "Blood pressure elevated"
  ],
  "model_name": "emilyalsentzer/Bio_ClinicalBERT",
  "normalize": true,
  "batch_processing": true
}
```

**Response**:
```json
{
  "embeddings": [
    [0.1234, -0.5678, 0.9012, ...],
    [0.2345, -0.6789, 0.8901, ...]
  ],
  "model_info": {
    "model_name": "emilyalsentzer/Bio_ClinicalBERT",
    "dimension": 768,
    "max_length": 512
  },
  "processing_metadata": {
    "processing_time_ms": 450,
    "texts_processed": 2,
    "chunks_created": 2
  }
}
```

### Calculate Text Similarity

**Endpoint**: `POST /clinical-bert/similarity`

**Description**: Calculate semantic similarity between clinical texts.

**Request Body**:
```json
{
  "text1": "Patient has diabetes mellitus",
  "text2": "Subject diagnosed with diabetes",
  "similarity_metric": "cosine"
}
```

**Response**:
```json
{
  "similarity_score": 0.8745,
  "similarity_metric": "cosine",
  "embeddings": {
    "text1": [0.1234, -0.5678, ...],
    "text2": [0.2345, -0.6789, ...]
  },
  "processing_metadata": {
    "processing_time_ms": 320
  }
}
```

### Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "dependencies": {
    "postgres": {
      "status": "healthy",
      "response_time_ms": 12
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 5
    },
    "medcat_model": {
      "status": "loaded",
      "model_version": "1.16.0",
      "memory_usage_mb": 1250
    },
    "clinical_bert": {
      "status": "loaded",
      "model_name": "emilyalsentzer/Bio_ClinicalBERT",
      "memory_usage_mb": 2048
    }
  }
}
```

---

## Terminology Service API

### Search Medical Concepts

**Endpoint**: `GET /search`

**Parameters**:
- `term` (required): Search term
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)
- `vocabularies` (optional): Filter by vocabularies (comma-separated)
- `semantic_types` (optional): Filter by semantic types (comma-separated)
- `sources` (optional): Filter by sources (comma-separated)

**Example Request**:
```http
GET /search?term=diabetes&limit=10&vocabularies=SNOMEDCT_US,ICD10CM&semantic_types=dsyn
```

**Response**:
```json
{
  "results": [
    {
      "cui": "C0011860",
      "preferred_name": "Diabetes Mellitus, Type 2",
      "semantic_type": "dsyn",
      "score": 0.95,
      "vocabularies": ["SNOMEDCT_US", "ICD10CM"],
      "codes": [
        {
          "vocabulary": "SNOMEDCT_US",
          "code": "44054006",
          "term": "Type 2 diabetes mellitus"
        },
        {
          "vocabulary": "ICD10CM",
          "code": "E11",
          "term": "Type 2 diabetes mellitus"
        }
      ]
    }
  ],
  "total_results": 156,
  "search_metadata": {
    "query": "diabetes",
    "processing_time_ms": 45,
    "filters_applied": {
      "vocabularies": ["SNOMEDCT_US", "ICD10CM"],
      "semantic_types": ["dsyn"]
    }
  }
}
```

### Pattern Matching in Text

**Endpoint**: `POST /pattern_match`

**Description**: Find and extract clinical terms from unstructured text.

**Request Body**:
```json
{
  "text": "Patient presents with acute myocardial infarction and takes metformin 500mg daily.",
  "match_options": {
    "minimum_score": 0.7,
    "max_matches": 50,
    "case_sensitive": false,
    "vocabularies": ["SNOMEDCT_US", "RXNORM"]
  }
}
```

**Response**:
```json
{
  "matches": [
    {
      "text": "acute myocardial infarction",
      "start": 20,
      "end": 47,
      "cui": "C0155626",
      "preferred_name": "Acute myocardial infarction",
      "score": 0.98,
      "semantic_type": "dsyn",
      "codes": [
        {
          "vocabulary": "SNOMEDCT_US",
          "code": "57054005",
          "term": "Acute myocardial infarction"
        }
      ]
    },
    {
      "text": "metformin",
      "start": 59,
      "end": 68,
      "cui": "C0025598",
      "preferred_name": "Metformin",
      "score": 1.0,
      "semantic_type": "orch",
      "codes": [
        {
          "vocabulary": "RXNORM",
          "code": "6809",
          "term": "Metformin"
        }
      ]
    }
  ],
  "processing_metadata": {
    "text_length": 84,
    "matches_found": 2,
    "processing_time_ms": 125
  }
}
```

---

## Knowledge Service API

### Get Concept Codes

**Endpoint**: `GET /api/v1/concepts/{cui}/codes`

**Description**: Retrieve all codes associated with a medical concept.

**Example Request**:
```http
GET /api/v1/concepts/C0011860/codes
```

**Response**:
```json
{
  "cui": "C0011860",
  "preferred_name": "Diabetes Mellitus, Type 2",
  "codes": [
    {
      "vocabulary": "SNOMEDCT_US",
      "code": "44054006",
      "term": "Type 2 diabetes mellitus",
      "is_preferred": true
    },
    {
      "vocabulary": "ICD10CM",
      "code": "E11",
      "term": "Type 2 diabetes mellitus",
      "is_preferred": true
    },
    {
      "vocabulary": "ICD9CM",
      "code": "250.00",
      "term": "Diabetes mellitus without mention of complication, type II or unspecified type, not stated as uncontrolled",
      "is_preferred": false
    }
  ],
  "metadata": {
    "total_codes": 15,
    "vocabularies_count": 8,
    "last_updated": "2024-01-15T00:00:00Z"
  }
}
```

### Get Concept Relationships

**Endpoint**: `GET /api/v1/concepts/{cui}/relationships`

**Description**: Retrieve hierarchical and semantic relationships for a concept.

**Parameters**:
- `relationship_types` (optional): Filter by relationship types
- `include_inverse` (optional): Include inverse relationships (default: false)

**Example Request**:
```http
GET /api/v1/concepts/C0011860/relationships?relationship_types=isa,part_of
```

**Response**:
```json
{
  "cui": "C0011860",
  "preferred_name": "Diabetes Mellitus, Type 2",
  "relationships": {
    "parents": [
      {
        "cui": "C0011849",
        "preferred_name": "Diabetes Mellitus",
        "relationship_type": "isa",
        "distance": 1
      }
    ],
    "children": [
      {
        "cui": "C0271650",
        "preferred_name": "Impaired glucose tolerance",
        "relationship_type": "isa",
        "distance": 1
      }
    ],
    "siblings": [
      {
        "cui": "C0011854",
        "preferred_name": "Diabetes Mellitus, Type 1",
        "relationship_type": "sibling",
        "distance": 2
      }
    ]
  },
  "metadata": {
    "total_relationships": 25,
    "relationship_types": ["isa", "part_of", "associated_with"],
    "hierarchy_depth": 4
  }
}
```

---

## Template Service API

### Create Template

**Endpoint**: `POST /templates`

**Description**: Create a new FHIR Questionnaire template.

**Request Body**:
```json
{
  "questionnaire": {
    "resourceType": "Questionnaire",
    "id": "diabetes-assessment",
    "title": "Diabetes Assessment Questionnaire",
    "status": "active",
    "item": [
      {
        "linkId": "1",
        "text": "Blood glucose level",
        "type": "decimal",
        "required": true
      },
      {
        "linkId": "2",
        "text": "Medication adherence",
        "type": "choice",
        "answerOption": [
          {"valueString": "Excellent"},
          {"valueString": "Good"},
          {"valueString": "Poor"}
        ]
      }
    ]
  },
  "metadata": {
    "encounter_type": "routine_checkup",
    "tags": ["diabetes", "assessment"],
    "version": "1.0.0",
    "author": "Dr. Smith"
  }
}
```

**Response**:
```json
{
  "id": "template-12345",
  "questionnaire": {
    "resourceType": "Questionnaire",
    "id": "diabetes-assessment",
    "title": "Diabetes Assessment Questionnaire",
    "status": "active",
    "item": [...]
  },
  "metadata": {
    "encounter_type": "routine_checkup",
    "tags": ["diabetes", "assessment"],
    "version": "1.0.0",
    "author": "Dr. Smith",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "validation": {
    "is_valid": true,
    "fhir_version": "4.0.1",
    "validation_messages": []
  }
}
```

### List Templates

**Endpoint**: `GET /templates`

**Parameters**:
- `encounter_type` (optional): Filter by encounter type
- `tags` (optional): Filter by tags (comma-separated)
- `limit` (optional): Number of results (default: 20)
- `offset` (optional): Pagination offset

**Example Request**:
```http
GET /templates?encounter_type=routine_checkup&tags=diabetes&limit=10
```

**Response**:
```json
{
  "templates": [
    {
      "id": "template-12345",
      "title": "Diabetes Assessment Questionnaire",
      "encounter_type": "routine_checkup",
      "tags": ["diabetes", "assessment"],
      "version": "1.0.0",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 45,
    "limit": 10,
    "offset": 0,
    "has_more": true
  }
}
```

---

## SLM Service API

### Process with LLM

**Endpoint**: `POST /process`

**Description**: Process text using large language models for various clinical tasks.

**Request Body**:
```json
{
  "text": "Patient is a 65-year-old male with history of diabetes and hypertension. Presenting with chest pain...",
  "task_type": "clinical_summary",
  "llm_config": {
    "model": "phi-3-medium",
    "max_tokens": 500,
    "temperature": 0.3
  },
  "include_medcat_entities": true,
  "context": {
    "patient_age": 65,
    "patient_gender": "male"
  }
}
```

**Response**:
```json
{
  "generated_text": "**Clinical Summary:**\n\n65-year-old male patient with significant past medical history of diabetes mellitus and hypertension presents with acute chest pain. Given the patient's cardiovascular risk factors, immediate cardiac evaluation is warranted...",
  "task_type": "clinical_summary",
  "llm_metadata": {
    "model_used": "phi-3-medium",
    "tokens_generated": 156,
    "processing_time_ms": 2500,
    "confidence_score": 0.87
  },
  "entities_used": [
    {
      "text": "diabetes",
      "cui": "C0011847",
      "included_in_prompt": true
    },
    {
      "text": "hypertension",
      "cui": "C0020538",
      "included_in_prompt": true
    }
  ]
}
```

### Stream Processing

**Endpoint**: `POST /stream-process`

**Description**: Stream LLM responses in real-time.

**Request Body**: Same as `/process` endpoint

**Response**: Server-Sent Events (SSE) stream
```
data: {"type": "start", "task_id": "task-12345"}

data: {"type": "token", "content": "**Clinical", "position": 0}

data: {"type": "token", "content": " Summary:**", "position": 1}

data: {"type": "complete", "final_text": "**Clinical Summary:**\n\n65-year-old male...", "metadata": {...}}
```

---

## Error Responses

All services follow a consistent error response format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The provided text exceeds the maximum length limit",
    "details": {
      "field": "text",
      "max_length": 50000,
      "provided_length": 65000
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req-12345"
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR` (400): Invalid request parameters
- `AUTHENTICATION_ERROR` (401): Invalid or missing authentication
- `AUTHORIZATION_ERROR` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `RATE_LIMIT_EXCEEDED` (429): Too many requests
- `INTERNAL_ERROR` (500): Internal server error
- `SERVICE_UNAVAILABLE` (503): Service temporarily unavailable

## Rate Limiting

All endpoints are subject to rate limiting:

- **Authenticated users**: 1000 requests per hour
- **Unauthenticated users**: 100 requests per hour
- **Bulk processing endpoints**: 100 requests per hour

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1642252800
```

## SDK Examples

### Python SDK Example

```python
import requests
from typing import List, Dict

class ClinicalAIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def process_clinical_text(self, text: str, **options) -> Dict:
        """Process clinical text with MedCAT and ClinicalBERT."""
        payload = {"text": text, **options}
        response = requests.post(
            f"{self.base_url}/process",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def search_concepts(self, term: str, limit: int = 20) -> Dict:
        """Search medical concepts in terminology service."""
        params = {"term": term, "limit": limit}
        response = requests.get(
            f"{self.base_url}/search",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = ClinicalAIClient("https://api.nexuscare.ai/clinical", "your-api-key")
result = client.process_clinical_text("Patient has diabetes mellitus type 2")
```

This API reference provides comprehensive documentation for integrating with all Clinical AI services.