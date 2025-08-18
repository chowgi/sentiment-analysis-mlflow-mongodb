#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup MLflow Setup
This script cleans up all MLflow-related files and directories
"""

import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_mlflow_files():
    """Clean up all MLflow-related files and directories"""
    
    logger.info("🧹 Starting MLflow cleanup...")
    
    # List of directories and files to clean up
    cleanup_items = [
        "mlflow_data",
        "mlruns",
        "tokenizer",
        "sample_output.txt"
    ]
    
    cleaned_items = []
    
    for item in cleanup_items:
        path = Path(item)
        
        if path.exists():
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                    logger.info(f"✅ Removed directory: {item}")
                else:
                    path.unlink()
                    logger.info(f"✅ Removed file: {item}")
                cleaned_items.append(item)
            except Exception as e:
                logger.warning(f"⚠️ Failed to remove {item}: {e}")
        else:
            logger.info(f"ℹ️ {item} does not exist, skipping")
    
    # Also clean up any tokenizer directories with patterns
    for tokenizer_dir in Path(".").glob("tokenizer*"):
        if tokenizer_dir.is_dir():
            try:
                shutil.rmtree(tokenizer_dir)
                logger.info(f"✅ Removed directory: {tokenizer_dir}")
                cleaned_items.append(str(tokenizer_dir))
            except Exception as e:
                logger.warning(f"⚠️ Failed to remove {tokenizer_dir}: {e}")
    
    if cleaned_items:
        logger.info(f"✅ Cleanup completed! Removed {len(cleaned_items)} items")
        logger.info(f"Cleaned items: {', '.join(cleaned_items)}")
    else:
        logger.info("ℹ️ No MLflow files found to clean up")
    
    return True

if __name__ == "__main__":
    cleanup_mlflow_files()
