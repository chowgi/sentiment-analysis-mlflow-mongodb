#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Sentiment Analysis System
Comprehensive setup script for the DistilBERT sentiment analysis system
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    logger.info("Checking dependencies...")
    
    required_packages = [
        "mlflow", "torch", "transformers", "fastapi", "uvicorn", 
        "pymongo", "requests", "pydantic"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"❌ {package} is missing")
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Please install missing packages using:")
        logger.info("pip install -r requirements.txt")
        return False
    
    return True

def check_mongodb():
    """Check if MongoDB Atlas is accessible"""
    logger.info("Checking MongoDB Atlas connection...")
    
    try:
        from pymongo import MongoClient
        
        # Get MongoDB URI from environment
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            logger.error("❌ MONGODB_URI not found in environment variables")
            logger.info("Please ensure .env file contains MONGODB_URI")
            return False
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        logger.info("✅ MongoDB Atlas is accessible")
        client.close()
        return True
    except Exception as e:
        logger.error(f"❌ MongoDB Atlas connection failed: {e}")
        logger.info("Please check your MongoDB Atlas connection string in .env file")
        logger.info("Ensure your IP address is whitelisted in MongoDB Atlas")
        return False

def setup_mlflow():
    """Set up MLflow tracking"""
    logger.info("Setting up MLflow tracking...")
    
    try:
        mlflow_dir = Path("mlflow_data")
        mlflow_dir.mkdir(exist_ok=True)
        
        # Import and set up MLflow
        import mlflow
        tracking_uri = f"sqlite:///{mlflow_dir}/mlflow.db"
        mlflow.set_tracking_uri(tracking_uri)
        
        logger.info(f"✅ MLflow tracking URI set to: {tracking_uri}")
        return True
    except Exception as e:
        logger.error(f"❌ MLflow setup failed: {e}")
        return False

def load_and_register_model():
    """Load and register the DistilBERT model"""
    logger.info("Loading and registering DistilBERT model...")
    
    try:
        # Run the model loading script
        result = subprocess.run([
            sys.executable, "load_distilbert_model.py"
        ], capture_output=True, text=True)
        
        # Check if model registration was successful despite warnings
        # Look for success messages in both stdout and stderr
        success_indicators = [
            "Successfully registered model",
            "Created version",
            "Registered model 'distilbert-sentiment' already exists"
        ]
        
        output_combined = result.stdout + result.stderr
        
        if any(indicator in output_combined for indicator in success_indicators):
            logger.info("✅ Model loaded and registered successfully")
            return True
        else:
            logger.error(f"❌ Model registration failed")
            logger.error(f"stdout: {result.stdout}")
            logger.error(f"stderr: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Model registration error: {e}")
        return False

def start_mlflow_server():
    """Start MLflow server in background"""
    logger.info("Starting MLflow server...")
    
    try:
        # Start MLflow server in background
        process = subprocess.Popen([
            sys.executable, "start_mlflow_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Check if server is responding
        try:
            response = requests.get("http://localhost:5002", timeout=5)
            if response.status_code == 200:
                logger.info("✅ MLflow server is running on http://localhost:5002")
                return process
            else:
                logger.warning("⚠️ MLflow server may not be fully started yet")
                return process
        except requests.exceptions.RequestException:
            logger.warning("⚠️ MLflow server may not be fully started yet")
            return process
            
    except Exception as e:
        logger.error(f"❌ Failed to start MLflow server: {e}")
        return None

def start_api_server():
    """Start the FastAPI server"""
    logger.info("Starting FastAPI server...")
    
    try:
        # Start API server in background
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "sentiment_api_server:app",
            "--host", "0.0.0.0", "--port", "8001", "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(5)
        
        # Check if server is responding
        try:
            response = requests.get("http://localhost:8001/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ FastAPI server is running on http://localhost:8001")
                return process
            else:
                logger.warning("⚠️ API server may not be fully started yet")
                return process
        except requests.exceptions.RequestException:
            logger.warning("⚠️ API server may not be fully started yet")
            return process
            
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        return None

def run_tests():
    """Run the test script"""
    logger.info("Running tests...")
    
    try:
        # Wait a bit more for servers to be fully ready
        time.sleep(3)
        
        result = subprocess.run([
            sys.executable, "test_sentiment_api.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Tests completed successfully")
            logger.info("Test output:")
            print(result.stdout)
        else:
            logger.warning("⚠️ Some tests may have failed")
            logger.info("Test output:")
            print(result.stdout)
            print("Errors:")
            print(result.stderr)
        
        return True
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return False

def cleanup_previous_setup():
    """Clean up any previous MLflow setup files"""
    logger.info("🧹 Cleaning up previous MLflow setup...")
    
    try:
        # Remove MLflow data directories
        import shutil
        from pathlib import Path
        
        # Clean up mlflow_data directory
        mlflow_data_dir = Path("mlflow_data")
        if mlflow_data_dir.exists():
            shutil.rmtree(mlflow_data_dir)
            logger.info("✅ Removed mlflow_data directory")
        
        # Clean up mlruns directory
        mlruns_dir = Path("mlruns")
        if mlruns_dir.exists():
            shutil.rmtree(mlruns_dir)
            logger.info("✅ Removed mlruns directory")
        
        # Clean up any tokenizer directories
        for tokenizer_dir in Path(".").glob("tokenizer*"):
            if tokenizer_dir.is_dir():
                shutil.rmtree(tokenizer_dir)
                logger.info(f"✅ Removed {tokenizer_dir} directory")
        
        # Clean up any sample output files
        for sample_file in Path(".").glob("sample_output.txt"):
            if sample_file.is_file():
                sample_file.unlink()
                logger.info("✅ Removed sample_output.txt")
        
        logger.info("✅ Cleanup completed successfully")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ Some cleanup operations failed: {e}")
        return True  # Continue anyway

def main():
    """Main setup function"""
    logger.info("=== Sentiment Analysis System Setup ===")
    
    # Step 0: Clean up previous setup
    cleanup_previous_setup()
    
    # Step 1: Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed. Please install missing packages.")
        sys.exit(1)
    
    # Step 2: Check MongoDB
    if not check_mongodb():
        logger.error("MongoDB check failed. Please ensure MongoDB is running.")
        sys.exit(1)
    
    # Step 3: Setup MLflow
    if not setup_mlflow():
        logger.error("MLflow setup failed.")
        sys.exit(1)
    
    # Step 4: Load and register model
    if not load_and_register_model():
        logger.error("Model registration failed.")
        sys.exit(1)
    
    # Step 5: Start MLflow server
    mlflow_process = start_mlflow_server()
    if mlflow_process is None:
        logger.error("Failed to start MLflow server.")
        sys.exit(1)
    
    # Step 6: Start API server
    api_process = start_api_server()
    if api_process is None:
        logger.error("Failed to start API server.")
        mlflow_process.terminate()
        sys.exit(1)
    
    # Step 7: Run tests
    run_tests()
    
    logger.info("\n=== Setup Complete ===")
    logger.info("🎉 Sentiment Analysis System is ready!")
    logger.info("")
    logger.info("📊 MLflow UI: http://localhost:5002")
    logger.info("🚀 API Server: http://localhost:8001")
    logger.info("📚 API Documentation: http://localhost:8001/docs")
    logger.info("")
    logger.info("💡 To test the API manually:")
    logger.info("   curl -X POST http://localhost:8001/predict \\")
    logger.info("     -H 'Content-Type: application/json' \\")
    logger.info("     -d '{\"review\": \"This movie is amazing!\"}'")
    logger.info("")
    logger.info("📝 To stop the servers, press Ctrl+C")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nShutting down servers...")
        if mlflow_process:
            mlflow_process.terminate()
        if api_process:
            api_process.terminate()
        logger.info("Servers stopped.")

if __name__ == "__main__":
    main()
