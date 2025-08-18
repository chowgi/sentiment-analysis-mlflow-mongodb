#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test MongoDB Atlas Trigger
This script adds test documents to the incoming_reviews collection
to test the automatic sentiment analysis trigger
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import time

# Load environment variables
load_dotenv()

def connect_mongodb():
    """Connect to MongoDB Atlas"""
    mongo_uri = os.getenv('MONGODB_URI')
    if not mongo_uri:
        raise ValueError("MONGODB_URI not found in environment variables")
    
    client = MongoClient(mongo_uri)
    db = client['imdb_reviews']
    return client, db

def add_test_reviews():
    """Add test reviews to the incoming_reviews collection"""
    
    client, db = connect_mongodb()
    incoming_collection = db['incoming_reviews']
    
    # Test reviews
    test_reviews = [
        {
            "review": "This movie is absolutely fantastic! The acting is superb and the plot is engaging from start to finish.",
            "movie_title": "The Great Adventure",
            "user_id": "user123",
            "created_at": datetime.utcnow()
        },
        {
            "review": "Terrible movie. Boring plot, bad acting, and a complete waste of time. I regret watching it.",
            "movie_title": "The Boring Disaster",
            "user_id": "user456",
            "created_at": datetime.utcnow()
        },
        {
            "review": "Amazing cinematography and brilliant storytelling. This is a masterpiece that will be remembered for years to come.",
            "movie_title": "Cinematic Masterpiece",
            "user_id": "user789",
            "created_at": datetime.utcnow()
        },
        {
            "review": "The movie was okay, nothing special. Some good moments but overall forgettable.",
            "movie_title": "Average Film",
            "user_id": "user101",
            "created_at": datetime.utcnow()
        },
        {
            "review": "Incredible performance by the lead actor. The emotional depth and character development are outstanding.",
            "movie_title": "Emotional Journey",
            "user_id": "user202",
            "created_at": datetime.utcnow()
        }
    ]
    
    print("📝 Adding test reviews to incoming_reviews collection...")
    
    for i, review in enumerate(test_reviews, 1):
        try:
            result = incoming_collection.insert_one(review)
            print(f"✅ Added review {i}: {review['movie_title']} (ID: {result.inserted_id})")
            time.sleep(1)  # Small delay between inserts
        except Exception as e:
            print(f"❌ Failed to add review {i}: {e}")
    
    print(f"\n📊 Total documents in incoming_reviews: {incoming_collection.count_documents({})}")
    
    client.close()

def check_processing_status():
    """Check the processing status of reviews"""
    
    client, db = connect_mongodb()
    incoming_collection = db['incoming_reviews']
    results_collection = db['sentiment_analysis']
    
    print("\n🔍 Checking processing status...")
    print("=" * 50)
    
    # Check incoming reviews
    incoming_reviews = list(incoming_collection.find().sort('created_at', -1).limit(5))
    
    for review in incoming_reviews:
        print(f"Review ID: {review['_id']}")
        print(f"Movie: {review.get('movie_title', 'N/A')}")
        print(f"Review: {review['review'][:50]}...")
        print(f"Processed: {review.get('processed', False)}")
        
        if review.get('processed'):
            print(f"Sentiment: {review.get('sentiment_result', 'N/A')}")
            print(f"Confidence: {review.get('confidence', 'N/A')}")
        elif review.get('error'):
            print(f"Error: {review.get('error', 'N/A')}")
        
        print("-" * 30)
    
    # Check results collection
    print(f"\n📊 Total processed results: {results_collection.count_documents({})}")
    
    recent_results = list(results_collection.find().sort('timestamp', -1).limit(3))
    if recent_results:
        print("\nRecent processed results:")
        for result in recent_results:
            print(f"- {result.get('movie_title', 'N/A')}: {result['sentiment']} ({result['confidence']:.3f})")
    
    client.close()

def main():
    """Main function"""
    
    print("🧪 MongoDB Atlas Trigger Test")
    print("=" * 40)
    
    try:
        # Add test reviews
        add_test_reviews()
        
        # Wait a bit for processing
        print("\n⏳ Waiting 10 seconds for trigger processing...")
        time.sleep(10)
        
        # Check processing status
        check_processing_status()
        
        print("\n✅ Test completed!")
        print("\n💡 To monitor in real-time:")
        print("   - Check MongoDB Atlas logs for trigger execution")
        print("   - Monitor the sentiment_analysis collection for new results")
        print("   - Use the API endpoints to view processed data")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
