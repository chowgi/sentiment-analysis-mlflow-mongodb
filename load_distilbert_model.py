#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load and Register DistilBERT Model with MLflow
This script loads the distilbert-base-uncased-finetuned-sst-2-english model
and registers it with MLflow for sentiment analysis
"""

import mlflow
import mlflow.pytorch
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import os
from pathlib import Path

def load_distilbert_model():
    """Load the DistilBERT model and tokenizer"""
    
    print("Loading DistilBERT model...")
    
    # Load model and tokenizer
    model_name = "distilbert-base-uncased-finetuned-sst-2-english"
    tokenizer = DistilBertTokenizer.from_pretrained(model_name)
    model = DistilBertForSequenceClassification.from_pretrained(model_name)
    
    print(f"Model loaded: {model_name}")
    return model, tokenizer

def create_prediction_function(model, tokenizer):
    """Create a prediction function for MLflow"""
    
    def predict_sentiment(text):
        """
        Predict sentiment for a given text
        Returns: (label, score)
        """
        # Tokenize the text
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
        
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
    
    return predict_sentiment

def register_model_with_mlflow(model, tokenizer, model_name="distilbert-sentiment"):
    """Register the model with MLflow"""
    
    # Set up MLflow tracking
    mlflow_dir = Path("mlflow_data")
    mlflow_dir.mkdir(exist_ok=True)
    MLFLOW_TRACKING_URI = f"sqlite:///{mlflow_dir}/mlflow.db"
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    # Create experiment
    mlflow.set_experiment("Sentiment Analysis")
    
    print(f"Registering model with MLflow...")
    print(f"Tracking URI: {MLFLOW_TRACKING_URI}")
    
    with mlflow.start_run(run_name=f"{model_name}-registration"):
        # Log model parameters
        mlflow.log_param("model_name", "distilbert-base-uncased-finetuned-sst-2-english")
        mlflow.log_param("task", "sentiment_analysis")
        mlflow.log_param("labels", ["NEGATIVE", "POSITIVE"])
        
        # Log model metrics (placeholder)
        mlflow.log_metric("model_size_mb", 260)  # Approximate size
        
        # Create prediction function
        predict_fn = create_prediction_function(model, tokenizer)
        
        # Log the model
        mlflow.pytorch.log_model(
            pytorch_model=model,
            artifact_path="model",
            registered_model_name=model_name,
            code_paths=[__file__]
        )
        
        # Log the tokenizer separately
        tokenizer_path = "tokenizer"
        tokenizer.save_pretrained(tokenizer_path)
        mlflow.log_artifact(tokenizer_path, "tokenizer")
        
        # Test the model
        test_text = "This movie is absolutely fantastic!"
        label, score = predict_fn(test_text)
        print(f"Test prediction: '{test_text}' -> {label} (confidence: {score:.3f})")
        
        # Log test results
        mlflow.log_param("test_text", test_text)
        mlflow.log_metric("test_confidence", score)
        
        print(f"Model registered successfully as '{model_name}'")
        print(f"Run ID: {mlflow.active_run().info.run_id}")
        
        return mlflow.active_run().info.run_id

def main():
    """Main function to load and register the model"""
    
    print("=== DistilBERT Model Registration with MLflow ===")
    
    try:
        # Load model
        model, tokenizer = load_distilbert_model()
        
        # Register with MLflow
        run_id = register_model_with_mlflow(model, tokenizer)
        
        print("\n=== Registration Complete ===")
        print(f"Model is ready for serving!")
        print(f"Run ID: {run_id}")
        print(f"Model name: distilbert-sentiment")
        
    except Exception as e:
        print(f"Error during model registration: {e}")
        raise

if __name__ == "__main__":
    main()
