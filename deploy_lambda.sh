#!/bin/bash

# Lambda Deployment Script for Sentiment Analysis
# This script packages and deploys the Lambda function

echo "🚀 Deploying Lambda Function for Sentiment Analysis..."
echo "====================================================="

# Configuration
FUNCTION_NAME="sentiment-analysis-lambda"
REGION="ap-southeast-2"
RUNTIME="python3.9"
HANDLER="lambda_sentiment_analysis.lambda_handler"
TIMEOUT=30
MEMORY_SIZE=512

# Create deployment directory
echo "📁 Creating deployment package..."
rm -rf lambda_deployment
mkdir -p lambda_deployment

# Copy Lambda function
cp lambda_sentiment_analysis.py lambda_deployment/

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r lambda_requirements.txt -t lambda_deployment/

# Create deployment package
echo "📦 Creating ZIP package..."
cd lambda_deployment
zip -r ../lambda_deployment.zip .
cd ..

# Check if function exists
echo "🔍 Checking if Lambda function exists..."
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > /dev/null 2>&1; then
    echo "📝 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda_deployment.zip \
        --region $REGION
    
    # Update configuration
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout $TIMEOUT \
        --memory-size $MEMORY_SIZE \
        --region $REGION
else
    echo "🆕 Creating new Lambda function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --handler $HANDLER \
        --timeout $TIMEOUT \
        --memory-size $MEMORY_SIZE \
        --zip-file fileb://lambda_deployment.zip \
        --region $REGION \
        --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/lambda-execution-role
fi

# Set environment variables
echo "⚙️ Setting environment variables..."
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment Variables='{
        "SAGEMAKER_ENDPOINT_NAME":"distilbert-sentiment",
        "MONGODB_DATABASE":"imdb_reviews",
        "MONGODB_COLLECTION":"sentiment_analysis"
    }' \
    --region $REGION

# Add permissions for EventBridge
echo "🔐 Adding EventBridge permissions..."
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id EventBridgeInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:$REGION:$(aws sts get-caller-identity --query Account --output text):rule/* \
    --region $REGION

# Add permissions for SageMaker
echo "🔐 Adding SageMaker permissions..."
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id SageMakerInvoke \
    --action lambda:InvokeFunction \
    --principal sagemaker.amazonaws.com \
    --source-arn arn:aws:sagemaker:ap-southeast-2:211125542926:endpoint/distilbert-sentiment \
    --region $REGION

# Clean up
echo "🧹 Cleaning up..."
rm -rf lambda_deployment
rm lambda_deployment.zip

echo ""
echo "✅ Lambda function deployed successfully!"
echo "========================================"
echo "Function Name: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Runtime: $RUNTIME"
echo "Handler: $HANDLER"
echo "Timeout: ${TIMEOUT}s"
echo "Memory: ${MEMORY_SIZE}MB"
echo ""
echo "🔧 Next steps:"
echo "1. Set the MONGODB_URI environment variable in the Lambda console"
echo "2. Create an EventBridge rule to trigger this Lambda"
echo "3. Test the function with a sample event"
echo ""
echo "📋 Useful commands:"
echo "  Test function: aws lambda invoke --function-name $FUNCTION_NAME --payload file://test-event.json response.json"
echo "  View logs: aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
echo "  Update env vars: aws lambda update-function-configuration --function-name $FUNCTION_NAME --environment Variables='MONGODB_URI=your-uri'"
