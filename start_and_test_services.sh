#!/bin/bash

# EC2 Startup and Test Script for Sentiment Analysis System
# This script starts the services and runs comprehensive tests
# Use this when your EC2 instance has been stopped and restarted

echo "🚀 Starting Sentiment Analysis System on EC2..."
echo "=============================================="

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if we're in the right directory
if [ ! -f "sentiment_api_server.py" ]; then
    echo "❌ Error: sentiment_api_server.py not found. Please run this script from the project directory."
    exit 1
fi

echo "📁 Working directory: $(pwd)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run deploy_ubuntu_ec2.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ Warning: .env file not found. Please create it with your MongoDB URI."
    echo "Example .env file:"
    echo "MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/imdb_reviews?retryWrites=true&w=majority"
fi

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    local url=$3
    
    echo "🔍 Checking $service_name..."
    
    # Check systemd service status
    if sudo systemctl is-active --quiet $service_name; then
        echo "✅ $service_name systemd service is running"
    else
        echo "❌ $service_name systemd service is not running"
        return 1
    fi
    
    # Check if port is listening
    if netstat -tlnp 2>/dev/null | grep ":$port " > /dev/null; then
        echo "✅ $service_name is listening on port $port"
    else
        echo "❌ $service_name is not listening on port $port"
        return 1
    fi
    
    # Check HTTP response
    if curl -s --max-time 5 "$url" > /dev/null; then
        echo "✅ $service_name is responding to HTTP requests"
    else
        echo "❌ $service_name is not responding to HTTP requests"
        return 1
    fi
    
    return 0
}

# Function to start a service
start_service() {
    local service_name=$1
    local description=$2
    
    echo "🚀 Starting $description..."
    sudo systemctl start $service_name
    
    # Wait a bit for service to start
    sleep 3
    
    # Check if service started successfully
    if sudo systemctl is-active --quiet $service_name; then
        echo "✅ $description started successfully"
        return 0
    else
        echo "❌ $description failed to start"
        echo "📋 Service status:"
        sudo systemctl status $service_name --no-pager -l
        return 1
    fi
}

# Start services
echo ""
echo "🔄 Starting services..."

# Start MLflow server first (API depends on it)
MLFLOW_STARTED=false
if start_service "mlflow-server" "MLflow Server"; then
    MLFLOW_STARTED=true
else
    echo "⚠️ MLflow server failed to start, but continuing..."
fi

# Start API server
API_STARTED=false
if start_service "sentiment-api" "Sentiment Analysis API"; then
    API_STARTED=true
else
    echo "⚠️ API server failed to start"
fi

# Wait for services to fully initialize
echo "⏳ Waiting for services to fully initialize..."
sleep 10

# Run comprehensive tests
echo ""
echo "🧪 Running comprehensive tests..."
echo "================================"

# Test 1: Check if services are running
echo ""
echo "📊 Service Status Check:"
echo "-----------------------"

if [ "$MLFLOW_STARTED" = true ]; then
    check_service "mlflow-server" "5002" "http://localhost:5002"
    MLFLOW_OK=$?
else
    echo "⚠️ Skipping MLflow check (service not started)"
    MLFLOW_OK=1
fi

if [ "$API_STARTED" = true ]; then
    check_service "sentiment-api" "8001" "http://localhost:8001/health"
    API_OK=$?
else
    echo "⚠️ Skipping API check (service not started)"
    API_OK=1
fi

# Test 2: API Health Check
echo ""
echo "🏥 API Health Check:"
echo "-------------------"
if [ "$API_STARTED" = true ]; then
    echo "Testing API health endpoint..."
    HEALTH_RESPONSE=$(curl -s --max-time 10 http://localhost:8001/health)
    if [ $? -eq 0 ]; then
        echo "✅ API health check successful"
        echo "Response: $HEALTH_RESPONSE"
    else
        echo "❌ API health check failed"
        API_OK=1
    fi
fi

# Test 3: MongoDB Connection Test
echo ""
echo "🗄️ MongoDB Connection Test:"
echo "---------------------------"
echo "Testing MongoDB connection..."
python -c "
import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient

try:
    load_dotenv()
    mongo_uri = os.getenv('MONGODB_URI')
    if not mongo_uri:
        print('❌ MONGODB_URI not found in .env file')
        sys.exit(1)
    
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✅ MongoDB connection successful')
    client.close()
except Exception as e:
    print(f'❌ MongoDB connection failed: {e}')
    sys.exit(1)
"
MONGO_OK=$?

# Test 4: Sentiment Analysis Test
echo ""
echo "🧠 Sentiment Analysis Test:"
echo "---------------------------"
if [ "$API_STARTED" = true ]; then
    echo "Testing sentiment analysis with sample review..."
    TEST_RESPONSE=$(curl -s --max-time 10 -X POST "http://localhost:8001/predict" \
        -H "Content-Type: application/json" \
        -d '{"review": "This movie was absolutely fantastic!", "movie_title": "Test Movie"}')
    
    if [ $? -eq 0 ]; then
        echo "✅ Sentiment analysis test successful"
        echo "Response: $TEST_RESPONSE"
    else
        echo "❌ Sentiment analysis test failed"
        API_OK=1
    fi
fi

# Test 5: Network Connectivity
echo ""
echo "🌐 Network Connectivity Test:"
echo "----------------------------"
echo "Checking if services are accessible from external IP..."

# Get external IP
EXTERNAL_IP=$(curl -s --max-time 5 http://checkip.amazonaws.com/ 2>/dev/null || echo "unknown")
echo "External IP: $EXTERNAL_IP"

if [ "$API_STARTED" = true ]; then
    echo "API should be accessible at: http://$EXTERNAL_IP:8001"
fi

if [ "$MLFLOW_STARTED" = true ]; then
    echo "MLflow UI should be accessible at: http://$EXTERNAL_IP:5002"
fi

# Summary
echo ""
echo "📋 Test Summary:"
echo "==============="
echo "MLflow Server: $([ $MLFLOW_OK -eq 0 ] && echo "✅ Working" || echo "❌ Issues")"
echo "API Server: $([ $API_OK -eq 0 ] && echo "✅ Working" || echo "❌ Issues")"
echo "MongoDB: $([ $MONGO_OK -eq 0 ] && echo "✅ Connected" || echo "❌ Issues")"

# Overall status
if [ $MLFLOW_OK -eq 0 ] && [ $API_OK -eq 0 ] && [ $MONGO_OK -eq 0 ]; then
    echo ""
    echo "🎉 All systems are working correctly!"
    echo "====================================="
    echo "🚀 Your sentiment analysis system is ready to use!"
    echo ""
    echo "📊 Access URLs:"
    echo "  API Server: http://$EXTERNAL_IP:8001"
    echo "  API Docs: http://$EXTERNAL_IP:8001/docs"
    echo "  MLflow UI: http://$EXTERNAL_IP:5002"
    echo ""
    echo "🔧 Useful commands:"
    echo "  Check service status: sudo systemctl status sentiment-api mlflow-server"
    echo "  View API logs: sudo journalctl -u sentiment-api -f"
    echo "  View MLflow logs: sudo journalctl -u mlflow-server -f"
    echo "  Restart services: sudo systemctl restart sentiment-api mlflow-server"
    echo ""
    echo "✅ System is ready for MongoDB Atlas trigger integration!"
else
    echo ""
    echo "⚠️ Some issues detected. Here's how to troubleshoot:"
    echo "=================================================="
    echo ""
    if [ $MLFLOW_OK -ne 0 ]; then
        echo "🔧 MLflow Server Issues:"
        echo "  - Check logs: sudo journalctl -u mlflow-server -f"
        echo "  - Restart: sudo systemctl restart mlflow-server"
        echo "  - Check if port 5002 is available: sudo netstat -tlnp | grep 5002"
    fi
    
    if [ $API_OK -ne 0 ]; then
        echo "🔧 API Server Issues:"
        echo "  - Check logs: sudo journalctl -u sentiment-api -f"
        echo "  - Restart: sudo systemctl restart sentiment-api"
        echo "  - Check if port 8001 is available: sudo netstat -tlnp | grep 8001"
        echo "  - Verify .env file exists and has correct MONGODB_URI"
    fi
    
    if [ $MONGO_OK -ne 0 ]; then
        echo "🔧 MongoDB Issues:"
        echo "  - Check .env file has correct MONGODB_URI"
        echo "  - Verify MongoDB Atlas cluster is accessible"
        echo "  - Check network connectivity to MongoDB"
    fi
    
    echo ""
    echo "💡 Try running this script again after fixing the issues above."
fi

echo ""
echo "🏁 Startup and test script completed!"
