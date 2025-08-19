#!/usr/bin/env python3
"""
Diagnostic script to check the status of all pipeline components
"""

import boto3
import pymongo
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_lambda_function():
    """Check if Lambda function exists and is configured correctly"""
    print("🔍 Checking Lambda Function...")
    print("-" * 40)
    
    try:
        lambda_client = boto3.client('lambda', region_name='ap-southeast-2')
        
        # Check if function exists
        response = lambda_client.get_function(FunctionName='sentiment-analysis-lambda')
        print(f"✅ Lambda function exists: {response['Configuration']['FunctionName']}")
        print(f"   Runtime: {response['Configuration']['Runtime']}")
        print(f"   Handler: {response['Configuration']['Handler']}")
        print(f"   Status: {response['Configuration']['State']}")
        
        # Check environment variables
        env_vars = response['Configuration'].get('Environment', {}).get('Variables', {})
        print(f"   Environment Variables:")
        for key, value in env_vars.items():
            if 'URI' in key or 'PASSWORD' in key:
                print(f"     {key}: {'*' * 10} (hidden)")
            else:
                print(f"     {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lambda function check failed: {e}")
        return False

def check_eventbridge_rules():
    """Check EventBridge rules"""
    print("\n🔍 Checking EventBridge Rules...")
    print("-" * 40)
    
    try:
        events_client = boto3.client('events', region_name='ap-southeast-2')
        
        # List rules
        response = events_client.list_rules()
        
        mongodb_rules = [rule for rule in response['Rules'] if 'mongodb' in rule['Name'].lower() or 'sentiment' in rule['Name'].lower()]
        
        if mongodb_rules:
            print(f"✅ Found {len(mongodb_rules)} potential MongoDB rules:")
            for rule in mongodb_rules:
                print(f"   Rule: {rule['Name']}")
                print(f"   State: {rule['State']}")
                print(f"   ARN: {rule['Arn']}")
                
                # Get rule details
                try:
                    rule_detail = events_client.describe_rule(Name=rule['Name'])
                    if 'Targets' in rule_detail:
                        for target in rule_detail['Targets']:
                            print(f"   Target: {target['Id']} -> {target['Arn']}")
                except Exception as e:
                    print(f"   Error getting rule details: {e}")
        else:
            print("❌ No MongoDB-related EventBridge rules found")
            print("   You need to create an EventBridge rule to trigger the Lambda function")
        
        return len(mongodb_rules) > 0
        
    except Exception as e:
        print(f"❌ EventBridge check failed: {e}")
        return False

def check_mongodb_connection():
    """Check MongoDB connection and collections"""
    print("\n🔍 Checking MongoDB Connection...")
    print("-" * 40)
    
    try:
        MONGO_URI = os.getenv("MONGODB_URI")
        if not MONGO_URI:
            print("❌ MONGODB_URI not found in environment variables")
            return False
        
        client = pymongo.MongoClient(MONGO_URI)
        db = client['imdb_reviews']
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Check collections
        collections = db.list_collection_names()
        print(f"   Collections: {collections}")
        
        # Check document counts
        incoming_count = db['incoming_reviews'].count_documents({})
        results_count = db['sentiment_analysis'].count_documents({})
        
        print(f"   incoming_reviews: {incoming_count} documents")
        print(f"   sentiment_analysis: {results_count} documents")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB check failed: {e}")
        return False

def check_sagemaker_endpoint():
    """Check SageMaker endpoint status"""
    print("\n🔍 Checking SageMaker Endpoint...")
    print("-" * 40)
    
    try:
        sagemaker_client = boto3.client('sagemaker', region_name='ap-southeast-2')
        
        # Check endpoint status
        response = sagemaker_client.describe_endpoint(EndpointName='distilbert-sentiment')
        
        print(f"✅ SageMaker endpoint exists: {response['EndpointName']}")
        print(f"   Status: {response['EndpointStatus']}")
        print(f"   Created: {response['CreationTime']}")
        
        if response['EndpointStatus'] == 'InService':
            print("✅ Endpoint is in service and ready")
            return True
        else:
            print(f"⚠️  Endpoint is not in service: {response['EndpointStatus']}")
            return False
            
    except Exception as e:
        print(f"❌ SageMaker endpoint check failed: {e}")
        return False

def create_eventbridge_rule():
    """Create EventBridge rule for MongoDB triggers"""
    print("\n🔧 Creating EventBridge Rule...")
    print("-" * 40)
    
    try:
        events_client = boto3.client('events', region_name='ap-southeast-2')
        
        # Event pattern for MongoDB Atlas triggers
        event_pattern = {
            "source": ["aws.partner/mongodb.com/stitch.trigger/*"],
            "detail-type": ["MongoDB Triggers Triggered"],
            "detail": {
                "database": ["imdb_reviews"],
                "collection": ["incoming_reviews"],
                "operationType": ["insert"]
            }
        }
        
        # Create rule
        rule_name = "mongodb-sentiment-trigger"
        response = events_client.put_rule(
            Name=rule_name,
            EventPattern=str(event_pattern).replace("'", '"'),
            State='ENABLED',
            Description='Trigger Lambda function when new reviews are added to MongoDB'
        )
        
        print(f"✅ Created EventBridge rule: {rule_name}")
        print(f"   ARN: {response['RuleArn']}")
        
        # Add Lambda target
        lambda_client = boto3.client('lambda', region_name='ap-southeast-2')
        lambda_client.add_permission(
            FunctionName='sentiment-analysis-lambda',
            StatementId='EventBridgeInvoke',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=response['RuleArn']
        )
        
        # Put targets
        events_client.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    'Id': 'SentimentAnalysisLambda',
                    'Arn': f"arn:aws:lambda:ap-southeast-2:{boto3.client('sts').get_caller_identity()['Account']}:function:sentiment-analysis-lambda"
                }
            ]
        )
        
        print("✅ Added Lambda function as target")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create EventBridge rule: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("🔍 MongoDB to Lambda Pipeline Diagnostic")
    print("=" * 50)
    
    # Check all components
    lambda_ok = check_lambda_function()
    eventbridge_ok = check_eventbridge_rules()
    mongodb_ok = check_mongodb_connection()
    sagemaker_ok = check_sagemaker_endpoint()
    
    print("\n📊 Diagnostic Summary:")
    print("=" * 30)
    print(f"Lambda Function: {'✅' if lambda_ok else '❌'}")
    print(f"EventBridge Rules: {'✅' if eventbridge_ok else '❌'}")
    print(f"MongoDB Connection: {'✅' if mongodb_ok else '❌'}")
    print(f"SageMaker Endpoint: {'✅' if sagemaker_ok else '❌'}")
    
    # Provide recommendations
    print("\n💡 Recommendations:")
    if not eventbridge_ok:
        print("❌ EventBridge rule is missing - this is likely why the pipeline isn't working")
        print("   Would you like me to create the EventBridge rule? (y/n): ", end="")
        response = input().lower()
        if response == 'y':
            create_eventbridge_rule()
    
    if not lambda_ok:
        print("❌ Lambda function has issues - check the configuration")
    
    if not mongodb_ok:
        print("❌ MongoDB connection failed - check your MONGODB_URI")
    
    if not sagemaker_ok:
        print("❌ SageMaker endpoint is not ready - check endpoint status")

if __name__ == "__main__":
    main()
