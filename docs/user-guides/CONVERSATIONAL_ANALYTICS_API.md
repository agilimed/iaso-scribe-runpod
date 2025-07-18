# Conversational Analytics API Documentation

## Overview

The Conversational Analytics API provides a natural language interface for querying healthcare data. It uses rule-based intent recognition and template-based SQL generation, enabling healthcare professionals to ask questions in plain English and receive meaningful insights from ClickHouse data.

## Base URL

```
Production: https://api.nexuscare.com/api/insights/chat
Development: http://localhost:3003/api/insights/chat
```

## Authentication

All endpoints require JWT authentication. Include the bearer token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

## Endpoints

### 1. Process Natural Language Query

**POST** `/query`

Process a natural language query and return healthcare analytics insights.

#### Request Body

```json
{
  "query": "Show me total patient count",
  "sessionId": "session_12345",  // Optional: for multi-turn conversations
  "context": {                    // Optional: additional context
    "department": "emergency",
    "timeRange": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    }
  }
}
```

#### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | Yes | Natural language query (max 1000 chars) |
| sessionId | string | No | Session ID for conversation continuity |
| context | object | No | Additional context for query refinement |
| context.department | string | No | Specific department filter |
| context.timeRange | object | No | Time range for the query |

#### Response

```json
{
  "interpretation": "Retrieving total patient count from the system",
  "intent": {
    "type": "aggregation",
    "subType": "count",
    "confidence": 0.95,
    "entities": {
      "metrics": ["patient_count"],
      "aggregations": ["total"],
      "timeRange": {
        "type": "all_time"
      }
    }
  },
  "sql": "SELECT COUNT(DISTINCT patient_id) as total_patients FROM fhir_events WHERE resource_type = 'Patient'",
  "results": [
    {
      "total_patients": 15234
    }
  ],
  "confidence": 0.95,
  "sessionId": "session_12345",
  "timestamp": "2024-01-15T10:30:00Z",
  "processingTime": 245
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| interpretation | string | Human-readable interpretation of the query |
| intent | object | Structured intent analysis |
| sql | string | Generated SQL query (if applicable) |
| results | array | Query results from ClickHouse |
| confidence | number | Confidence score (0-1) |
| sessionId | string | Session ID for conversation tracking |
| timestamp | string | ISO 8601 timestamp |
| processingTime | number | Processing time in milliseconds |

### 2. Get Conversation History

**GET** `/history/:sessionId`

Retrieve the conversation history for a specific session.

#### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sessionId | string | Yes | Session ID (URL parameter) |

#### Response

```json
{
  "sessionId": "session_12345",
  "history": [
    {
      "query": "Show me patient count",
      "response": "Total patient count is 15,234",
      "timestamp": "2024-01-15T10:30:00Z",
      "intent": {
        "type": "aggregation",
        "confidence": 0.95
      }
    },
    {
      "query": "Compare it to last month",
      "response": "Patient count increased by 5.2% compared to last month",
      "timestamp": "2024-01-15T10:31:00Z",
      "intent": {
        "type": "comparison",
        "confidence": 0.92
      }
    }
  ],
  "count": 2,
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### 3. Clear Session Context

**DELETE** `/session/:sessionId`

Clear the conversation context for a session.

#### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sessionId | string | Yes | Session ID (URL parameter) |

#### Response

```json
{
  "message": "Session context cleared successfully",
  "sessionId": "session_12345",
  "timestamp": "2024-01-15T10:40:00Z"
}
```

### 4. Get Query Suggestions

**POST** `/suggestions`

Get contextual query suggestions based on conversation history.

#### Request Body

```json
{
  "sessionId": "session_12345"
}
```

#### Response

```json
{
  "sessionId": "session_12345",
  "suggestions": [
    "Compare patient count by department",
    "Show admission trends over the past week",
    "What's the average length of stay?",
    "Break down by insurance type",
    "Show readmission rates",
    "Compare to same period last year"
  ],
  "count": 6,
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### 5. Get Query Templates

**GET** `/templates`

Get pre-defined query templates based on user role.

#### Response

```json
{
  "templates": [
    {
      "category": "Emergency Department",
      "templates": [
        "Show me ED wait times today",
        "ED patient volume trends this week",
        "Emergency department capacity utilization",
        "Compare ED metrics to last month"
      ]
    },
    {
      "category": "Quality Metrics",
      "templates": [
        "Patient satisfaction scores by department",
        "Infection rates trending analysis",
        "Mortality rates for ICU patients",
        "Patient safety indicators dashboard"
      ]
    },
    {
      "category": "Financial Analytics",
      "templates": [
        "Cost per procedure analysis",
        "Revenue vs budget comparison",
        "Supply costs by department",
        "Profit margins by service line"
      ]
    }
  ],
  "count": 3,
  "userRole": "admin",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### 6. Health Check

**GET** `/health`

Check the health status of the conversational analytics service and its dependencies.

#### Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:35:00Z",
  "services": {
    "llm": "healthy",
    "conversationalService": "available"
  },
  "capabilities": [
    "natural_language_processing",
    "intent_recognition",
    "sql_generation",
    "multi_turn_conversation",
    "healthcare_analytics"
  ]
}
```

## Intent Types

The system recognizes various intent types:

| Intent Type | Description | Example Queries |
|-------------|-------------|-----------------|
| aggregation | Count, sum, average queries | "Total patient count", "Average length of stay" |
| trend_analysis | Time-based trends | "Show admission trends this week" |
| comparison | Comparative analysis | "Compare this month to last month" |
| filtering | Filtered queries | "Show ICU patients only" |
| distribution | Breakdown analysis | "Patient count by department" |
| real_time | Current status queries | "How many beds available now?" |

## Error Responses

All errors follow a consistent format:

```json
{
  "error": "Failed to process query",
  "message": "Specific error message",
  "details": {
    "code": "INTENT_RECOGNITION_FAILED",
    "context": "Additional error context"
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_REQUEST | 400 | Invalid request format or parameters |
| UNAUTHORIZED | 401 | Missing or invalid authentication token |
| INTENT_RECOGNITION_FAILED | 422 | Failed to understand the query intent |
| SERVICE_UNAVAILABLE | 503 | LLM service is down |
| INTERNAL_ERROR | 500 | Internal server error |

## Multi-turn Conversation Support

The API supports multi-turn conversations by maintaining context across queries:

1. **First Query**: "Show me patient count"
   - System understands this is about total patients

2. **Follow-up**: "Compare it to last month"
   - System remembers "it" refers to patient count

3. **Further Refinement**: "Break it down by department"
   - System maintains context of patient count comparison

### Best Practices for Multi-turn Conversations

1. Always use the same `sessionId` for related queries
2. Sessions expire after 30 minutes of inactivity
3. Clear sessions explicitly when starting new topics
4. Maximum context window is last 10 queries

## Integration Examples

### JavaScript/TypeScript

```typescript
// Initialize the client
const conversationalAnalytics = {
  baseUrl: 'https://api.nexuscare.com/api/insights/chat',
  token: 'your-jwt-token'
};

// Simple query
async function askQuestion(query: string) {
  const response = await fetch(`${conversationalAnalytics.baseUrl}/query`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${conversationalAnalytics.token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query })
  });
  
  return response.json();
}

// Multi-turn conversation
class ConversationSession {
  private sessionId: string;
  
  constructor() {
    this.sessionId = `session_${Date.now()}`;
  }
  
  async ask(query: string) {
    const response = await fetch(`${conversationalAnalytics.baseUrl}/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${conversationalAnalytics.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query,
        sessionId: this.sessionId
      })
    });
    
    return response.json();
  }
  
  async getHistory() {
    const response = await fetch(
      `${conversationalAnalytics.baseUrl}/history/${this.sessionId}`,
      {
        headers: {
          'Authorization': `Bearer ${conversationalAnalytics.token}`
        }
      }
    );
    
    return response.json();
  }
}

// Usage
const session = new ConversationSession();
const result1 = await session.ask("Show me patient count");
const result2 = await session.ask("Compare it to last month");
```

### Python

```python
import requests
from datetime import datetime

class ConversationalAnalyticsClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self.session_id = f"session_{int(datetime.now().timestamp())}"
    
    def query(self, query_text, context=None):
        payload = {
            'query': query_text,
            'sessionId': self.session_id
        }
        if context:
            payload['context'] = context
        
        response = requests.post(
            f"{self.base_url}/query",
            json=payload,
            headers=self.headers
        )
        return response.json()
    
    def get_history(self):
        response = requests.get(
            f"{self.base_url}/history/{self.session_id}",
            headers=self.headers
        )
        return response.json()

# Usage
client = ConversationalAnalyticsClient(
    'https://api.nexuscare.com/api/insights/chat',
    'your-jwt-token'
)

# Ask questions
result = client.query("Show me ED wait times today")
print(f"Answer: {result['interpretation']}")
print(f"Data: {result['results']}")

# Follow-up question
follow_up = client.query("How does that compare to our target?")
```

## Rate Limiting

- **Rate Limit**: 100 requests per minute per user
- **Burst Limit**: 20 requests per second
- **Headers**: Rate limit info returned in response headers
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

## Performance Considerations

1. **Query Complexity**: Complex queries may take 1-3 seconds
2. **Caching**: Results are cached for 5 minutes for identical queries
3. **Batch Queries**: For multiple related queries, use sessions
4. **Timeouts**: Request timeout is 30 seconds

## Security

1. **Authentication**: All requests require valid JWT tokens
2. **Authorization**: Queries respect user's data access permissions
3. **Data Filtering**: Results automatically filtered by tenant/organization
4. **Audit Logging**: All queries are logged for compliance
5. **PII Protection**: Patient identifiers are never returned

## Supported Query Patterns

### Demographics
- "Total patient count"
- "Patient distribution by age group"
- "Gender breakdown of patients"

### Operations
- "Current ED wait times"
- "Bed occupancy rate"
- "Staff utilization by department"

### Clinical
- "Readmission rates"
- "Average length of stay"
- "Infection rates by unit"

### Financial
- "Revenue this month"
- "Cost per patient by department"
- "Insurance claim denial rates"

### Quality
- "Patient satisfaction scores"
- "Clinical outcome metrics"
- "Safety incident trends"

## Webhooks

Configure webhooks to receive notifications about:
- Query failures
- Unusual query patterns
- Session completions

Contact support to set up webhooks for your organization.

## Support

For API support:
- Email: api-support@nexuscare.com
- Documentation: https://docs.nexuscare.com/api/conversational
- Status Page: https://status.nexuscare.com

## Changelog

### Version 2.0 (Current)
- Added multi-turn conversation support
- Improved intent recognition with rule-based approach
- Added LLM integration for enhanced capabilities
- Enhanced healthcare-specific understanding

### Version 1.0
- Initial release with basic NLP
- Simple query processing
- Limited intent types