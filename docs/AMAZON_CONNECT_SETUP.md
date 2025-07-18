# Amazon Connect Setup Guide for IasoVoice

This guide walks through setting up Amazon Connect to integrate with the IasoVoice platform for telephony-based medical conversations.

## Prerequisites

- AWS Account with appropriate permissions
- Amazon Connect service access (may require AWS support ticket in some regions)
- Configured IasoVoice services (Whisper, RASA, Phi-4, Polly)
- SSL certificate for WebSocket endpoint (for production)

## Step 1: Create Amazon Connect Instance

1. **Navigate to Amazon Connect Console**
   ```
   https://console.aws.amazon.com/connect/
   ```

2. **Create Instance**
   - Click "Create instance"
   - Choose "Store users within Amazon Connect"
   - Enter instance alias: `iaso-voice-prod` (or your preferred name)
   - Select "I want to make outbound calls with Amazon Connect"

3. **Configure Data Storage**
   - Enable call recordings: Yes
   - Enable chat transcripts: No (using custom transcription)
   - Select S3 bucket for recordings: `iaso-voice-recordings`
   - Enable data streaming: Yes (for real-time analytics)

4. **Review and Create**
   - Review settings
   - Click "Create instance"
   - Wait 2-3 minutes for provisioning

## Step 2: Configure Phone Numbers

1. **Claim Phone Number**
   - Go to Routing → Phone numbers
   - Click "Claim a number"
   - Choose country and type (DID or Toll-free)
   - Select number and click "Save"

2. **Configure Emergency Calling** (if required)
   - Go to Routing → Emergency admin
   - Configure emergency location information

## Step 3: Set Up Contact Flows

### Main IasoVoice Flow

1. **Create New Contact Flow**
   - Go to Routing → Contact flows
   - Click "Create contact flow"
   - Name: "IasoVoice Medical Assistant"

2. **Import Base Flow**
   ```json
   {
     "Version": "2019-10-30",
     "StartAction": "greeting",
     "Actions": {
       "greeting": {
         "Type": "MessageParticipant",
         "Parameters": {
           "Text": "Connecting you to IASO health assistant..."
         },
         "Transitions": {
           "NextAction": "enable-streaming"
         }
       },
       "enable-streaming": {
         "Type": "StartMediaStreaming",
         "Parameters": {
           "Track": "FromCustomer",
           "MediaStreamTypes": "Audio",
           "ConnectionAttributes": {
             "WebSocketUrl": "wss://your-iasovoice-domain.com/connect/${ContactId}"
           }
         },
         "Transitions": {
           "NextAction": "wait-for-session"
         }
       },
       "wait-for-session": {
         "Type": "Wait",
         "Parameters": {
           "TimeoutSeconds": 300
         },
         "Transitions": {
           "NextAction": "disconnect"
         }
       },
       "disconnect": {
         "Type": "DisconnectParticipant",
         "Parameters": {},
         "Transitions": {}
       }
     }
   }
   ```

3. **Configure WebSocket Endpoint**
   - Replace `your-iasovoice-domain.com` with your actual domain
   - Ensure WebSocket endpoint supports WSS (secure WebSocket)

### Authentication Flow (Optional)

1. **Create Authentication Flow**
   - Name: "IasoVoice Patient Authentication"
   - Add customer input for patient ID or phone verification
   - Store authentication status in contact attributes

## Step 4: Configure Lambda Integration

1. **Create Lambda Function**
   ```python
   import json
   import boto3
   
   def lambda_handler(event, context):
       """
       Pre-process Connect events before WebSocket streaming
       """
       contact_id = event.get('Details', {}).get('ContactData', {}).get('ContactId')
       phone_number = event.get('Details', {}).get('ContactData', {}).get('CustomerEndpoint', {}).get('Address')
       
       # Look up patient by phone number (optional)
       patient_id = lookup_patient_by_phone(phone_number)
       
       return {
           'ContactId': contact_id,
           'PhoneNumber': phone_number,
           'PatientId': patient_id,
           'Authenticated': patient_id is not None
       }
   ```

2. **Add Lambda to Contact Flow**
   - Add "Invoke AWS Lambda function" block
   - Select your Lambda function
   - Store returned attributes

## Step 5: Configure Outbound Calling

1. **Create Outbound Campaign** (if needed)
   - Go to Campaigns → Create campaign
   - Configure dialer settings
   - Set up compliance rules

2. **API Integration for Outbound**
   ```python
   import boto3
   
   connect_client = boto3.client('connect', region_name='us-east-1')
   
   def initiate_outbound_call(phone_number, patient_id):
       response = connect_client.start_outbound_voice_contact(
           DestinationPhoneNumber=phone_number,
           ContactFlowId='your-contact-flow-id',
           InstanceId='your-instance-id',
           Attributes={
               'PatientId': patient_id,
               'CallType': 'ScheduledCheckIn'
           }
       )
       return response['ContactId']
   ```

## Step 6: WebSocket Integration

### IasoVoice WebSocket Handler

The orchestrator expects WebSocket connections at:
```
wss://your-domain.com/connect/{call_id}
```

### Message Format

**From Connect to IasoVoice:**
```json
{
  "type": "audio",
  "data": "base64-encoded-audio-chunk",
  "metadata": {
    "sampleRate": 8000,
    "encoding": "pcm"
  }
}
```

**From IasoVoice to Connect:**
```json
{
  "type": "audio",
  "data": "base64-encoded-audio-response"
}
```

## Step 7: Configure Amazon Polly

1. **Ensure Polly Access**
   - IAM role must include `polly:SynthesizeSpeech` permission
   - Configure neural voices for better quality

2. **Voice Selection**
   ```python
   # In PollyClient configuration
   VOICE_MAPPING = {
       'default': 'Joanna',      # Female, neural
       'male': 'Matthew',        # Male, neural
       'clinical': 'Salli',      # Clear, professional
       'empathetic': 'Kendra'    # Warm, caring
   }
   ```

## Step 8: Testing

### Test Phone Call
1. Call your claimed phone number
2. Monitor CloudWatch logs for WebSocket connection
3. Verify audio streaming works both ways

### Test Commands
```bash
# Monitor Connect metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Connect \
  --metric-name CallsPerInterval \
  --dimensions Name=InstanceId,Value=your-instance-id \
  --statistics Sum \
  --start-time 2025-01-17T00:00:00Z \
  --end-time 2025-01-17T23:59:59Z \
  --period 3600

# Check contact flow logs
aws logs tail /aws/connect/your-instance-alias --follow
```

### Debug Checklist
- [ ] WebSocket endpoint accessible from Connect
- [ ] SSL certificate valid for WSS
- [ ] Audio format compatible (8kHz PCM)
- [ ] Contact attributes passed correctly
- [ ] Lambda functions have correct permissions

## Step 9: Production Considerations

### High Availability
1. **Multi-Region Setup**
   - Deploy IasoVoice in multiple regions
   - Use Route 53 for failover

2. **Auto-Scaling**
   - Configure EKS/GKE auto-scaling for pods
   - Use Application Load Balancer for WebSocket

### Security
1. **Encryption**
   - Enable encryption at rest for recordings
   - Use KMS for sensitive data

2. **Access Control**
   - Implement JWT authentication for WebSocket
   - Restrict Connect instance access

3. **Compliance**
   - Enable HIPAA compliance features
   - Configure audit logging

### Monitoring
1. **CloudWatch Dashboards**
   ```json
   {
     "MetricWidget": {
       "metrics": [
         ["AWS/Connect", "CallsPerInterval"],
         [".", "CallRecordingUploadError"],
         [".", "ToInstancePacketLossRate"],
         ["Custom", "WebSocketConnections"],
         [".", "TranscriptionLatency"],
         [".", "SOAPGenerationTime"]
       ]
     }
   }
   ```

2. **Alarms**
   - High packet loss rate
   - WebSocket connection failures
   - Transcription errors
   - Long response times

## Step 10: Integration Testing

### End-to-End Test Script
```python
import asyncio
import websockets
import json
import base64

async def test_iasovoice_integration():
    """Test complete flow from Connect to SOAP note"""
    
    # 1. Initiate test call
    call_id = initiate_outbound_call("+1234567890", "test-patient-123")
    
    # 2. Connect to WebSocket
    uri = f"wss://your-domain.com/connect/{call_id}"
    async with websockets.connect(uri) as websocket:
        # 3. Send test audio
        test_audio = load_test_audio("medical-dictation.wav")
        await websocket.send(json.dumps({
            "type": "audio",
            "data": base64.b64encode(test_audio).decode()
        }))
        
        # 4. Receive response
        response = await websocket.recv()
        assert json.loads(response)["type"] == "audio"
        
    # 5. Verify SOAP note created
    soap_note = get_soap_note_for_call(call_id)
    assert soap_note is not None
    print(f"Test passed! SOAP note created for call {call_id}")
```

## Common Issues and Solutions

### Issue: No Audio from Connect
**Solution:**
- Verify media streaming is enabled in contact flow
- Check WebSocket URL format
- Ensure security groups allow WebSocket traffic

### Issue: Poor Audio Quality
**Solution:**
- Implement jitter buffer in audio handler
- Use Opus codec if available
- Monitor network metrics

### Issue: High Latency
**Solution:**
- Optimize Whisper processing (batch audio chunks)
- Pre-warm Lambda functions
- Use connection pooling for API calls

## Next Steps

1. **Train RASA Model**
   - Create medical conversation training data
   - Define intents and entities
   - Train and deploy model

2. **Customize Conversation Flows**
   - Add appointment scheduling
   - Implement medication reminders
   - Create emergency escalation

3. **Analytics Integration**
   - Export conversation data to data warehouse
   - Create clinical insights dashboards
   - Monitor conversation quality metrics

## Support Resources

- [Amazon Connect Documentation](https://docs.aws.amazon.com/connect/)
- [WebSocket API Reference](https://docs.aws.amazon.com/apigateway/latest/developerguide/websocket-api.html)
- [IasoVoice GitHub Repository](https://github.com/your-org/iasovoice)
- Internal Support: iasovoice-support@your-org.com