// MongoDB Atlas Trigger Function
// This function is triggered when a new document is added to the 'incoming_reviews' collection
// It calls the sentiment analysis API and stores the result back in MongoDB

exports = async function(changeEvent) {
  try {
    // Get the database and collections
    // In Atlas triggers, we access the database through the configured service
    let db;
    try {
      // Use the configured service name "DemoTriggers"
      db = context.services.get("DemoTriggers").db("imdb_reviews");
    } catch (serviceError) {
      try {
        // Fallback to standard Atlas trigger pattern
        db = context.services.get("mongodb-atlas").db("imdb_reviews");
      } catch (altError) {
        try {
          // Try alternative service name
          db = context.services.get("mongodb").db("imdb_reviews");
        } catch (finalError) {
          console.error("All connection attempts failed:", {
            "DemoTriggers": serviceError.message,
            "mongodb-atlas": altError.message,
            "mongodb": finalError.message
          });
          throw new Error("Cannot connect to MongoDB service. Please check service configuration.");
        }
      }
    }
    
    const incomingCollection = db.collection("incoming_reviews");
    const resultsCollection = db.collection("sentiment_analysis");
    
    // Get the new document that was inserted
    const newDocument = changeEvent.fullDocument;
    
    if (!newDocument) {
      console.log("No document found in change event");
      return;
    }
    
    console.log("Processing new review:", newDocument._id);
    
    // Prepare the API request payload
    const apiPayload = {
      review: newDocument.review,
      movie_title: newDocument.movie_title || null,
      user_id: newDocument.user_id || null
    };
    
    // Call the sentiment analysis API
    const response = await context.http.post({
      url: "http://ec2-3-104-64-153.ap-southeast-2.compute.amazonaws.com:8001/predict",
      headers: {
        "Content-Type": ["application/json"]
      },
      body: JSON.stringify(apiPayload)
    });
    
    if (response.statusCode === 200) {
      const result = JSON.parse(response.body.text());
      
      console.log("Successfully processed review:", newDocument._id, "Sentiment:", result.sentiment);
      console.log("API stored result in MongoDB with ID:", result._id || "unknown");
      
    } else {
      console.error("API call failed with status:", response.statusCode);
      console.error("Response body:", response.body.text());
      
      console.error("API call failed - no document created");
    }
    
  } catch (error) {
    console.error("Error processing review:", error);
    
    console.error("Error processing review - no document created");
  }
};
