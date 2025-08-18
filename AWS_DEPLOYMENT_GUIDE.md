# AWS EC2 Deployment Guide for Sentiment Analysis System

This guide will help you deploy the complete sentiment analysis system with MongoDB Atlas triggers on AWS EC2.

## 🎯 **System Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MongoDB Atlas │    │   AWS EC2       │    │   External      │
│   (Trigger)     │    │   (API Server)  │    │   Applications  │
│                 │    │                 │    │                 │
│ incoming_reviews│───▶│ sentiment_api   │◀───│ Add Reviews     │
│ collection      │    │ server          │    │ via API         │
│                 │    │                 │    │                 │
│ sentiment_      │◀───│ MLflow Server   │    │ View Results    │
│ analysis        │    │                 │    │ via API         │
│ collection      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 **Step 1: AWS EC2 Setup**

### **1.1 Launch EC2 Instance**
- **Instance Type**: t3.medium or larger (recommended: t3.large for ML models)
- **AMI**: Ubuntu 20.04 or 22.04 (recommended)
- **Storage**: At least 20GB
- **Security Groups**: 
  - Port 22 (SSH)
  - Port 8001 (API Server)
  - Port 5002 (MLflow UI)

### **1.2 Connect to EC2**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

## 📦 **Step 2: Deploy Application**

### **2.1 Copy Application Files**
```bash
# Option 1: SCP (from your local machine)
scp -i your-key.pem -r /path/to/mlflow/* ubuntu@your-ec2-ip:/opt/sentiment-analysis/

# Option 2: Git clone (recommended)
cd /opt
sudo git clone https://github.com/chowgi/
sentiment-analysis-mlflow-mongodb.git sentiment-analysis
sudo chown -R ubuntu:ubuntu sentiment-analysis
cd sentiment-analysis
```

### **2.2 Run Deployment Script**
```bash
# For Ubuntu EC2 instances (recommended)
chmod +x deploy_ubuntu_ec2.sh
./deploy_ubuntu_ec2.sh

# Or for Amazon Linux instances
chmod +x deploy_to_ec2.sh
./deploy_to_ec2.sh
```

### **2.3 Update Environment Variables**
```bash
# Edit .env file with your MongoDB Atlas URI
nano .env

# Content should be:
MONGODB_URI=mongodb+srv://username:password@your-cluster.mongodb.net/?retryWrites=true&w=majority
HF_TOKEN=your_huggingface_token_if_needed
```

## 🔧 **Step 3: MongoDB Atlas Trigger Setup**

### **3.1 Create Trigger in MongoDB Atlas**
1. Go to your MongoDB Atlas dashboard
2. Navigate to **App Services** → **Triggers**
3. Click **"Create Trigger"**
4. Configure the trigger:
   - **Name**: `sentiment_analysis_trigger`
   - **Type**: Database
   - **Event Type**: Insert
   - **Database**: `imdb_reviews`
   - **Collection**: `incoming_reviews`
   - **Function**: Copy the code from `mongodb_trigger.js`

### **3.2 Update Trigger URL**
In the trigger function, update the API URL to point to your EC2 instance:
```javascript
// Change this line in mongodb_trigger.js
url: "http://YOUR_EC2_PRIVATE_IP:8001/predict",
```

**Note**: Use the private IP address for better security and performance.

## 🧪 **Step 4: Testing the System**

### **4.1 Test API Server**
```bash
# Health check
curl http://YOUR_EC2_IP:8001/health

# Direct prediction
curl -X POST http://YOUR_EC2_IP:8001/predict \
  -H 'Content-Type: application/json' \
  -d '{"review": "This movie is amazing!", "movie_title": "Test Movie"}'
```

### **4.2 Test MongoDB Trigger**
```bash
# Run the test script
python3 test_trigger.py
```

### **4.3 Monitor Results**
```bash
# Check API results
curl http://YOUR_EC2_IP:8001/reviews

# Check MongoDB directly
python3 -c "
import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['imdb_reviews']
print('Incoming reviews:', db['incoming_reviews'].count_documents({}))
print('Processed results:', db['sentiment_analysis'].count_documents({}))
client.close()
"
```

## 📊 **Step 5: Monitoring and Management**

### **5.1 Service Management**
```bash
# Check service status
sudo systemctl status sentiment-api mlflow-server

# View logs
sudo journalctl -u sentiment-api -f
sudo journalctl -u mlflow-server -f

# Restart services
sudo systemctl restart sentiment-api mlflow-server
```

### **5.2 Health Monitoring**
```bash
# Run health check
./health_check.sh

# Monitor system resources
htop
df -h
```

## 🔒 **Step 6: Security Considerations**

### **6.1 Network Security**
- Configure AWS Security Groups properly
- Use private subnets for the EC2 instance
- Consider using Application Load Balancer for production

### **6.2 Application Security**
- Use HTTPS in production
- Implement API authentication
- Regularly update dependencies

### **6.3 MongoDB Atlas Security**
- Use IP whitelisting (add your EC2 public IP)
- Use database user with minimal required permissions
- Enable audit logging

## 📈 **Step 7: Production Considerations**

### **7.1 Scaling**
- Use Auto Scaling Groups for high availability
- Consider using ECS/EKS for containerized deployment
- Implement load balancing

### **7.2 Monitoring**
- Set up CloudWatch alarms
- Implement application logging
- Monitor API response times and error rates

### **7.3 Backup and Recovery**
- Regular MongoDB Atlas backups
- EC2 instance snapshots
- Application configuration backups

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Ubuntu vs Amazon Linux Differences**
- **User**: Ubuntu uses `ubuntu`, Amazon Linux uses `ec2-user`
- **Package Manager**: Ubuntu uses `apt`, Amazon Linux uses `yum`
- **Firewall**: Ubuntu uses `ufw`, Amazon Linux uses `firewalld`
- **Use the appropriate deployment script**: `deploy_ubuntu_ec2.sh` for Ubuntu

#### **API Server Not Starting**
```bash
# Check logs
sudo journalctl -u sentiment-api -f

# Check dependencies
source venv/bin/activate
pip list | grep -E "(mlflow|torch|transformers)"
```

#### **MongoDB Connection Issues**
```bash
# Test connection
python3 -c "
import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=5000)
client.admin.command('ping')
print('Connection successful')
client.close()
"
```

#### **Trigger Not Firing**
- Check MongoDB Atlas App Services logs
- Verify trigger configuration
- Ensure API server is accessible from Atlas
- Check if using correct IP address (private vs public)

#### **Firewall Issues on Ubuntu**
```bash
# Check UFW status
sudo ufw status

# Allow ports if needed
sudo ufw allow 8001/tcp
sudo ufw allow 5002/tcp
sudo ufw allow ssh
```

## 📞 **Support**

For issues or questions:
1. Check the logs: `sudo journalctl -u sentiment-api -f`
2. Verify MongoDB Atlas trigger logs
3. Test API endpoints manually
4. Check system resources: `htop`, `df -h`
5. Ensure you're using the correct deployment script for your OS
6. Check firewall settings: `sudo ufw status`

## 🎉 **Success Indicators**

Your deployment is successful when:
- ✅ API server responds to health checks
- ✅ MLflow UI is accessible
- ✅ MongoDB trigger processes new reviews automatically
- ✅ Sentiment analysis results appear in `sentiment_analysis` collection
- ✅ Services restart automatically after EC2 reboot
