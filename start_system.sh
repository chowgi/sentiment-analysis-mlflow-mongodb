#!/bin/bash

# Sentiment Analysis System Startup Script
# This script starts the complete sentiment analysis system

echo "🎬 Starting Sentiment Analysis System..."
echo "========================================"

# Clean up previous MLflow setup
echo "🧹 Cleaning up previous MLflow setup..."
rm -rf mlflow_data/ mlruns/ tokenizer*/ sample_output.txt 2>/dev/null || true
echo "✅ Cleanup completed"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📚 Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if MongoDB Atlas is accessible
echo "🗄️ Checking MongoDB Atlas connection..."
if ! python3 -c "
import os
import pymongo
from dotenv import load_dotenv
load_dotenv()

mongo_uri = os.getenv('MONGODB_URI')
if not mongo_uri:
    print('❌ MONGODB_URI not found in environment variables')
    print('Please ensure .env file contains MONGODB_URI')
    exit(1)

try:
    client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
    client.admin.command('ping')
    print('✅ MongoDB Atlas is accessible')
    client.close()
except Exception as e:
    print(f'❌ MongoDB Atlas connection failed: {e}')
    print('Please check your MongoDB Atlas connection string in .env file')
    print('Ensure your IP address is whitelisted in MongoDB Atlas')
    exit(1)
"; then
    exit 1
fi

# Run the complete setup
echo "🚀 Starting complete system setup..."
python3 setup_sentiment_analysis.py

echo ""
echo "🎉 System startup complete!"
echo "📊 MLflow UI: http://localhost:5002"
echo "🚀 API Server: http://localhost:8001"
echo "📚 API Docs: http://localhost:8001/docs"
