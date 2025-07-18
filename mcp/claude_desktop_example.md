# Using IASO MCP Services with Claude Desktop

## Quick Start

### 1. Configure Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "iaso-orchestrator": {
      "command": "python",
      "args": ["/path/to/iaso-scribe-runpod/mcp/iaso_orchestrator.py"],
      "env": {
        "RUNPOD_API_KEY": "your_runpod_api_key_here",
        "WHISPER_ENDPOINT_ID": "rntxttrdl8uv3i",
        "PHI4_ENDPOINT_ID": "tmmwa4q8ax5sg4"
      }
    }
  }
}
```

### 2. Restart Claude Desktop

After updating the configuration, restart Claude Desktop to load the MCP server.

### 3. Example Conversations

#### Medical Dictation Processing
```
You: Process this medical dictation audio and create a SOAP note:
https://example.com/dr-smith-patient-johnson.wav

Claude: I'll process that medical dictation for you using the IASO services.
[Uses process_medical_dictation tool]

Here's the transcription and SOAP note:

**Transcription:**
"Patient is a 45-year-old male presenting with chest pain..."

**SOAP Note:**
SUBJECTIVE:
• Chief complaint: Chest pain x 2 hours
• Character: Crushing sensation, radiating to left arm
...
```

#### Clinical Analysis
```
You: Analyze this patient note and extract key medical insights:
[Paste clinical note]

Claude: I'll analyze this clinical note for key medical insights.
[Uses analyze_patient_encounter tool]

**Key Findings:**
- Medications: Metformin 1000mg BID, Lisinopril 10mg daily
- Diagnoses: Type 2 Diabetes, Hypertension
- Symptoms: Chest pain (8/10), dyspnea, diaphoresis
- Risk Factors: Cardiovascular disease risk elevated
```

### 4. Available Commands

With the orchestrator connected, you can ask Claude to:

1. **Transcribe Medical Audio**
   - "Transcribe this medical dictation"
   - "What language is this audio in?"

2. **Generate Clinical Documentation**
   - "Create a SOAP note from this text"
   - "Summarize this consultation in 500 words"
   - "Generate a discharge summary"

3. **Extract Medical Information**
   - "What medications is the patient taking?"
   - "Extract all diagnoses from this note"
   - "Identify critical findings"

4. **Analyze Clinical Cases**
   - "Provide differential diagnosis"
   - "Assess clinical risks"
   - "Suggest treatment plan"

### 5. Custom Workflows

You can also create custom workflows:

```
You: First transcribe this audio, then extract medications from it, 
and finally create a medication reconciliation report.

Claude: I'll create a custom workflow to process your request.
[Uses execute_custom_workflow with multiple steps]

Step 1: Transcription complete
Step 2: Medications extracted:
- Aspirin 81mg daily
- Atorvastatin 40mg daily
- Metoprolol 50mg BID

Step 3: Medication Reconciliation Report:
[Detailed report...]
```

## Troubleshooting

### MCP Server Not Loading
1. Check the path to the Python script is correct
2. Ensure RUNPOD_API_KEY is set
3. Check Claude Desktop logs for errors

### Service Errors
1. Verify RunPod endpoints are active
2. Check API key has proper permissions
3. Ensure audio URLs are accessible

### Performance Issues
1. First calls may be slower (cold start)
2. Large audio files take longer to process
3. Complex analyses may take 10-30 seconds

## Advanced Usage

### Using Individual Services

You can also configure individual MCP servers:

```json
{
  "mcpServers": {
    "whisper-service": {
      "command": "python",
      "args": ["/path/to/whisper_mcp_server.py"],
      "env": {"RUNPOD_API_KEY": "..."}
    },
    "phi4-service": {
      "command": "python",
      "args": ["/path/to/phi4_mcp_server.py"],
      "env": {"RUNPOD_API_KEY": "..."}
    }
  }
}
```

This gives you more granular control over which services to use.

## Security Notes

1. **API Keys**: Keep your RUNPOD_API_KEY secure
2. **Audio URLs**: Ensure medical audio is stored securely
3. **PHI**: Be cautious with patient information
4. **Network**: MCP servers make external API calls to RunPod