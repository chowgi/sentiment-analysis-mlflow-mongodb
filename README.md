# Sentiment Analysis System with DistilBERT and MLflow

This project implements a complete sentiment analysis system using the DistilBERT model, served via MLflow, with a FastAPI backend that stores results in MongoDB.

## 🎯 Features

- **DistilBERT Model**: Uses `distilbert-base-uncased-finetuned-sst-2-english` for sentiment analysis
- **MLflow Integration**: Model versioning, tracking, and serving via MLflow
- **FastAPI Backend**: RESTful API for sentiment analysis requests
- **MongoDB Storage**: Stores review data, sentiment predictions, and metadata
- **Comprehensive Testing**: Built-in test suite with sample movie reviews

## 📋 Prerequisites

### System Requirements
- Python 3.8+
- MongoDB Atlas account (connection string in .env file)
- 4GB+ RAM (for model loading)

### Dependencies
All required packages are listed in `requirements.txt`:
- mlflow >= 2.8.0
- transformers >= 4.30.0
- torch >= 2.0.0
- fastapi >= 0.100.0
- uvicorn >= 0.23.0
- pymongo >= 4.5.0
- requests >= 2.28.0
- pydantic >= 1.10.0

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure MongoDB Atlas
Ensure your `.env` file contains the MongoDB Atlas connection string:
```bash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

Make sure your IP address is whitelisted in MongoDB Atlas Network Access settings.

### 3. Run Complete Setup
```bash
python setup_sentiment_analysis.py
```

This script will:
- Clean up any previous MLflow setup files
- Check all dependencies
- Verify MongoDB Atlas connection
- Load and register the DistilBERT model with MLflow
- Start the MLflow server
- Start the FastAPI server
- Run comprehensive tests

## 📁 Project Structure

```
mlflow/
├── load_distilbert_model.py      # Model loading and registration
├── sentiment_api_server.py       # FastAPI server
├── start_mlflow_server.py        # MLflow server startup
├── test_sentiment_api.py         # Test suite
├── setup_sentiment_analysis.py   # Complete setup script
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── mlflow_data/                  # MLflow artifacts and database
└── mlruns/                       # MLflow experiment runs
```

## 🔧 Manual Setup (Alternative)

If you prefer to run components individually:

### 1. Load and Register Model
```bash
python load_distilbert_model.py
```

### 2. Start MLflow Server
```bash
python start_mlflow_server.py
```

### 3. Start API Server
```bash
python sentiment_api_server.py
```

### 4. Run Tests
```bash
python test_sentiment_api.py
```

### 5. Cleanup (if needed)
If you encounter issues with previous setups, you can clean up all MLflow files:
```bash
python cleanup_mlflow.py
```

## 🌐 API Endpoints

### Base URL
- **API Server**: http://localhost:8001
- **MLflow UI**: http://localhost:5002

### Available Endpoints

#### Health Check
```bash
GET /health
```
Returns system health status.

#### Predict Sentiment
```bash
POST /predict
Content-Type: application/json

{
  "review": "This movie is absolutely fantastic!",
  "movie_title": "The Great Adventure",
  "user_id": "user123"
}
```

Response:
```json
{
  "review": "This movie is absolutely fantastic!",
  "sentiment": "POSITIVE",
  "confidence": 0.987,
  "timestamp": "2024-01-15T10:30:00.000Z",
  "movie_title": "The Great Adventure",
  "user_id": "user123"
}
```

#### Get Recent Reviews
```bash
GET /reviews?limit=10&skip=0
```

#### Get Statistics
```bash
GET /stats
```

## 🗄️ MongoDB Schema

The system stores data in the `imdb_reviews` database, `sentiment_analysis` collection:

```json
{
  "_id": "ObjectId",
  "review": "Movie review text",
  "sentiment": "POSITIVE|NEGATIVE",
  "confidence": 0.987,
  "timestamp": "2024-01-15T10:30:00.000Z",
  "movie_title": "Movie Title",
  "user_id": "user123",
  "model_version": "distilbert-sentiment"
}
```

## 🧪 Testing

### Automated Tests
Run the complete test suite:
```bash
python test_sentiment_api.py
```

### Manual Testing
Test the API manually using curl:
```bash
# Health check
curl http://localhost:8001/health

# Predict sentiment
curl -X POST http://localhost:8001/predict \
  -H 'Content-Type: application/json' \
  -d '{"review": "This movie is amazing!", "movie_title": "Test Movie"}'

# Get recent reviews
curl http://localhost:8001/reviews?limit=5

# Get statistics
curl http://localhost:8001/stats
```

## 📊 MLflow Integration

### Model Registry
- Model name: `distilbert-sentiment`
- Version: Latest version is automatically loaded
- Artifacts: Model weights and tokenizer

### Tracking
- Experiment: "Sentiment Analysis"
- Metrics: Model size, confidence scores
- Parameters: Model configuration, labels

### UI Access
Visit http://localhost:5000 to access the MLflow UI for:
- Model registry management
- Experiment tracking
- Artifact browsing

## 🔍 Troubleshooting

### Common Issues

#### MongoDB Atlas Connection Failed
```bash
# Check if .env file exists and contains MONGODB_URI
cat .env

# Ensure your IP address is whitelisted in MongoDB Atlas
# Go to Network Access in MongoDB Atlas dashboard
```

#### Model Loading Issues
```bash
# Clean up previous setup
python cleanup_mlflow.py

# Or manually clean up
rm -rf mlflow_data/ mlruns/ tokenizer*/ sample_output.txt

# Re-run setup
python setup_sentiment_analysis.py
```

#### Port Already in Use
```bash
# Check what's using the ports
lsof -i :8000
lsof -i :5000

# Kill processes if needed
kill -9 <PID>
```

### Logs
- API Server logs: Check terminal output
- MLflow logs: Check terminal output
- MongoDB logs: Check system logs

## 🚀 Production Deployment

For production deployment, consider:

1. **Environment Variables**:
   ```bash
   export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
   export MLFLOW_TRACKING_URI="your-production-mlflow-uri"
   ```

2. **Process Management**: Use systemd, supervisor, or Docker

3. **Load Balancing**: Use nginx or similar

4. **Monitoring**: Add health checks and metrics

5. **Security**: Add authentication and rate limiting

## 📝 License

This project is for educational and demonstration purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!
