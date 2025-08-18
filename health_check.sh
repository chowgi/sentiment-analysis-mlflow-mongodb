#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏥 Sentiment Analysis System Health Check${NC}"
echo "=========================================="

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

# Function to check if a service is running
check_service() {
    if sudo systemctl is-active --quiet $1; then
        echo -e "${GREEN}✅ $1 service is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 service is not running${NC}"
        return 1
    fi
}

# Function to check if a port is listening
check_port() {
    if netstat -tuln | grep -q ":$1 "; then
        echo -e "${GREEN}✅ Port $1 is listening${NC}"
        return 0
    else
        echo -e "${RED}❌ Port $1 is not listening${NC}"
        return 1
    fi
}

# Function to check HTTP endpoint
check_http() {
    local url=$1
    local description=$2
    local response=$(curl -s -o /dev/null -w "%{http_code}" $url)
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ $description is responding (HTTP $response)${NC}"
        return 0
    else
        echo -e "${RED}❌ $description is not responding (HTTP $response)${NC}"
        return 1
    fi
}

# Change to application directory and activate virtual environment
cd /opt/sentiment-analysis
source venv/bin/activate

echo -e "\n${BLUE}🔧 System Services Check${NC}"
echo "------------------------"

# Check systemd services
check_service "sentiment-api"
api_service_status=$?

check_service "mlflow-server"
mlflow_service_status=$?

echo -e "\n${BLUE}🌐 Network Ports Check${NC}"
echo "----------------------"

# Check if ports are listening
check_port "8001"
api_port_status=$?

check_port "5002"
mlflow_port_status=$?

echo -e "\n${BLUE}🌍 HTTP Endpoints Check${NC}"
echo "------------------------"

# Check API health endpoint
echo "Testing API health endpoint..."
check_http "http://localhost:8001/health" "API Health Endpoint"
api_health_status=$?

# Check API docs endpoint
echo "Testing API documentation..."
check_http "http://localhost:8001/docs" "API Documentation"
api_docs_status=$?

# Check MLflow UI
echo "Testing MLflow UI..."
check_http "http://localhost:5002" "MLflow UI"
mlflow_ui_status=$?

echo -e "\n${BLUE}🗄️  Database Connection Check${NC}"
echo "----------------------------"

# Check MongoDB connection
echo "Testing MongoDB Atlas connection..."
python -c "
import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient

try:
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    if not uri:
        print('❌ MONGODB_URI not found in .env file')
        sys.exit(1)
    
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✅ MongoDB Atlas connection successful')
    client.close()
    sys.exit(0)
except Exception as e:
    print(f'❌ MongoDB connection failed: {e}')
    sys.exit(1)
"
mongodb_status=$?

echo -e "\n${BLUE}🧪 API Functionality Test${NC}"
echo "---------------------------"

# Test sentiment analysis API
echo "Testing sentiment analysis endpoint..."
response=$(curl -s -X POST "http://localhost:8001/predict" \
    -H "Content-Type: application/json" \
    -d '{"review": "This movie is absolutely fantastic!", "movie_title": "Test Movie", "user_id": "test_user"}')

if echo "$response" | grep -q "sentiment"; then
    echo -e "${GREEN}✅ Sentiment analysis API is working${NC}"
    echo "Response: $response" | jq .
    api_test_status=0
else
    echo -e "${RED}❌ Sentiment analysis API test failed${NC}"
    echo "Response: $response"
    api_test_status=1
fi

echo -e "\n${BLUE}📊 Summary${NC}"
echo "-------"

# Calculate overall status
overall_status=0
if [ $api_service_status -ne 0 ] || [ $mlflow_service_status -ne 0 ]; then
    echo -e "${RED}❌ System services are not running properly${NC}"
    overall_status=1
fi

if [ $api_port_status -ne 0 ] || [ $mlflow_port_status -ne 0 ]; then
    echo -e "${RED}❌ Network ports are not listening${NC}"
    overall_status=1
fi

if [ $api_health_status -ne 0 ] || [ $api_docs_status -ne 0 ] || [ $mlflow_ui_status -ne 0 ]; then
    echo -e "${RED}❌ HTTP endpoints are not responding${NC}"
    overall_status=1
fi

if [ $mongodb_status -ne 0 ]; then
    echo -e "${RED}❌ Database connection failed${NC}"
    overall_status=1
fi

if [ $api_test_status -ne 0 ]; then
    echo -e "${RED}❌ API functionality test failed${NC}"
    overall_status=1
fi

if [ $overall_status -eq 0 ]; then
    echo -e "${GREEN}🎉 All systems are operational!${NC}"
    echo -e "${BLUE}📊 MLflow UI: http://localhost:5002${NC}"
    echo -e "${BLUE}🚀 API Server: http://localhost:8001${NC}"
    echo -e "${BLUE}📚 API Docs: http://localhost:8001/docs${NC}"
else
    echo -e "${YELLOW}⚠️  Some issues detected. Check the details above.${NC}"
    echo -e "${BLUE}🔧 Troubleshooting commands:${NC}"
    echo "  sudo systemctl status sentiment-api mlflow-server"
    echo "  sudo journalctl -u sentiment-api -f"
    echo "  sudo journalctl -u mlflow-server -f"
    echo "  netstat -tuln | grep -E ':(8001|5002)'"
fi

exit $overall_status
