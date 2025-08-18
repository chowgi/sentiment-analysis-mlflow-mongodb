#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local MLflow Server Setup for Mac
This script sets up a local MLflow tracking server with SQLite backend
"""

import mlflow
import subprocess
import os
import sys
from pathlib import Path

def setup_mlflow_local():
    """Set up MLflow with local SQLite backend"""
    
    # Create mlflow directory if it doesn't exist
    mlflow_dir = Path("mlflow_data")
    mlflow_dir.mkdir(exist_ok=True)
    
    # Set up tracking URI (SQLite for local development)
    MLFLOW_TRACKING_URI = f"sqlite:///{mlflow_dir}/mlflow.db"
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    # Create default experiment
    mlflow.set_experiment("Local Development")
    
    print(f"MLflow tracking URI set to: {MLFLOW_TRACKING_URI}")
    print(f"MLflow data directory: {mlflow_dir.absolute()}")
    
    return MLFLOW_TRACKING_URI

def start_mlflow_ui(tracking_uri, port=5000):
    """Start MLflow UI server"""
    
    print(f"\nStarting MLflow UI on port {port}...")
    print(f"Access the UI at: http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Start MLflow UI server
        subprocess.run([
            "mlflow", "ui", 
            "--backend-store-uri", tracking_uri,
            "--port", str(port),
            "--host", "0.0.0.0"  # Allow external connections
        ])
    except KeyboardInterrupt:
        print("\nMLflow UI server stopped.")
    except FileNotFoundError:
        print("Error: MLflow not found. Please install it first:")
        print("pip install mlflow")
        sys.exit(1)

def create_sample_experiment():
    """Create a sample experiment to test MLflow"""
    
    print("\nCreating sample experiment...")
    
    with mlflow.start_run(run_name="sample_run"):
        # Log some sample parameters
        mlflow.log_param("model_type", "sample_model")
        mlflow.log_param("dataset_size", 1000)
        
        # Log some sample metrics
        mlflow.log_metric("accuracy", 0.85)
        mlflow.log_metric("loss", 0.15)
        mlflow.log_metric("precision", 0.87)
        mlflow.log_metric("recall", 0.83)
        
        # Log a sample artifact (text file)
        sample_data = "This is sample model output data"
        with open("sample_output.txt", "w") as f:
            f.write(sample_data)
        mlflow.log_artifact("sample_output.txt")
        
        print("Sample experiment created successfully!")

if __name__ == "__main__":
    print("Setting up local MLflow server...")
    
    # Setup MLflow
    tracking_uri = setup_mlflow_local()
    
    # Create a sample experiment
    create_sample_experiment()
    
    # Start the UI
    start_mlflow_ui(tracking_uri, port=5001)
