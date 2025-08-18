#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Sentiment Analysis API
Script to test the sentiment analysis API with sample movie reviews
"""

import requests
import json
import time
from datetime import datetime

# API configuration
API_BASE_URL = "http://localhost:8001"

def test_health_check():
    """Test the health check endpoint"""
    print("=== Testing Health Check ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_sentiment_prediction(review, movie_title=None, user_id=None):
    """Test sentiment prediction for a review"""
    
    payload = {
        "review": review,
        "movie_title": movie_title,
        "user_id": user_id
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Prediction successful:")
            print(f"   Review: '{data['review'][:50]}...'")
            print(f"   Sentiment: {data['sentiment']}")
            print(f"   Confidence: {data['confidence']:.3f}")
            print(f"   Movie: {data.get('movie_title', 'N/A')}")
            print(f"   User ID: {data.get('user_id', 'N/A')}")
            print(f"   Timestamp: {data['timestamp']}")
            return data
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return None

def test_get_reviews():
    """Test getting recent reviews"""
    print("\n=== Testing Get Reviews ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/reviews?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {data['total']} reviews")
            for i, review in enumerate(data['reviews'], 1):
                print(f"   {i}. '{review['review'][:50]}...' -> {review['sentiment']} ({review['confidence']:.3f})")
            return data
        else:
            print(f"❌ Get reviews failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Get reviews error: {e}")
        return None

def test_get_stats():
    """Test getting statistics"""
    print("\n=== Testing Get Stats ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Statistics retrieved:")
            print(f"   Total reviews: {data['total_reviews']}")
            print(f"   Positive reviews: {data['positive_reviews']}")
            print(f"   Negative reviews: {data['negative_reviews']}")
            print(f"   Positive percentage: {data['positive_percentage']:.1f}%")
            print(f"   Average confidence: {data['average_confidence']:.3f}")
            return data
        else:
            print(f"❌ Get stats failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Get stats error: {e}")
        return None

def main():
    """Main test function"""
    
    print("=== Sentiment Analysis API Test ===")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Timestamp: {datetime.now()}")
    
    # Sample movie reviews for testing
    test_reviews = [
        {
            "review": "This movie is absolutely fantastic! The acting is superb and the plot is engaging from start to finish. I highly recommend it to everyone.",
            "movie_title": "The Great Adventure",
            "user_id": "user123"
        },
        {
            "review": "Terrible movie. Boring plot, bad acting, and a complete waste of time. I regret watching it.",
            "movie_title": "The Boring Disaster",
            "user_id": "user456"
        },
        {
            "review": "Amazing cinematography and brilliant storytelling. This is a masterpiece that will be remembered for years to come.",
            "movie_title": "Cinematic Masterpiece",
            "user_id": "user789"
        },
        {
            "review": "The movie was okay, nothing special. Some good moments but overall forgettable.",
            "movie_title": "Average Film",
            "user_id": "user101"
        },
        {
            "review": "Incredible performance by the lead actor. The emotional depth and character development are outstanding.",
            "movie_title": "Emotional Journey",
            "user_id": "user202"
        }
    ]
    
    # Test health check
    if not test_health_check():
        print("❌ Health check failed. Make sure the API server is running.")
        return
    
    # Test sentiment predictions
    print("\n=== Testing Sentiment Predictions ===")
    for i, test_case in enumerate(test_reviews, 1):
        print(f"\n--- Test Case {i} ---")
        test_sentiment_prediction(
            review=test_case["review"],
            movie_title=test_case["movie_title"],
            user_id=test_case["user_id"]
        )
        time.sleep(1)  # Small delay between requests
    
    # Test getting reviews
    test_get_reviews()
    
    # Test getting stats
    test_get_stats()
    
    print("\n=== Test Complete ===")
    print("Check the MongoDB database 'imdb_reviews' collection 'sentiment_analysis' for stored results.")

if __name__ == "__main__":
    main()
