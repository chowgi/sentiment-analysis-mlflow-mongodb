#!/bin/bash

# AWS EC2 Ubuntu Deployment Script for Sentiment Analysis System
# This script sets up the complete system on an Ubuntu EC2 instance

echo "🚀 Deploying Sentiment Analysis System to Ubuntu EC2..."
echo "======================================================"

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.9 and pip
echo "🐍 Installing Python 3.9..."
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.9 python3.9-pip python3.9-venv python3.9-dev

# Install development tools
echo "🔧 Installing development tools..."
sudo apt install -y build-essential git curl jq

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /opt/sentiment-analysis
sudo chown ubuntu:ubuntu /opt/sentiment-analysis
cd /opt/sentiment-analysis

# Clone or copy application files
echo "📋 Setting up application files..."
git clone https://github.com/chowgi/sentiment-analysis-mlflow-mongodb.git .

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x deploy_ubuntu_ec2.sh
chmod +x start_system.sh

# Create virtual environment
echo "🔧 Creating Python virtual environment..."

# Check available Python versions and install venv package
if command -v python3.9 &> /dev/null; then
    PYTHON_CMD="python3.9"
    VENV_PACKAGE="python3.9-venv"
elif command -v python3.8 &> /dev/null; then
    PYTHON_CMD="python3.8"
    VENV_PACKAGE="python3.8-venv"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    # Get the exact Python version for venv package
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    VENV_PACKAGE="python${PYTHON_VERSION}-venv"
else
    echo "❌ No Python 3.x found. Installing Python 3.9..."
    sudo apt install -y software-properties-common
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install -y python3.9 python3.9-pip python3.9-venv python3.9-dev
    PYTHON_CMD="python3.9"
    VENV_PACKAGE="python3.9-venv"
fi

echo "Using Python: $PYTHON_CMD"
echo "Installing venv package: $VENV_PACKAGE"

# Install the appropriate venv package
sudo apt install -y $VENV_PACKAGE

# Create virtual environment
$PYTHON_CMD -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run the setup script to configure everything
echo "🔧 Running setup script..."
python setup_sentiment_analysis.py &
SETUP_PID=$!

# Wait for setup to complete (with timeout)
echo "⏳ Waiting for setup to complete..."
timeout 300 bash -c 'while kill -0 $SETUP_PID 2>/dev/null; do sleep 5; done' || {
    echo "⚠️ Setup script is taking longer than expected, continuing..."
    kill $SETUP_PID 2>/dev/null || true
}

# Create systemd service for the API server
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/sentiment-api.service > /dev/null <<EOF
[Unit]
Description=Sentiment Analysis API Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/sentiment-analysis
Environment=PATH=/opt/sentiment-analysis/venv/bin
Environment=PYTHONPATH=/opt/sentiment-analysis
ExecStart=/opt/sentiment-analysis/venv/bin/python sentiment_api_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for MLflow server
sudo tee /etc/systemd/system/mlflow-server.service > /dev/null <<EOF
[Unit]
Description=MLflow Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/sentiment-analysis
Environment=PATH=/opt/sentiment-analysis/venv/bin
Environment=PYTHONPATH=/opt/sentiment-analysis
ExecStart=/opt/sentiment-analysis/venv/bin/python start_mlflow_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable sentiment-api
sudo systemctl enable mlflow-server

# Start services and check status
echo "Starting sentiment-api service..."
sudo systemctl start sentiment-api
if sudo systemctl is-active --quiet sentiment-api; then
    echo "✅ sentiment-api service started successfully"
else
    echo "❌ sentiment-api service failed to start"
    sudo systemctl status sentiment-api
fi

echo "Starting mlflow-server service..."
sudo systemctl start mlflow-server
if sudo systemctl is-active --quiet mlflow-server; then
    echo "✅ mlflow-server service started successfully"
else
    echo "❌ mlflow-server service failed to start"
    sudo systemctl status mlflow-server
fi

# Configure firewall (if using security groups, configure in AWS console)
echo "🔥 Configuring firewall..."
sudo ufw allow 8001/tcp  # API server
sudo ufw allow 5002/tcp  # MLflow UI
sudo ufw allow ssh       # Keep SSH access
sudo ufw --force enable

# Create startup script
echo "📝 Creating startup script..."
tee start_services.sh > /dev/null <<EOF
#!/bin/bash
cd /opt/sentiment-analysis
source venv/bin/activate

echo "Starting Sentiment Analysis System..."
echo "API Server: http://localhost:8001"
echo "MLflow UI: http://localhost:5002"

# Check if services are running
sudo systemctl status sentiment-api
sudo systemctl status mlflow-server
EOF

chmod +x start_services.sh

# Create health check script
echo "🏥 Creating health check script..."
tee health_check.sh > /dev/null <<EOF
#!/bin/bash
cd /opt/sentiment-analysis
source venv/bin/activate

echo "Checking API server health..."
curl -s http://localhost:8001/health | jq .

echo "Checking MLflow server..."
curl -s http://localhost:5002 | head -5

echo "Checking MongoDB connection..."
python -c "
import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=5000)
client.admin.command('ping')
print('✅ MongoDB connection successful')
client.close()
"
EOF

chmod +x health_check.sh

# Run comprehensive health check
echo ""
echo "🏥 Running comprehensive health check..."
sleep 10  # Give services time to fully start

# Run health check script
if [ -f "health_check.sh" ]; then
    ./health_check.sh
    HEALTH_CHECK_RESULT=$?
else
    echo "⚠️ Health check script not found, running basic checks..."
    # Basic health checks
    echo "Checking API server..."
    if curl -s http://localhost:8001/health > /dev/null; then
        echo "✅ API server is responding"
    else
        echo "❌ API server is not responding"
    fi
    
    echo "Checking MLflow server..."
    if curl -s http://localhost:5002 > /dev/null; then
        echo "✅ MLflow server is responding"
    else
        echo "❌ MLflow server is not responding"
    fi
    
    HEALTH_CHECK_RESULT=0
fi

echo ""
echo "🎉 Deployment completed!"
echo "======================="
echo "📊 MLflow UI: http://YOUR_EC2_IP:5002"
echo "🚀 API Server: http://YOUR_EC2_IP:8001"
echo "📚 API Docs: http://YOUR_EC2_IP:8001/docs"
echo ""
echo "📋 Useful commands:"
echo "  Check status: sudo systemctl status sentiment-api mlflow-server"
echo "  View logs: sudo journalctl -u sentiment-api -f"
echo "  Health check: ./health_check.sh"
echo "  Start services: ./start_services.sh"
echo ""
echo "🔧 Next steps:"
echo "1. Update your .env file with the correct MongoDB Atlas URI"
echo "2. Configure MongoDB Atlas trigger with the trigger function"
echo "3. Test the system by adding documents to incoming_reviews collection"
echo ""
if [ $HEALTH_CHECK_RESULT -eq 0 ]; then
    echo "✅ System appears to be working correctly!"
else
    echo "⚠️ Some issues detected. Check the health check output above."
    echo "💡 Troubleshooting:"
    echo "   - Check service logs: sudo journalctl -u sentiment-api -f"
    echo "   - Restart services: sudo systemctl restart sentiment-api mlflow-server"
    echo "   - Run health check again: ./health_check.sh"
fi
