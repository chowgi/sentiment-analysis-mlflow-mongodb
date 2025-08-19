#!/bin/bash

# Lambda Deployment Script for Sentiment Analysis
# This script packages and deploys the Lambda function

echo "🚀 Deploying Lambda Function for Sentiment Analysis..."
echo "====================================================="

# Check for required tools
check_requirements() {
    echo "🔍 Checking requirements..."
    
    # Check for zip
    if ! command -v zip &> /dev/null; then
        echo "❌ zip command not found. Installing..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command -v brew &> /dev/null; then
                brew install zip
            else
                echo "❌ Please install Homebrew first: https://brew.sh/"
                echo "   Then run: brew install zip"
                exit 1
            fi
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            if command -v apt-get &> /dev/null; then
                sudo apt-get update && sudo apt-get install -y zip
            elif command -v yum &> /dev/null; then
                sudo yum install -y zip
            else
                echo "❌ Please install zip manually for your Linux distribution"
                exit 1
            fi
        else
            echo "❌ Please install zip manually for your operating system"
            exit 1
        fi
    fi
    
    # Check for AWS CLI
    if ! command -v aws &> /dev/null; then
        echo "❌ AWS CLI not found. Please install it first:"
        echo "   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        echo ""
        echo "   For macOS: brew install awscli"
        echo "   For Linux: pip install awscli"
        echo ""
        echo "   After installation, configure AWS credentials:"
        echo "   aws configure"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "❌ AWS credentials not configured. Please run:"
        echo "   aws configure"
        echo "   or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables"
        exit 1
    fi
    
    echo "✅ All requirements satisfied"
}

# Configuration
FUNCTION_NAME="sentiment-analysis-lambda"
REGION="ap-southeast-2"
RUNTIME="python3.9"
HANDLER="lambda_sentiment_analysis.lambda_handler"
TIMEOUT=30
MEMORY_SIZE=512

# Run requirements check
check_requirements

# Create deployment directory
echo "📁 Creating deployment package..."
rm -rf lambda_deployment
mkdir -p lambda_deployment

# Copy Lambda function
cp lambda_sentiment_analysis.py lambda_deployment/

# Install dependencies
echo "📦 Installing dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r lambda_requirements.txt -t lambda_deployment/
elif command -v pip &> /dev/null; then
    pip install -r lambda_requirements.txt -t lambda_deployment/
else
    echo "❌ pip not found. Please install Python and pip first."
    exit 1
fi

# Create deployment package
echo "📦 Creating ZIP package..."
cd lambda_deployment
zip -r ../lambda_deployment.zip .
cd ..

# Create Lambda execution role if it doesn't exist
create_lambda_role() {
    ROLE_NAME="lambda-execution-role"
    echo "🔐 Creating Lambda execution role..."
    
    # Create trust policy
    cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create role
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file://trust-policy.json \
        --region $REGION 2>/dev/null || echo "Role already exists or creation failed"
    
    # Attach basic execution policy
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
        --region $REGION 2>/dev/null || echo "Basic execution policy already attached"
    
    # Attach SageMaker policy
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess \
        --region $REGION 2>/dev/null || echo "SageMaker policy already attached"
    
    # Wait for role to be available
    echo "⏳ Waiting for role to be available..."
    sleep 10
    
    # Clean up
    rm -f trust-policy.json
}

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
    
    # Create role first
    create_lambda_role
    
    # Get account ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/lambda-execution-role"
    
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --handler $HANDLER \
        --timeout $TIMEOUT \
        --memory-size $MEMORY_SIZE \
        --zip-file fileb://lambda_deployment.zip \
        --region $REGION \
        --role $ROLE_ARN
fi

# Set environment variables
echo "⚙️ Setting environment variables..."
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment 'Variables={"SAGEMAKER_ENDPOINT_NAME":"distilbert-sentiment","MONGODB_DATABASE":"imdb_reviews","MONGODB_COLLECTION":"sentiment_analysis"}' \
    --region $REGION

# Add permissions for EventBridge
echo "🔐 Adding EventBridge permissions..."
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id EventBridgeInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:$REGION:$(aws sts get-caller-identity --query Account --output text):rule/* \
    --region $REGION 2>/dev/null || echo "EventBridge permissions already exist"

# Add permissions for SageMaker
echo "🔐 Adding SageMaker permissions..."
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id SageMakerInvoke \
    --action lambda:InvokeFunction \
    --principal sagemaker.amazonaws.com \
    --source-arn arn:aws:sagemaker:ap-southeast-2:211125542926:endpoint/distilbert-sentiment \
    --region $REGION 2>/dev/null || echo "SageMaker permissions already exist"

# Clean up
echo "🧹 Cleaning up..."
rm -rf lambda_deployment
if [ -f "lambda_deployment.zip" ]; then
    rm lambda_deployment.zip
fi

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
