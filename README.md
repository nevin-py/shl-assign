# SHL Assessment Recommendation System

AI-powered recommendation system that matches job requirements with SHL assessments using semantic search.

## Features

- 377 SHL assessments with complete metadata
- Semantic search using sentence-transformers
- Intelligent ranking with balanced recommendations
- FastAPI backend + Streamlit frontend
- RESTful API with automatic documentation

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/shl-assign.git
cd shl-assign

# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running Locally

```bash
# Start Backend (Port 8000)
python backend/main.py

# Start Frontend (Port 8501)
streamlit run frontend/app.py
```

Visit:
- Frontend: http://localhost:8501
- API Docs: http://localhost:8000/docs

## API Usage

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "Java developer with team collaboration skills"}'
```

Response:
```json
{
  "recommendations": [
    {
      "url": "https://www.shl.com/products/product-catalog/view/java-8-new/",
      "name": "Java 8 (New)",
      "adaptive_support": "No",
      "description": "Multi-choice test that measures...",
      "duration": 18,
      "remote_support": "Yes",
      "test_type": ["Knowledge & Skills"]
    }
  ]
}
```

## Project Structure

```
shl-assign/
├── backend/
│   ├── main.py                      # FastAPI server
│   ├── recommender_local.py         # Recommendation engine
│   └── embedding_pipeline_local.py  # Embedding generation
├── frontend/
│   └── app.py                       # Streamlit UI
├── scraper/
│   ├── complete_scraper.py          # Data scraper
│   └── update_chromadb.py           # DB updates
├── data/
│   └── scraped_assessments_complete.json  # 377 assessments
├── chroma_db/                       # Vector database
└── predictions.csv                  # Evaluation results
```

## Tech Stack

- **Backend**: FastAPI, ChromaDB
- **Frontend**: Streamlit
- **ML Model**: sentence-transformers/all-MiniLM-L6-v2
- **Database**: ChromaDB (vector store)

## Deployment

### Render.com

**Backend Service:**
- Build: `pip install -r requirements.txt`
- Start: `python backend/main.py`
- Port: 8000

**Frontend Service:**
- Build: `pip install -r requirements.txt`
- Start: `streamlit run frontend/app.py --server.port $PORT`
- Environment: `API_URL=<backend-url>`

## How It Works

1. **Query Enhancement**: Expands queries with relevant keywords
2. **Vector Search**: Finds semantically similar assessments using ChromaDB
3. **Smart Ranking**: Balances technical and behavioral assessments
4. **Top 10 Results**: Returns diverse, relevant recommendations

## Assessment Categories

- Knowledge & Skills
- Personality & Behavior
- Simulations
- Ability & Aptitude
- Biodata & Situational Judgement
- Competencies
- Development & 360
- Assessment Exercises

## License

Educational project for SHL AI Intern Assignment 2024
