#!/bin/bash

# Deploy Amazon Connect infrastructure for IasoVoice
# Usage: ./deploy-connect-infrastructure.sh [environment] [region]

set -e

ENVIRONMENT=${1:-development}
REGION=${2:-us-east-1}
STACK_NAME="iasovoice-connect-${ENVIRONMENT}"

echo "Deploying Amazon Connect infrastructure for IasoVoice..."
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Stack: $STACK_NAME"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS CLI not configured. Please run 'aws configure'"
    exit 1
fi

# Create CloudFormation template
cat > /tmp/connect-infrastructure.yaml << 'EOF'
AWSTemplateFormatVersion: '2010-09-09'
Description: 'IasoVoice Amazon Connect Infrastructure'

Parameters:
  Environment:
    Type: String
    Default: development
    AllowedValues: [development, staging, production]
  
  WebSocketDomain:
    Type: String
    Description: Domain for WebSocket endpoint (e.g., api.iasovoice.com)
    Default: localhost
  
  CertificateArn:
    Type: String
    Description: ACM certificate ARN for SSL/TLS
    Default: ""

Resources:
  # S3 Bucket for call recordings
  CallRecordingsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "iasovoice-recordings-${Environment}-${AWS::AccountId}"
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: aws:kms
              KMSMasterKeyID: !Ref RecordingsKMSKey
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      LifecycleConfiguration:
        Rules:
          - Id: DeleteAfter7Years
            Status: Enabled
            ExpirationInDays: 2555  # 7 years for HIPAA compliance
      VersioningConfiguration:
        Status: Enabled

  # KMS Key for encryption
  RecordingsKMSKey:
    Type: AWS::KMS::Key
    Properties:
      Description: "KMS key for IasoVoice call recordings encryption"
      KeyPolicy:
        Statement:
          - Sid: Enable IAM User Permissions
            Effect: Allow
            Principal:
              AWS: !Sub "arn:aws:iam::${AWS::AccountId}:root"
            Action: "kms:*"
            Resource: "*"
          - Sid: Allow Connect Service
            Effect: Allow
            Principal:
              Service: connect.amazonaws.com
            Action:
              - kms:Decrypt
              - kms:GenerateDataKey
            Resource: "*"

  RecordingsKMSKeyAlias:
    Type: AWS::KMS::Alias
    Properties:
      AliasName: !Sub "alias/iasovoice-recordings-${Environment}"
      TargetKeyId: !Ref RecordingsKMSKey

  # IAM Role for Connect
  ConnectServiceRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub "IasoVoice-Connect-${Environment}"
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: connect.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonConnectServiceRolePolicy
      Policies:
        - PolicyName: S3RecordingsAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:PutObject
                  - s3:GetObject
                  - s3:DeleteObject
                Resource: !Sub "${CallRecordingsBucket}/*"
              - Effect: Allow
                Action:
                  - s3:ListBucket
                Resource: !Ref CallRecordingsBucket
              - Effect: Allow
                Action:
                  - kms:Decrypt
                  - kms:GenerateDataKey
                Resource: !Ref RecordingsKMSKey

  # Lambda function for Connect integration
  ConnectLambdaRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub "IasoVoice-Lambda-${Environment}"
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: ConnectPermissions
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - connect:StartOutboundVoiceContact
                  - connect:StopContact
                  - connect:GetContactAttributes
                  - connect:UpdateContactAttributes
                Resource: "*"

  ConnectIntegrationLambda:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub "iasovoice-connect-integration-${Environment}"
      Runtime: python3.9
      Handler: index.lambda_handler
      Role: !GetAtt ConnectLambdaRole.Arn
      Timeout: 30
      Environment:
        Variables:
          IASOVOICE_ENDPOINT: !Ref WebSocketDomain
          ENVIRONMENT: !Ref Environment
      Code:
        ZipFile: |
          import json
          import os
          import boto3
          import logging
          
          logger = logging.getLogger()
          logger.setLevel(logging.INFO)
          
          def lambda_handler(event, context):
              """
              Pre-process Connect events before WebSocket streaming
              """
              try:
                  # Extract contact information
                  contact_data = event.get('Details', {}).get('ContactData', {})
                  contact_id = contact_data.get('ContactId')
                  phone_number = contact_data.get('CustomerEndpoint', {}).get('Address')
                  
                  # Log the incoming event
                  logger.info(f"Processing contact {contact_id} from {phone_number}")
                  
                  # Look up patient by phone number (implement your logic)
                  patient_id = lookup_patient_by_phone(phone_number)
                  
                  # Return attributes to be set in Connect
                  return {
                      'ContactId': contact_id,
                      'PhoneNumber': phone_number,
                      'PatientId': patient_id or 'unknown',
                      'Authenticated': str(patient_id is not None).lower(),
                      'WebSocketEndpoint': f"wss://{os.environ['IASOVOICE_ENDPOINT']}/connect/{contact_id}"
                  }
                  
              except Exception as e:
                  logger.error(f"Error processing contact: {str(e)}")
                  return {
                      'Error': str(e),
                      'ContactId': contact_id if 'contact_id' in locals() else 'unknown'
                  }
          
          def lookup_patient_by_phone(phone_number):
              """
              Look up patient by phone number
              Implement your patient lookup logic here
              """
              # Example: Query your patient database
              # return patient_service.get_patient_by_phone(phone_number)
              return None

  # CloudWatch Log Group for Lambda
  ConnectLambdaLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub "/aws/lambda/iasovoice-connect-integration-${Environment}"
      RetentionInDays: 30

  # Lambda permission for Connect
  ConnectLambdaPermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref ConnectIntegrationLambda
      Action: lambda:InvokeFunction
      Principal: connect.amazonaws.com
      SourceAccount: !Ref AWS::AccountId

  # CloudWatch Dashboard
  ConnectDashboard:
    Type: AWS::CloudWatch::Dashboard
    Properties:
      DashboardName: !Sub "IasoVoice-Connect-${Environment}"
      DashboardBody: !Sub |
        {
          "widgets": [
            {
              "type": "metric",
              "x": 0,
              "y": 0,
              "width": 12,
              "height": 6,
              "properties": {
                "metrics": [
                  ["AWS/Connect", "CallsPerInterval"],
                  [".", "CallRecordingUploadError"],
                  [".", "ToInstancePacketLossRate"]
                ],
                "period": 300,
                "stat": "Sum",
                "region": "${AWS::Region}",
                "title": "Connect Metrics"
              }
            },
            {
              "type": "metric",
              "x": 0,
              "y": 6,
              "width": 12,
              "height": 6,
              "properties": {
                "metrics": [
                  ["AWS/Lambda", "Duration", "FunctionName", "iasovoice-connect-integration-${Environment}"],
                  [".", "Errors", ".", "."],
                  [".", "Invocations", ".", "."]
                ],
                "period": 300,
                "stat": "Average",
                "region": "${AWS::Region}",
                "title": "Lambda Performance"
              }
            }
          ]
        }

  # CloudWatch Alarms
  HighPacketLossAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub "IasoVoice-Connect-HighPacketLoss-${Environment}"
      AlarmDescription: "High packet loss rate detected"
      MetricName: ToInstancePacketLossRate
      Namespace: AWS/Connect
      Statistic: Average
      Period: 300
      EvaluationPeriods: 2
      Threshold: 0.05  # 5% packet loss
      ComparisonOperator: GreaterThanThreshold
      TreatMissingData: notBreaching

  LambdaErrorAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub "IasoVoice-Lambda-Errors-${Environment}"
      AlarmDescription: "Lambda function errors detected"
      MetricName: Errors
      Namespace: AWS/Lambda
      Dimensions:
        - Name: FunctionName
          Value: !Ref ConnectIntegrationLambda
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 1
      Threshold: 1
      ComparisonOperator: GreaterThanOrEqualToThreshold
      TreatMissingData: notBreaching

Outputs:
  CallRecordingsBucket:
    Description: S3 bucket for call recordings
    Value: !Ref CallRecordingsBucket
    Export:
      Name: !Sub "${AWS::StackName}-CallRecordingsBucket"

  KMSKeyId:
    Description: KMS key for encryption
    Value: !Ref RecordingsKMSKey
    Export:
      Name: !Sub "${AWS::StackName}-KMSKey"

  LambdaFunctionArn:
    Description: Lambda function ARN for Connect integration
    Value: !GetAtt ConnectIntegrationLambda.Arn
    Export:
      Name: !Sub "${AWS::StackName}-LambdaArn"

  ConnectServiceRoleArn:
    Description: IAM role ARN for Connect service
    Value: !GetAtt ConnectServiceRole.Arn
    Export:
      Name: !Sub "${AWS::StackName}-ConnectRole"

  DashboardURL:
    Description: CloudWatch dashboard URL
    Value: !Sub "https://console.aws.amazon.com/cloudwatch/home?region=${AWS::Region}#dashboards:name=${ConnectDashboard}"
EOF

# Deploy the CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file /tmp/connect-infrastructure.yaml \
  --stack-name $STACK_NAME \
  --parameter-overrides \
    Environment=$ENVIRONMENT \
    WebSocketDomain=${WEBSOCKET_DOMAIN:-localhost} \
    CertificateArn=${CERTIFICATE_ARN:-""} \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

# Get stack outputs
echo ""
echo "Stack deployment complete! Getting outputs..."
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table

# Save outputs to file
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs' \
  --output json > "connect-outputs-${ENVIRONMENT}.json"

echo ""
echo "Outputs saved to connect-outputs-${ENVIRONMENT}.json"

# Clean up temporary file
rm -f /tmp/connect-infrastructure.yaml

echo ""
echo "Next steps:"
echo "1. Create Amazon Connect instance using the console"
echo "2. Configure the instance with the S3 bucket from outputs"
echo "3. Import the contact flow JSON (see docs/AMAZON_CONNECT_SETUP.md)"
echo "4. Claim a phone number and assign to the contact flow"
echo "5. Update your IasoVoice orchestrator with the Connect instance details"
echo ""
echo "For detailed setup instructions, see docs/AMAZON_CONNECT_SETUP.md"