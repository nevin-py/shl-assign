"""
FastAPI Backend for SHL Assessment Recommendation System
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize FastAPI app
app = FastAPI(
    title="SHL Assessment Recommendation API",
    description="API for recommending SHL assessments based on job descriptions or queries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize recommendation engine
recommender = None


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "I need a Java developer who can collaborate with teams"
            }
        }


class AssessmentRecommendation(BaseModel):
    url: str
    name: str
    adaptive_support: str
    description: str
    duration: Optional[int] = None  # Duration in minutes, 0 for reports
    remote_support: str
    test_type: List[str]


class RecommendationResponse(BaseModel):
    recommendations: List[AssessmentRecommendation]
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommendations": [
                    {
                        "url": "https://www.shl.com/solutions/products/product-catalog/view/python-new/",
                        "name": "Python (New)",
                        "adaptive_support": "No",
                        "description": "Multi-choice test that measures knowledge of Java programming",
                        "duration": 11,
                        "remote_support": "Yes",
                        "test_type": ["Knowledge & Skills"]
                    }
                ]
            }
        }


class HealthResponse(BaseModel):
    status: str
    message: Optional[str] = None


def get_recommender():
    """Lazy-initialize the recommendation engine on first use"""
    global recommender
    if recommender is None:
        try:
            print("Initializing recommendation engine...")
            
            # Check which embedding mode to use
            use_api = os.getenv("USE_API_EMBEDDINGS", "false").lower() == "true"
            
            if use_api:
                print("🌐 Using API-based embeddings (lightweight for deployment)")
                from backend.recommender_api import APIRecommendationEngine
                RecommendationEngine = APIRecommendationEngine
            else:
                print("💻 Using local embeddings (full model)")
                from backend.recommender_local import LocalRecommendationEngine
                RecommendationEngine = LocalRecommendationEngine
            
            chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
            recommender = RecommendationEngine(chroma_dir=chroma_dir)
            print("✓ Recommendation engine initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing recommendation engine: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=503,
                detail=f"Failed to initialize recommendation engine: {str(e)}"
            )
    return recommender


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "SHL Assessment Recommendation API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "recommend": "/recommend"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify the API is running
    
    Returns:
        HealthResponse: Status of the API
    """
    # Return healthy immediately without initializing the heavy recommender
    # This allows Render to detect the service is up quickly
    return HealthResponse(
        status="healthy",
        message="API is running. Recommendation engine will initialize on first request."
    )


@app.post("/recommend", response_model=RecommendationResponse, tags=["Recommendations"])
async def recommend_assessments(request: QueryRequest):
    """
    Get assessment recommendations based on a job description or query
    
    Args:
        request: QueryRequest containing the query (can be text, JD, or URL)
    
    Returns:
        RecommendationResponse: List of recommended assessments (5-10)
    
    Example:
        ```
        POST /recommend
        {
            "query": "I need a Java developer who can collaborate with teams"
        }
        ```
    """
    # Lazy-initialize recommender on first request
    rec = get_recommender()
    
    if not request.query or len(request.query.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )
    
    try:
        # Get recommendations
        result = rec.get_recommendations(
            query=request.query,
            min_results=5,
            max_results=10
        )
        
        # Check for errors
        if isinstance(result, dict) and 'error' in result:
            raise HTTPException(
                status_code=400,
                detail=result['error']
            )
        
        # Extract recommendations list from result dict
        recommendations_list = result.get('recommendations', []) if isinstance(result, dict) else []
        
        # Format response
        formatted_recommendations = [
            AssessmentRecommendation(
                url=rec['url'],
                name=rec['assessment_name'],
                adaptive_support=rec.get('adaptive_support', 'No'),
                description=rec.get('description', ''),
                duration=rec.get('duration'),
                remote_support=rec.get('remote_support', 'No'),
                test_type=rec.get('test_type', []) if isinstance(rec.get('test_type'), list) else [rec.get('test_type', '')]
            )
            for rec in recommendations_list
        ]
        
        return RecommendationResponse(recommendations=formatted_recommendations)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    # Render uses PORT, but allow API_PORT for local development
    port = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
    
    print(f"Starting API server on {host}:{port}")
    print(f"PORT environment variable: {os.getenv('PORT', 'not set')}")
    print(f"API_PORT environment variable: {os.getenv('API_PORT', 'not set')}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")
