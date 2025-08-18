#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load Dataset to MongoDB
This script loads HuggingFace datasets into MongoDB similar to telstra_ods_mlflow.py
"""

import os
import pymongo
from datasets import load_dataset
from dotenv import load_dotenv
import mlflow
from transformers import pipeline
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_mongodb_connection():
    """Set up MongoDB connection using environment variables"""
    
    # Get MongoDB URI from environment
    mongo_uri = os.getenv('MONGODB_URI')
    if not mongo_uri:
        raise ValueError("MONGODB_URI not found in environment variables")
    
    # Get database name (you can customize this)
    db_name = "mlflow_demo"
    
    # Create MongoDB client
    mongo_client = pymongo.MongoClient(mongo_uri, appname="mlflow_demo")
    db = mongo_client[db_name]
    
    logger.info(f"Connected to MongoDB database: {db_name}")
    return mongo_client, db

def setup_mlflow():
    """Set up MLflow tracking"""
    
    # Set up tracking URI (SQLite for local development)
    MLFLOW_TRACKING_URI = "sqlite:///mlflow_data/mlflow.db"
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("Dataset Processing")
    
    logger.info(f"MLflow tracking URI set to: {MLFLOW_TRACKING_URI}")
    return MLFLOW_TRACKING_URI

def load_dataset_with_auth():
    """Load dataset from HuggingFace with authentication"""
    
    # Get HuggingFace token from environment
    hf_token = os.getenv('HF_TOKEN')
    if not hf_token:
        logger.warning("HF_TOKEN not found, loading dataset without authentication")
        dataset = load_dataset("imdb", split="test[:100]")
    else:
        logger.info("Loading dataset with HuggingFace authentication")
        dataset = load_dataset("imdb", split="test[:100]", token=hf_token)
    
    return dataset

def setup_sentiment_analyzer():
    """Set up sentiment analysis pipeline"""
    
    logger.info("Setting up sentiment analysis pipeline...")
    classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    return classifier

def log_sentiment_to_mlflow(review_text, review_id, classifier):
    """Log sentiment analysis results to MLflow"""
    
    with mlflow.start_run(run_name=f"review_{review_id}"):
        # Truncate the review text to the maximum sequence length of the model (512)
        truncated_review_text = review_text[:512]
        result = classifier(truncated_review_text)[0]
        
        # Log review and results
        mlflow.log_param("review_id", review_id)
        mlflow.log_param("review_text", review_text)  # Log the original text
        mlflow.log_param("truncated_review_text", truncated_review_text)  # Log the truncated text
        mlflow.log_metric("sentiment_score", result["score"])
        mlflow.log_param("sentiment_label", result["label"])
        
        logger.info(f"Review {review_id}: {result['label']} (Confidence: {result['score']:.4f})")
        
        return result

def process_dataset_and_store():
    """Main function to process dataset and store in MongoDB"""
    
    try:
        # Setup connections
        mongo_client, db = setup_mongodb_connection()
        setup_mlflow()
        
        # Load dataset
        logger.info("Loading IMDB dataset...")
        dataset = load_dataset_with_auth()
        
        # Setup sentiment analyzer
        classifier = setup_sentiment_analyzer()
        
        # Get the collection
        collection = db["imdb_reviews"]
        
        logger.info("Processing dataset and storing in MongoDB...")
        
        # Process each item in the dataset
        for idx, item in enumerate(dataset):
            try:
                # Perform sentiment analysis
                truncated_review_text = item["text"][:512]
                result = classifier(truncated_review_text)[0]
                
                # Create document for MongoDB
                document = {
                    "text": item["text"],
                    "original_label": item["label"],  # 0 for negative, 1 for positive
                    "sentiment_label": result["label"],
                    "sentiment_score": result["score"],
                    "review_id": idx,
                    "dataset_split": "test"
                }
                
                # Insert into MongoDB
                collection.insert_one(document)
                
                # Log to MLflow
                log_sentiment_to_mlflow(item["text"], idx, classifier)
                
                if (idx + 1) % 10 == 0:
                    logger.info(f"Processed {idx + 1} reviews...")
                    
            except Exception as e:
                logger.error(f"Error processing review {idx}: {e}")
                continue
        
        logger.info(f"Successfully processed and stored {len(dataset)} reviews in MongoDB")
        
        # Print some statistics
        total_docs = collection.count_documents({})
        positive_sentiments = collection.count_documents({"sentiment_label": "POSITIVE"})
        negative_sentiments = collection.count_documents({"sentiment_label": "NEGATIVE"})
        
        logger.info(f"Database statistics:")
        logger.info(f"  Total documents: {total_docs}")
        logger.info(f"  Positive sentiments: {positive_sentiments}")
        logger.info(f"  Negative sentiments: {negative_sentiments}")
        
        # Close MongoDB connection
        mongo_client.close()
        
    except Exception as e:
        logger.error(f"Error in process_dataset_and_store: {e}")
        raise

def test_mongodb_connection():
    """Test MongoDB connection and create a sample document"""
    
    try:
        mongo_client, db = setup_mongodb_connection()
        collection = db["test_collection"]
        
        # Insert a test document
        test_doc = {"test": "connection", "status": "success"}
        result = collection.insert_one(test_doc)
        
        logger.info(f"MongoDB connection test successful. Inserted document ID: {result.inserted_id}")
        
        # Clean up test document
        collection.delete_one({"_id": result.inserted_id})
        
        mongo_client.close()
        return True
        
    except Exception as e:
        logger.error(f"MongoDB connection test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting dataset loading process...")
    
    # Test MongoDB connection first
    if test_mongodb_connection():
        logger.info("MongoDB connection test passed. Proceeding with dataset processing...")
        process_dataset_and_store()
    else:
        logger.error("MongoDB connection test failed. Please check your connection settings.")

