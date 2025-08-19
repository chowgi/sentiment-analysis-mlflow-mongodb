#!/bin/bash

# Installation script for Lambda deployment requirements
echo "🔧 Installing Lambda deployment requirements..."
echo "=============================================="

# Detect operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🐧 Detected macOS"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "📦 Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo "✅ Homebrew already installed"
    fi
    
    # Install zip
    echo "📦 Installing zip..."
    brew install zip
    
    # Install AWS CLI
    echo "📦 Installing AWS CLI..."
    brew install awscli
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Detected Linux"
    
    # Install zip
    echo "📦 Installing zip..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y zip
    elif command -v yum &> /dev/null; then
        sudo yum install -y zip
    else
        echo "❌ Please install zip manually for your Linux distribution"
    fi
    
    # Install AWS CLI
    echo "📦 Installing AWS CLI..."
    if command -v pip3 &> /dev/null; then
        pip3 install awscli
    elif command -v pip &> /dev/null; then
        pip install awscli
    else
        echo "❌ Please install pip first, then run: pip install awscli"
    fi
    
else
    echo "❌ Unsupported operating system: $OSTYPE"
    echo "Please install the following manually:"
    echo "  - zip"
    echo "  - AWS CLI (https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)"
    exit 1
fi

echo ""
echo "✅ Installation completed!"
echo "========================="
echo ""
echo "🔧 Next steps:"
echo "1. Configure AWS credentials:"
echo "   aws configure"
echo ""
echo "2. Deploy the Lambda function:"
echo "   ./deploy_lambda.sh"
echo ""
echo "📋 AWS Configuration:"
echo "   You'll need your AWS Access Key ID and Secret Access Key"
echo "   Get them from: https://console.aws.amazon.com/iam/home#/security_credentials"
