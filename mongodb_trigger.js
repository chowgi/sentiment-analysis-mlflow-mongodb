// MongoDB Atlas Trigger Function
// This function is triggered when a new document is added to the 'incoming_reviews' collection
// It calls the sentiment analysis API and stores the result back in MongoDB

exports = async function(changeEvent) {
  // Get the database and collections
  const db = context.services.get("mongodb-atlas").db("imdb_reviews");
  const incomingCollection = db.collection("incoming_reviews");
  const resultsCollection = db.collection("sentiment_analysis");
  
  // Get the new document that was inserted
  const newDocument = changeEvent.fullDocument;
  
  if (!newDocument) {
    console.log("No document found in change event");
    return;
  }
  
  console.log("Processing new review:", newDocument._id);
  
  try {
    // Prepare the API request payload
    const apiPayload = {
      review: newDocument.review,
      movie_title: newDocument.movie_title || null,
      user_id: newDocument.user_id || null
    };
    
    // Call the sentiment analysis API
    const response = await context.http.post({
      url: "http://localhost:8001/predict",
      headers: {
        "Content-Type": ["application/json"]
      },
      body: JSON.stringify(apiPayload)
    });
    
    if (response.statusCode === 200) {
      const result = JSON.parse(response.body.text());
      
      // Store the result in the sentiment_analysis collection
      const resultDocument = {
        review: result.review,
        sentiment: result.sentiment,
        confidence: result.confidence,
        timestamp: new Date(result.timestamp),
        movie_title: result.movie_title,
        user_id: result.user_id,
        model_version: result.model_version || "distilbert-sentiment",
        source_document_id: newDocument._id,
        processed_at: new Date()
      };
      
      await resultsCollection.insertOne(resultDocument);
      
      // Update the original document with processing status
      await incomingCollection.updateOne(
        { _id: newDocument._id },
        { 
          $set: { 
            processed: true,
            processed_at: new Date(),
            sentiment_result: result.sentiment,
            confidence: result.confidence
          }
        }
      );
      
      console.log("Successfully processed review:", newDocument._id, "Sentiment:", result.sentiment);
      
    } else {
      console.error("API call failed with status:", response.statusCode);
      console.error("Response body:", response.body.text());
      
      // Mark the document as failed
      await incomingCollection.updateOne(
        { _id: newDocument._id },
        { 
          $set: { 
            processed: false,
            error: `API call failed with status ${response.statusCode}`,
            processed_at: new Date()
          }
        }
      );
    }
    
  } catch (error) {
    console.error("Error processing review:", newDocument._id, error);
    
    // Mark the document as failed
    await incomingCollection.updateOne(
      { _id: newDocument._id },
      { 
        $set: { 
          processed: false,
          error: error.message,
          processed_at: new Date()
        }
      }
    );
  }
};
