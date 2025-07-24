# AWS Deployment Guide

This guide explains how to deploy the Document to Speech Flask application to AWS using different methods.

## Prerequisites

1. AWS CLI installed and configured
2. Docker installed (for container deployment)
3. OpenAI API key

## Method 1: AWS Elastic Beanstalk (Recommended)

### Step 1: Prepare the Application

1. Create an `.env` file with your configuration:
```bash
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
```

2. Create `application.py` (Elastic Beanstalk requires this name):
```python
from app import app as application

if __name__ == "__main__":
    application.run()
```

### Step 2: Deploy to Elastic Beanstalk

1. Initialize Elastic Beanstalk:
```bash
eb init -p python-3.11 document-to-speech-app
```

2. Create environment:
```bash
eb create document-to-speech-env
```

3. Set environment variables:
```bash
eb setenv OPENAI_API_KEY=your_key_here SECRET_KEY=your_secret_key
```

4. Deploy:
```bash
eb deploy
```

### Step 3: Configure Environment

Create `.ebextensions/01_packages.config`:
```yaml
packages:
  yum:
    ffmpeg: []
```

## Method 2: AWS ECS with Fargate

### Step 1: Build and Push Docker Image

1. Build the Docker image:
```bash
docker build -t document-to-speech .
```

2. Tag for ECR:
```bash
docker tag document-to-speech:latest <account-id>.dkr.ecr.<region>.amazonaws.com/document-to-speech:latest
```

3. Push to ECR:
```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/document-to-speech:latest
```

### Step 2: Create ECS Service

1. Create task definition (`task-definition.json`):
```json
{
  "family": "document-to-speech",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "document-to-speech",
      "image": "<account-id>.dkr.ecr.<region>.amazonaws.com/document-to-speech:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "your_api_key_here"
        },
        {
          "name": "SECRET_KEY",
          "value": "your_secret_key_here"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/document-to-speech",
          "awslogs-region": "<region>",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

2. Register task definition:
```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

3. Create ECS service with Application Load Balancer

## Method 3: AWS Lambda + API Gateway (For smaller documents)

### Step 1: Prepare Lambda Package

1. Create `lambda_function.py`:
```python
import json
import base64
from app import DocumentToSpeechApp

def lambda_handler(event, context):
    # Handle Lambda event
    # Note: Limited by Lambda execution time and memory
    pass
```

2. Package dependencies:
```bash
pip install -r requirements.txt -t .
zip -r deployment-package.zip .
```

### Step 2: Deploy Lambda

1. Create Lambda function:
```bash
aws lambda create-function \
  --function-name document-to-speech \
  --runtime python3.11 \
  --role arn:aws:iam::<account-id>:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://deployment-package.zip
```

2. Create API Gateway to trigger Lambda

## Environment Variables

Set these environment variables in your chosen deployment method:

- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: Flask secret key for sessions
- `FLASK_ENV`: Set to `production`

## Security Considerations

1. **API Keys**: Store sensitive keys in AWS Systems Manager Parameter Store or AWS Secrets Manager
2. **HTTPS**: Always use HTTPS in production
3. **WAF**: Consider using AWS WAF for additional security
4. **VPC**: Deploy in private subnets with NAT Gateway for outbound internet access

## Monitoring and Logging

1. **CloudWatch**: Monitor application logs and metrics
2. **Health Checks**: The app includes a `/health` endpoint
3. **Alarms**: Set up CloudWatch alarms for error rates and response times

## Cost Optimization

1. **Auto Scaling**: Configure based on demand
2. **Spot Instances**: Use for non-critical workloads
3. **CloudWatch**: Monitor costs and set up billing alerts

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Ensure ffmpeg is installed in the container/environment
2. **OpenAI API errors**: Check API key and rate limits
3. **File upload issues**: Check file size limits and permissions
4. **Audio processing timeout**: Increase timeout limits for large documents

### Logs

Check application logs for detailed error information:
```bash
# Elastic Beanstalk
eb logs

# ECS
aws logs get-log-events --log-group-name /ecs/document-to-speech
```

## Performance Tuning

1. **File Processing**: Consider implementing asynchronous processing for large files
2. **Caching**: Cache frequently processed documents
3. **CDN**: Use CloudFront for static assets
4. **Database**: Consider adding a database for user management and file tracking