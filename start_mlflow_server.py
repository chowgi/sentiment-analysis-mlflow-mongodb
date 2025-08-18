#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start MLflow Server for Model Serving
This script starts the MLflow server to serve the registered DistilBERT model
"""

import subprocess
import sys
import os
from pathlib import Path

def start_mlflow_server():
    """Start MLflow server for model serving"""
    
    # Set up paths
    mlflow_dir = Path("mlflow_data")
    mlflow_dir.mkdir(exist_ok=True)
    
    # MLflow tracking URI
    tracking_uri = f"sqlite:///{mlflow_dir}/mlflow.db"
    
    print("=== Starting MLflow Server ===")
    print(f"Tracking URI: {tracking_uri}")
    print(f"Model serving will be available at: http://localhost:5002")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Start MLflow server
        subprocess.run([
            "mlflow", "server",
            "--backend-store-uri", tracking_uri,
            "--default-artifact-root", str(mlflow_dir / "artifacts"),
            "--host", "0.0.0.0",
            "--port", "5002"
        ])
    except KeyboardInterrupt:
        print("\nMLflow server stopped.")
    except FileNotFoundError:
        print("Error: MLflow not found. Please install it first:")
        print("pip install mlflow")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting MLflow server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_mlflow_server()
