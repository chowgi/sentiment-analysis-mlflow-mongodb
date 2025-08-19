#!/usr/bin/env python3
"""
Test script for MongoDB to Lambda pipeline
Adds reviews to incoming_reviews collection and monitors sentiment_analysis collection
"""

import pymongo
import time
import random
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise ValueError("MONGODB_URI not found in environment variables")

DATABASE_NAME = "imdb_reviews"
INCOMING_COLLECTION = "incoming_reviews"
RESULTS_COLLECTION = "sentiment_analysis"

# Sample movie reviews for testing
SAMPLE_REVIEWS = [
    {
        "review": "This movie was absolutely fantastic! The acting was superb and the plot was engaging from start to finish. I couldn't take my eyes off the screen.",
        "movie_title": "The Great Adventure",
        "user_id": "user001"
    },
    {
        "review": "Terrible movie. Boring plot, bad acting, and a complete waste of time. I regret watching it.",
        "movie_title": "The Boring Disaster",
        "user_id": "user002"
    },
    {
        "review": "Amazing cinematography and brilliant performances by the entire cast. This is a masterpiece that will be remembered for years.",
        "movie_title": "Cinematic Masterpiece",
        "user_id": "user003"
    },
    {
        "review": "I found this movie to be quite disappointing. The story had potential but was poorly executed.",
        "movie_title": "Missed Opportunity",
        "user_id": "user004"
    },
    {
        "review": "Absolutely loved it! The characters were well-developed and the story was compelling. Highly recommend!",
        "movie_title": "Character Driven Drama",
        "user_id": "user005"
    },
    {
        "review": "This film was a complete disaster. Poor direction, weak script, and terrible special effects.",
        "movie_title": "Special Effects Nightmare",
        "user_id": "user006"
    },
    {
        "review": "A heartwarming story with beautiful visuals and touching moments. This movie touched my soul.",
        "movie_title": "Heartwarming Tale",
        "user_id": "user007"
    },
    {
        "review": "Mediocre at best. Nothing special about this movie. It was just okay.",
        "movie_title": "Average Film",
        "user_id": "user008"
    },
    {
        "review": "Outstanding performance by the lead actor! The movie exceeded all my expectations and delivered an unforgettable experience.",
        "movie_title": "Outstanding Performance",
        "user_id": "user009"
    },
    {
        "review": "I was really looking forward to this movie but it was a huge disappointment. The plot made no sense.",
        "movie_title": "Plot Confusion",
        "user_id": "user010"
    }
]

def connect_mongodb():
    """Connect to MongoDB and return client and collections"""
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        incoming_collection = db[INCOMING_COLLECTION]
        results_collection = db[RESULTS_COLLECTION]
        
        # Test connection
        client.admin.command('ping')
        print(f"✅ Connected to MongoDB: {MONGO_URI}")
        print(f"📊 Database: {DATABASE_NAME}")
        print(f"📥 Incoming Collection: {INCOMING_COLLECTION}")
        print(f"📤 Results Collection: {RESULTS_COLLECTION}")
        
        return client, incoming_collection, results_collection
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise

def get_initial_counts(incoming_collection, results_collection):
    """Get initial document counts"""
    incoming_count = incoming_collection.count_documents({})
    results_count = results_collection.count_documents({})
    
    print(f"📊 Initial counts:")
    print(f"   Incoming reviews: {incoming_count}")
    print(f"   Sentiment results: {results_count}")
    
    return incoming_count, results_count

def add_review_to_incoming(incoming_collection, review_data, review_number):
    """Add a review to the incoming_reviews collection"""
    try:
        # Add timestamp
        review_data["timestamp"] = datetime.utcnow()
        review_data["test_review_number"] = review_number
        
        # Insert the review
        result = incoming_collection.insert_one(review_data)
        
        print(f"✅ Added review {review_number}: {review_data['movie_title']}")
        print(f"   ID: {result.inserted_id}")
        print(f"   Review: {review_data['review'][:50]}...")
        
        return result.inserted_id
    except Exception as e:
        print(f"❌ Failed to add review {review_number}: {e}")
        return None

def monitor_results(results_collection, expected_count, timeout=60):
    """Monitor the results collection for new sentiment analysis results"""
    print(f"\n🔍 Monitoring for {expected_count} new sentiment analysis results...")
    print(f"⏱️  Timeout: {timeout} seconds")
    
    start_time = time.time()
    initial_count = results_collection.count_documents({})
    
    while time.time() - start_time < timeout:
        current_count = results_collection.count_documents({})
        new_results = current_count - initial_count
        
        if new_results >= expected_count:
            print(f"✅ All {expected_count} results received!")
            return True
        
        print(f"📊 Progress: {new_results}/{expected_count} results received...")
        time.sleep(2)
    
    print(f"⏰ Timeout reached. Only {new_results}/{expected_count} results received.")
    return False

def display_results(results_collection, test_review_ids):
    """Display the sentiment analysis results"""
    print(f"\n📋 Sentiment Analysis Results:")
    print("=" * 80)
    
    # Get recent results
    recent_results = list(results_collection.find().sort("processed_at", -1).limit(len(test_review_ids)))
    
    for i, result in enumerate(recent_results, 1):
        print(f"\n{i}. Movie: {result.get('movie_title', 'Unknown')}")
        print(f"   Review: {result.get('review', '')[:60]}...")
        print(f"   Sentiment: {result.get('sentiment', 'Unknown')}")
        print(f"   Confidence: {result.get('confidence', 0):.4f}")
        print(f"   Processed: {result.get('processed_at', 'Unknown')}")
        print(f"   Model: {result.get('model_version', 'Unknown')}")

def main():
    """Main test function"""
    print("🚀 Testing MongoDB to Lambda Pipeline")
    print("=" * 50)
    
    try:
        # Connect to MongoDB
        client, incoming_collection, results_collection = connect_mongodb()
        
        # Get initial counts
        initial_incoming, initial_results = get_initial_counts(incoming_collection, results_collection)
        
        # Store test review IDs
        test_review_ids = []
        
        print(f"\n📝 Adding {len(SAMPLE_REVIEWS)} reviews to incoming_reviews collection...")
        print("⏱️  2-second gap between each review")
        print("-" * 50)
        
        # Add reviews one by one with 2-second gaps
        for i, review_data in enumerate(SAMPLE_REVIEWS, 1):
            review_id = add_review_to_incoming(incoming_collection, review_data, i)
            if review_id:
                test_review_ids.append(review_id)
            
            # Wait 2 seconds before next review (except for the last one)
            if i < len(SAMPLE_REVIEWS):
                print("⏳ Waiting 2 seconds...")
                time.sleep(2)
        
        print(f"\n✅ Added {len(test_review_ids)} reviews successfully")
        
        # Monitor for results
        success = monitor_results(results_collection, len(test_review_ids), timeout=120)
        
        if success:
            # Display results
            display_results(results_collection, test_review_ids)
            
            # Final counts
            final_incoming = incoming_collection.count_documents({})
            final_results = results_collection.count_documents({})
            
            print(f"\n📊 Final Summary:")
            print(f"   Incoming reviews: {initial_incoming} → {final_incoming} (+{final_incoming - initial_incoming})")
            print(f"   Sentiment results: {initial_results} → {final_results} (+{final_results - initial_results})")
            
            if final_results - initial_results == len(test_review_ids):
                print("🎉 Pipeline test completed successfully!")
            else:
                print("⚠️  Some results may be missing")
        else:
            print("❌ Pipeline test failed - not all results received")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        if 'client' in locals():
            client.close()
            print("\n🔌 MongoDB connection closed")

if __name__ == "__main__":
    main()
