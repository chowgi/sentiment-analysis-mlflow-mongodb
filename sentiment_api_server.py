#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sentiment Analysis API Server
FastAPI server that serves DistilBERT model via MLflow and stores results in MongoDB
"""

import mlflow
import mlflow.pytorch
import torch
from transformers import DistilBertTokenizer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
import os
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sentiment Analysis API",
    description="API for sentiment analysis using DistilBERT model served via MLflow",
    version="1.0.0"
)

# MongoDB configuration
MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise ValueError("MONGODB_URI not found in environment variables")
MONGO_DB = "imdb_reviews"
MONGO_COLLECTION = "sentiment_analysis"

# MLflow configuration
MLFLOW_TRACKING_URI = f"sqlite:///{Path('mlflow_data')}/mlflow.db"
MODEL_NAME = "distilbert-sentiment"

# Global variables for model and tokenizer
model = None
tokenizer = None

class ReviewRequest(BaseModel):
    """Request model for sentiment analysis"""
    review: str
    movie_title: Optional[str] = None
    user_id: Optional[str] = None

class SentimentResponse(BaseModel):
    """Response model for sentiment analysis"""
    review: str
    sentiment: str
    confidence: float
    timestamp: datetime
    movie_title: Optional[str] = None
    user_id: Optional[str] = None

def connect_mongodb():
    """Connect to MongoDB and return client and collection"""
    try:
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        
        # Test connection
        client.admin.command('ping')
        logger.info(f"Connected to MongoDB: {MONGO_URI}")
        logger.info(f"Database: {MONGO_DB}, Collection: {MONGO_COLLECTION}")
        
        return client, collection
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

def load_model_from_mlflow():
    """Load the model and tokenizer from MLflow"""
    global model, tokenizer
    
    try:
        # Set MLflow tracking URI
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        
        # Load the latest version of the model
        model_uri = f"models:/{MODEL_NAME}/latest"
        logger.info(f"Loading model from: {model_uri}")
        
        # Load the PyTorch model
        model = mlflow.pytorch.load_model(model_uri)
        model.eval()  # Set to evaluation mode
        
        # Find the registration run
        runs = mlflow.search_runs(
            filter_string=f"tags.mlflow.runName = '{MODEL_NAME}-registration'"
        )
        
        if runs.empty:
            logger.warning("No registration run found, loading tokenizer directly from HuggingFace")
            # Fallback: load tokenizer directly from HuggingFace
            tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
        else:
            # Load the tokenizer from artifacts
            run_id = runs.iloc[0]["run_id"]
            tokenizer_path = mlflow.artifacts.download_artifacts(
                run_id=run_id,
                artifact_path="tokenizer"
            )
            tokenizer = DistilBertTokenizer.from_pretrained(tokenizer_path)
        
        logger.info("Model and tokenizer loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to load model from MLflow: {e}")
        raise

def predict_sentiment(text: str) -> tuple[str, float]:
    """Predict sentiment for a given text"""
    global model, tokenizer
    
    if model is None or tokenizer is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Tokenize the text
        inputs = tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512, 
            padding=True
        )
        
        # Get prediction
        with torch.no_grad():
            outputs = model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            predicted_class = torch.argmax(probabilities, dim=1).item()
            confidence_score = probabilities[0][predicted_class].item()
        
        # Map class index to label
        labels = ["NEGATIVE", "POSITIVE"]
        predicted_label = labels[predicted_class]
        
        return predicted_label, confidence_score
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

def store_result_in_mongodb(collection, review_data: dict):
    """Store the sentiment analysis result in MongoDB"""
    try:
        result = collection.insert_one(review_data)
        logger.info(f"Stored result in MongoDB with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        logger.error(f"Failed to store result in MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Failed to store result")

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("Starting Sentiment Analysis API Server...")
    
    # Connect to MongoDB
    global mongo_client, mongo_collection
    mongo_client, mongo_collection = connect_mongodb()
    
    # Load model from MLflow
    load_model_from_mlflow()
    
    logger.info("API Server started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down API Server...")
    if 'mongo_client' in globals():
        mongo_client.close()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Sentiment Analysis API",
        "model": MODEL_NAME,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "mongodb_connected": mongo_client is not None
    }

@app.post("/predict", response_model=SentimentResponse)
async def predict_sentiment_endpoint(request: ReviewRequest):
    """Predict sentiment for a movie review"""
    
    if not request.review.strip():
        raise HTTPException(status_code=400, detail="Review text cannot be empty")
    
    try:
        # Predict sentiment
        sentiment, confidence = predict_sentiment(request.review)
        
        # Create response
        response = SentimentResponse(
            review=request.review,
            sentiment=sentiment,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            movie_title=request.movie_title,
            user_id=request.user_id
        )
        
        # Store in MongoDB
        review_data = {
            "review": request.review,
            "sentiment": sentiment,
            "confidence": confidence,
            "timestamp": response.timestamp,
            "movie_title": request.movie_title,
            "user_id": request.user_id,
            "model_version": MODEL_NAME
        }
        
        store_result_in_mongodb(mongo_collection, review_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reviews")
async def get_reviews(limit: int = 10, skip: int = 0):
    """Get recent sentiment analysis results from MongoDB"""
    try:
        cursor = mongo_collection.find().sort("timestamp", -1).skip(skip).limit(limit)
        reviews = list(cursor)
        
        # Convert ObjectId to string for JSON serialization
        for review in reviews:
            review["_id"] = str(review["_id"])
        
        return {
            "reviews": reviews,
            "total": len(reviews),
            "limit": limit,
            "skip": skip
        }
        
    except Exception as e:
        logger.error(f"Error fetching reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get statistics about sentiment analysis results"""
    try:
        total_reviews = mongo_collection.count_documents({})
        positive_reviews = mongo_collection.count_documents({"sentiment": "POSITIVE"})
        negative_reviews = mongo_collection.count_documents({"sentiment": "NEGATIVE"})
        
        avg_confidence = mongo_collection.aggregate([
            {"$group": {"_id": None, "avg_confidence": {"$avg": "$confidence"}}}
        ]).next()["avg_confidence"]
        
        return {
            "total_reviews": total_reviews,
            "positive_reviews": positive_reviews,
            "negative_reviews": negative_reviews,
            "positive_percentage": (positive_reviews / total_reviews * 100) if total_reviews > 0 else 0,
            "average_confidence": round(avg_confidence, 3) if avg_confidence else 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "sentiment_api_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
