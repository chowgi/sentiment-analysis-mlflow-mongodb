import json
import boto3
import pymongo
import os
from datetime import datetime
from typing import Dict, Any

def lambda_handler(event, context):
    """
    Lambda function to process MongoDB Atlas events via EventBridge
    Calls SageMaker endpoint directly and updates MongoDB with results
    """
    
    try:
        # Extract the document from the event
        detail = event['detail']
        full_document = detail['fullDocument']
        
        print(f"Processing document: {full_document.get('_id')}")
        
        # Call SageMaker endpoint
        sentiment_result = call_sagemaker_endpoint(full_document)
        
        # Store result in MongoDB
        store_result_in_mongodb(full_document, sentiment_result)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Review processed successfully',
                'document_id': str(full_document.get('_id')),
                'sentiment': sentiment_result['sentiment']
            })
        }
        
    except Exception as e:
        print(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to process review'
            })
        }

def call_sagemaker_endpoint(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call SageMaker endpoint for sentiment analysis
    """
    # SageMaker configuration
    ENDPOINT_NAME = os.environ.get('SAGEMAKER_ENDPOINT_NAME', 'distilbert-sentiment-endpoint')
    REGION = os.environ.get('AWS_REGION', 'ap-southeast-2')
    
    # Initialize SageMaker runtime client
    runtime = boto3.client('sagemaker-runtime', region_name=REGION)
    
    # Prepare the input data
    review_text = document.get('review', '')
    
    # Format input for SageMaker endpoint
    # Adjust this based on your model's expected input format
    input_data = {
        "review": review_text,
        "movie_title": document.get('movie_title'),
        "user_id": document.get('user_id')
    }
    
    # Convert to JSON string
    input_json = json.dumps(input_data)
    
    print(f"Calling SageMaker endpoint: {ENDPOINT_NAME}")
    print(f"Input: {input_json}")
    
    try:
        # Call the SageMaker endpoint
        response = runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType='application/json',
            Body=input_json
        )
        
        # Parse the response
        result = json.loads(response['Body'].read().decode())
        
        print(f"SageMaker response: {result}")
        
        # Format the result
        sentiment_result = {
            'review': review_text,
            'sentiment': result.get('sentiment', 'UNKNOWN'),
            'confidence': result.get('confidence', 0.0),
            'timestamp': datetime.utcnow().isoformat(),
            'movie_title': document.get('movie_title'),
            'user_id': document.get('user_id'),
            'model_version': 'sagemaker-distilbert',
            'source_document_id': str(document.get('_id')),
            'processed_at': datetime.utcnow().isoformat()
        }
        
        return sentiment_result
        
    except Exception as e:
        print(f"Error calling SageMaker endpoint: {str(e)}")
        raise Exception(f"SageMaker endpoint call failed: {str(e)}")

def store_result_in_mongodb(original_document: Dict[str, Any], sentiment_result: Dict[str, Any]):
    """
    Store the sentiment analysis result in MongoDB
    """
    # MongoDB configuration
    MONGODB_URI = os.environ.get('MONGODB_URI')
    DATABASE_NAME = os.environ.get('MONGODB_DATABASE', 'imdb_reviews')
    COLLECTION_NAME = os.environ.get('MONGODB_COLLECTION', 'sentiment_analysis')
    
    if not MONGODB_URI:
        raise Exception("MONGODB_URI environment variable not set")
    
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Insert the result
        result = collection.insert_one(sentiment_result)
        
        print(f"Stored result in MongoDB with ID: {result.inserted_id}")
        
        # Close the connection
        client.close()
        
    except Exception as e:
        print(f"Error storing result in MongoDB: {str(e)}")
        raise Exception(f"MongoDB storage failed: {str(e)}")

# Optional: Test function for local development
def test_lambda():
    """
    Test function to simulate the Lambda execution locally
    """
    test_event = {
        "detail": {
            "fullDocument": {
                "_id": {"$oid": "test-document-id"},
                "review": "This movie was absolutely fantastic!",
                "movie_title": "Test Movie",
                "user_id": "test-user-123"
            }
        }
    }
    
    result = lambda_handler(test_event, None)
    print(f"Test result: {result}")

if __name__ == "__main__":
    test_lambda()
