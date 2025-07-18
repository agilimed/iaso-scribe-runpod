#!/usr/bin/env python3
"""
Test script for Amazon Connect + IasoVoice integration
"""

import asyncio
import json
import base64
import boto3
import time
from typing import Dict, Any
import websockets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectIntegrationTester:
    """Test Amazon Connect integration with IasoVoice"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.connect_client = boto3.client('connect', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        
    def test_lambda_function(self, function_name: str, test_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Test the Connect Lambda function"""
        logger.info(f"Testing Lambda function: {function_name}")
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_payload)
            )
            
            result = json.loads(response['Payload'].read())
            logger.info(f"Lambda response: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Lambda test failed: {e}")
            return {"error": str(e)}
    
    def test_outbound_call(self, instance_id: str, contact_flow_id: str, 
                          phone_number: str, patient_id: str) -> str:
        """Test outbound call initiation"""
        logger.info(f"Initiating outbound call to {phone_number}")
        
        try:
            response = self.connect_client.start_outbound_voice_contact(
                DestinationPhoneNumber=phone_number,
                ContactFlowId=contact_flow_id,
                InstanceId=instance_id,
                Attributes={
                    'PatientId': patient_id,
                    'CallType': 'TestCall',
                    'Environment': 'testing'
                }
            )
            
            contact_id = response['ContactId']
            logger.info(f"Outbound call initiated: {contact_id}")
            return contact_id
            
        except Exception as e:
            logger.error(f"Outbound call failed: {e}")
            return ""
    
    async def test_websocket_connection(self, websocket_url: str, 
                                       test_audio_file: str = None) -> bool:
        """Test WebSocket connection with IasoVoice"""
        logger.info(f"Testing WebSocket connection to {websocket_url}")
        
        try:
            async with websockets.connect(websocket_url) as websocket:
                logger.info("WebSocket connected successfully")
                
                # Send test audio if provided
                if test_audio_file:
                    test_audio = self._load_test_audio(test_audio_file)
                    await websocket.send(json.dumps({
                        "type": "audio",
                        "data": base64.b64encode(test_audio).decode(),
                        "metadata": {
                            "sampleRate": 8000,
                            "encoding": "pcm"
                        }
                    }))
                    logger.info("Test audio sent")
                
                # Send test metadata
                await websocket.send(json.dumps({
                    "type": "metadata",
                    "phoneNumber": "+1234567890",
                    "patientId": "test-patient-123"
                }))
                logger.info("Test metadata sent")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    logger.info(f"Received response: {response}")
                    return True
                except asyncio.TimeoutError:
                    logger.warning("No response received within timeout")
                    return False
                    
        except Exception as e:
            logger.error(f"WebSocket test failed: {e}")
            return False
    
    def _load_test_audio(self, file_path: str) -> bytes:
        """Load test audio file"""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load test audio: {e}")
            # Return empty PCM audio (silence)
            return b'\x00' * 1600  # 0.1 seconds of silence at 8kHz
    
    def test_connect_metrics(self, instance_id: str) -> Dict[str, Any]:
        """Test Connect metrics retrieval"""
        logger.info(f"Testing Connect metrics for instance {instance_id}")
        
        cloudwatch = boto3.client('cloudwatch', region_name=self.region)
        
        try:
            # Get call metrics for the last hour
            end_time = time.time()
            start_time = end_time - 3600  # 1 hour ago
            
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Connect',
                MetricName='CallsPerInterval',
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            metrics = response.get('Datapoints', [])
            logger.info(f"Found {len(metrics)} metric datapoints")
            
            return {
                'success': True,
                'datapoints': len(metrics),
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Metrics test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """Generate test report"""
        report = []
        report.append("=== Amazon Connect + IasoVoice Integration Test Report ===")
        report.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            report.append(f"{test_name}: {status}")
            
            if not result.get('success', False) and 'error' in result:
                report.append(f"  Error: {result['error']}")
            
            if 'details' in result:
                report.append(f"  Details: {result['details']}")
            
            report.append("")
        
        return "\n".join(report)

async def main():
    """Main test function"""
    tester = ConnectIntegrationTester()
    results = {}
    
    # Configuration (update these values)
    CONFIG = {
        'lambda_function_name': 'iasovoice-connect-integration-development',
        'connect_instance_id': 'your-connect-instance-id',
        'contact_flow_id': 'your-contact-flow-id',
        'websocket_url': 'wss://localhost:8888/connect/test-call-123',
        'test_phone_number': '+1234567890',
        'test_patient_id': 'test-patient-123',
        'test_audio_file': 'test-audio.wav'  # Optional
    }
    
    logger.info("Starting Amazon Connect + IasoVoice integration tests")
    
    # Test 1: Lambda function
    logger.info("=== Test 1: Lambda Function ===")
    test_payload = {
        "Details": {
            "ContactData": {
                "ContactId": "test-contact-123",
                "CustomerEndpoint": {
                    "Address": CONFIG['test_phone_number']
                }
            }
        }
    }
    
    lambda_result = tester.test_lambda_function(
        CONFIG['lambda_function_name'],
        test_payload
    )
    results['lambda_function'] = {
        'success': 'error' not in lambda_result,
        'details': lambda_result
    }
    
    # Test 2: WebSocket connection
    logger.info("=== Test 2: WebSocket Connection ===")
    websocket_success = await tester.test_websocket_connection(
        CONFIG['websocket_url'],
        CONFIG.get('test_audio_file')
    )
    results['websocket_connection'] = {
        'success': websocket_success
    }
    
    # Test 3: Outbound call (optional - may incur charges)
    if input("Test outbound call? This may incur charges (y/N): ").lower() == 'y':
        logger.info("=== Test 3: Outbound Call ===")
        contact_id = tester.test_outbound_call(
            CONFIG['connect_instance_id'],
            CONFIG['contact_flow_id'],
            CONFIG['test_phone_number'],
            CONFIG['test_patient_id']
        )
        results['outbound_call'] = {
            'success': bool(contact_id),
            'details': f"Contact ID: {contact_id}" if contact_id else "Failed to initiate call"
        }
    
    # Test 4: Connect metrics
    logger.info("=== Test 4: Connect Metrics ===")
    metrics_result = tester.test_connect_metrics(CONFIG['connect_instance_id'])
    results['connect_metrics'] = metrics_result
    
    # Generate and display report
    report = tester.generate_test_report(results)
    print("\n" + report)
    
    # Save report to file
    with open('connect-integration-test-report.txt', 'w') as f:
        f.write(report)
    
    logger.info("Test report saved to connect-integration-test-report.txt")

if __name__ == "__main__":
    asyncio.run(main())