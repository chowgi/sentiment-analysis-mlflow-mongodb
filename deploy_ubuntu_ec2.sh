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
# Note: You'll need to copy your application files here
# Either via SCP, git clone, or other method

# Create virtual environment
echo "🔧 Creating Python virtual environment..."
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

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
ExecStart=/opt/sentiment-analysis/venv/bin/python sentiment_api_server.py
Restart=always
RestartSec=10

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
ExecStart=/opt/sentiment-analysis/venv/bin/python start_mlflow_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable sentiment-api
sudo systemctl enable mlflow-server
sudo systemctl start sentiment-api
sudo systemctl start mlflow-server

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
echo "Checking API server health..."
curl -s http://localhost:8001/health | jq .

echo "Checking MLflow server..."
curl -s http://localhost:5002 | head -5

echo "Checking MongoDB connection..."
python3 -c "
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
