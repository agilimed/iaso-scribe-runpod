# IASO Medical AI Services - Developer Guide

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  (Claude Desktop, VS Code, Python Apps, REST APIs, EHR Systems) │
└────────────────────────┬────────────────────────────────────────┘
                         │ MCP Protocol
┌────────────────────────┴────────────────────────────────────────┐
│                    MCP Server Layer                              │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌──────────────────┐   │
│ │ Whisper MCP     │ │ Phi-4 MCP       │ │ IASO Orchestrator│   │
│ │ Server          │ │ Server          │ │ (Agent + Router) │   │
│ └────────┬────────┘ └────────┬────────┘ └────────┬─────────┘   │
└──────────┼───────────────────┼───────────────────┼─────────────┘
           │                   │                   │
┌──────────┴───────────────────┴───────────────────┴─────────────┐
│                    RunPod Endpoints Layer                        │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌──────────────────┐   │
│ │ Whisper Medium  │ │ Phi-4 Reasoning │ │ Future Services  │   │
│ │ (Transcription) │ │ (Medical AI)    │ │ (Lab, Rx, etc)   │   │
│ └─────────────────┘ └─────────────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## File Structure

```
iaso-scribe-runpod/
├── mcp/                              # MCP Implementation
│   ├── whisper_mcp_server.py        # Whisper service MCP server
│   ├── phi4_mcp_server.py           # Phi-4 service MCP server
│   ├── iaso_orchestrator.py         # Intelligent orchestration agent
│   ├── requirements.txt             # Python dependencies
│   ├── claude_desktop_config.json   # Claude Desktop configuration
│   └── example_usage.py             # Usage examples
│
├── whisper/                         # Whisper Service
│   ├── handler.py                   # RunPod handler for Whisper
│   └── Dockerfile                   # Container definition
│
├── phi4/                            # Phi-4 Service
│   ├── handler.py                   # RunPod handler for Phi-4
│   ├── handler_streaming.py         # Streaming support
│   ├── response_parser.py           # Tag parsing utilities
│   └── medical_summary_template.py  # Prompt templates
│
└── docs/mcp/                        # Documentation
    ├── USER_GUIDE.md               # End-user documentation
    └── DEVELOPER_GUIDE.md          # This file
```

## Core Components

### 1. MCP Servers

#### Whisper MCP Server (`mcp/whisper_mcp_server.py`)

**Purpose**: Exposes Whisper transcription capabilities via MCP

**Key Classes**:
- `WhisperMCPServer`: Main server class
- `TranscriptionRequest`: Request validation model

**Available Tools**:
```python
- transcribe_audio(audio_url, language, return_segments)
- transcribe_medical_dictation(audio_url, speaker_info)
- detect_audio_language(audio_url)
```

**Data Flow**:
```
MCP Client → MCP Server → RunPod API → Whisper Endpoint → Response
```

#### Phi-4 MCP Server (`mcp/phi4_mcp_server.py`)

**Purpose**: Exposes Phi-4 medical reasoning capabilities via MCP

**Key Classes**:
- `Phi4MCPServer`: Main server class
- Response parser for `<think>` and `<solution>` tags

**Available Tools**:
```python
- generate_soap_note(text, include_reasoning)
- create_clinical_summary(text, max_words, focus_areas)
- extract_medical_insights(text, insight_types)
- analyze_clinical_case(case_text, analysis_type)
- generate_medical_report(clinical_data, report_type, specialty)
```

**Tag-Based Output**:
```xml
<think>
  Clinical reasoning and analysis steps
</think>
<solution>
  Final formatted output (SOAP note, summary, etc.)
</solution>
```

### 2. Orchestrator

#### IASO Orchestrator (`mcp/iaso_orchestrator.py`)

**Purpose**: Intelligent agent that coordinates multiple services

**Key Components**:
- `ServiceRegistry`: Tracks available services and capabilities
- `WorkflowPlanner`: Plans multi-step workflows
- `IASOOrchestrator`: Main orchestration logic

**Workflow Planning Algorithm**:
```python
def plan_workflow(inputs, required_outputs):
    1. Identify available data from inputs
    2. Determine missing data needed for outputs
    3. Find services that can produce missing data
    4. Order steps based on dependencies
    5. Return executable workflow plan
```

### 3. RunPod Handlers

#### Whisper Handler (`whisper/handler.py`)

**Key Functions**:
- Model initialization with GPU detection
- Audio processing with VAD filtering
- Segment extraction for timestamps

#### Phi-4 Handler (`phi4/handler.py`)

**Key Features**:
- 32K context window support
- Tag-based structured output
- Multiple prompt types (medical_insights, soap, summary)
- Automatic tag closure for incomplete responses

## Data Flow Examples

### Example 1: Direct Service Call

```
1. Client calls Phi-4 MCP Server
   → tool: "generate_soap_note"
   → arguments: {text: "...", include_reasoning: true}

2. MCP Server processes request
   → Validates input
   → Calls RunPod endpoint

3. RunPod endpoint executes
   → Loads Phi-4 model
   → Generates response with tags
   → Returns structured output

4. MCP Server parses response
   → Extracts <think> and <solution> sections
   → Formats final response

5. Client receives structured result
   → soap_note: "SUBJECTIVE:..."
   → clinical_reasoning: "Step 1:..."
```

### Example 2: Orchestrated Workflow

```
1. Client calls Orchestrator
   → tool: "process_medical_dictation"
   → arguments: {audio_url: "...", outputs: ["soap_note"]}

2. Orchestrator plans workflow
   → Step 1: Whisper transcription needed
   → Step 2: Phi-4 SOAP generation needed

3. Execute Step 1
   → Call Whisper MCP → RunPod → Transcription

4. Execute Step 2
   → Pass transcription to Phi-4 MCP → RunPod → SOAP

5. Return combined results
   → transcription: "..."
   → soap_note: "..."
```

## Implementation Details

### Service Registration

```python
# In iaso_orchestrator.py
self.services = {
    "whisper": {
        "capabilities": [ServiceCapability.TRANSCRIPTION],
        "endpoint": "whisper_mcp_server",
        "status": "active"
    },
    "phi4": {
        "capabilities": [
            ServiceCapability.MEDICAL_REASONING,
            ServiceCapability.SOAP_GENERATION,
            ServiceCapability.CLINICAL_SUMMARY
        ],
        "endpoint": "phi4_mcp_server",
        "status": "active"
    }
}
```

### Adding New Services

1. **Create MCP Server**:
```python
# new_service_mcp_server.py
class NewServiceMCPServer:
    def __init__(self):
        self.server = Server("new-medical-service")
        self.setup_tools()
    
    def setup_tools(self):
        @self.server.list_tools()
        async def list_tools():
            return [Tool(...)]
```

2. **Register with Orchestrator**:
```python
# In ServiceRegistry
"new_service": {
    "capabilities": [ServiceCapability.NEW_CAPABILITY],
    "endpoint": "new_service_mcp_server",
    "status": "active"
}
```

3. **Update Workflow Planner**:
```python
# Add output mappings
"new_output": {
    "capability": ServiceCapability.NEW_CAPABILITY,
    "required_inputs": ["text"],
    "outputs": ["new_result"]
}
```

### Error Handling

```python
try:
    result = await self.call_runpod_endpoint(payload)
    if "error" in result:
        return {"error": result["error"], "service": "whisper"}
except httpx.TimeoutError:
    return {"error": "Service timeout", "retry_after": 30}
except Exception as e:
    logger.error(f"Service error: {str(e)}")
    return {"error": "Internal service error"}
```

### Streaming Support

```python
# In handler_streaming.py
async def stream_response(prompt, max_tokens):
    stream = phi_model(prompt, stream=True)
    for output in stream:
        token = output['choices'][0]['text']
        yield {
            "token": token,
            "accumulated_text": accumulated_text,
            "tokens_generated": total_tokens
        }
```

## Testing

### Unit Tests

```python
# test_whisper_mcp.py
async def test_transcribe_audio():
    server = WhisperMCPServer()
    result = await server.transcribe_audio({
        "audio_url": "test.wav",
        "language": "en"
    })
    assert "transcription" in result
    assert result["language"] == "en"
```

### Integration Tests

```python
# test_orchestrator.py
async def test_medical_workflow():
    orchestrator = IASOOrchestrator()
    result = await orchestrator.process_medical_dictation({
        "audio_url": "test.wav",
        "outputs": ["transcription", "soap_note"]
    })
    assert result["status"] == "completed"
    assert "soap_note" in result["results"]
```

### Load Testing

```python
# Load test with concurrent requests
async def load_test():
    tasks = []
    for i in range(100):
        task = client.call_tool("generate_soap_note", {...})
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    success_rate = sum(1 for r in results if "error" not in r) / len(results)
```

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r mcp/requirements.txt

# Set environment variables
export RUNPOD_API_KEY="your_key"
export WHISPER_ENDPOINT_ID="rntxttrdl8uv3i"
export PHI4_ENDPOINT_ID="tmmwa4q8ax5sg4"

# Run MCP server
python mcp/iaso_orchestrator.py
```

### Production Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  whisper-mcp:
    build: ./mcp
    environment:
      - RUNPOD_API_KEY=${RUNPOD_API_KEY}
      - WHISPER_ENDPOINT_ID=${WHISPER_ENDPOINT_ID}
    command: python whisper_mcp_server.py
    
  phi4-mcp:
    build: ./mcp
    environment:
      - RUNPOD_API_KEY=${RUNPOD_API_KEY}
      - PHI4_ENDPOINT_ID=${PHI4_ENDPOINT_ID}
    command: python phi4_mcp_server.py
    
  orchestrator:
    build: ./mcp
    environment:
      - RUNPOD_API_KEY=${RUNPOD_API_KEY}
    command: python iaso_orchestrator.py
```

### Monitoring

```python
# Add to MCP servers
import structlog
logger = structlog.get_logger()

async def call_tool(name, arguments):
    start_time = time.time()
    try:
        result = await self._call_tool_impl(name, arguments)
        logger.info("tool_called", 
                   tool=name, 
                   duration=time.time()-start_time,
                   status="success")
        return result
    except Exception as e:
        logger.error("tool_error",
                    tool=name,
                    error=str(e),
                    duration=time.time()-start_time)
        raise
```

## Performance Optimization

### Caching

```python
# Add caching layer
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_cached_transcription(audio_hash):
    # Check cache before calling RunPod
    return await call_runpod_endpoint(...)
```

### Connection Pooling

```python
# Reuse HTTP connections
class ServiceClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=100),
            timeout=httpx.Timeout(300.0)
        )
```

### Batch Processing

```python
# Process multiple requests efficiently
async def batch_process(requests):
    # Group by service type
    grouped = defaultdict(list)
    for req in requests:
        grouped[req.service].append(req)
    
    # Process in parallel
    tasks = []
    for service, reqs in grouped.items():
        task = process_service_batch(service, reqs)
        tasks.append(task)
    
    return await asyncio.gather(*tasks)
```

## Security Considerations

### API Key Management

```python
# Use environment variables
API_KEY = os.environ.get("RUNPOD_API_KEY")
if not API_KEY:
    raise ValueError("RUNPOD_API_KEY not set")

# Never log API keys
headers = {"Authorization": f"Bearer {API_KEY}"}
logger.info("Making request", headers={"Authorization": "Bearer ***"})
```

### Input Validation

```python
# Validate all inputs
from pydantic import validator

class TranscriptionRequest(BaseModel):
    audio_url: str
    
    @validator('audio_url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Invalid URL scheme')
        return v
```

### Rate Limiting

```python
# Implement rate limiting
from asyncio import Semaphore

class RateLimiter:
    def __init__(self, max_concurrent=10):
        self.semaphore = Semaphore(max_concurrent)
    
    async def __aenter__(self):
        await self.semaphore.acquire()
    
    async def __aexit__(self, *args):
        self.semaphore.release()

# Usage
rate_limiter = RateLimiter(max_concurrent=10)
async with rate_limiter:
    result = await call_service(...)
```

## Troubleshooting

### Common Issues

1. **Connection Timeouts**
   - Increase timeout values
   - Check RunPod endpoint status
   - Verify network connectivity

2. **Tag Parsing Errors**
   - Check prompt templates
   - Verify model is using correct format
   - Add fallback parsing logic

3. **Memory Issues**
   - Reduce batch sizes
   - Implement streaming for large responses
   - Monitor model memory usage

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug endpoints
@server.list_tools()
async def list_tools():
    if os.environ.get("DEBUG"):
        tools.append(Tool(
            name="debug_info",
            description="Get debug information"
        ))
```

## Contributing

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all functions
- Keep functions under 50 lines

### Testing Requirements

- Unit tests for all new functions
- Integration tests for new workflows
- Load test for performance-critical paths
- Documentation for new features

### Pull Request Process

1. Create feature branch
2. Write tests
3. Implement feature
4. Update documentation
5. Submit PR with description

## Resources

- [MCP Specification](https://github.com/anthropics/mcp)
- [RunPod API Docs](https://docs.runpod.ai)
- [IASO GitHub Repository](https://github.com/your-repo)
- [Support Discord](https://discord.gg/your-discord)