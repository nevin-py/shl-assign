# SHL Assessment Recommendation System - Deployment Guide

## Quick Deploy to Render.com

### Prerequisites
1. GitHub account
2. Render.com account (free tier works)
3. Push this repository to GitHub

### Step 1: Push to GitHub

```bash
cd /home/ariva/work/shl_assign
git init
git add .
git commit -m "Initial commit - SHL Assessment Recommender"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### Step 2: Deploy Backend API

1. Go to https://render.com/dashboard
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `shl-assessment-api`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
5. Add Environment Variables:
   - `PYTHON_VERSION`: `3.11.9`
6. Click "Create Web Service"
7. Wait for deployment (5-10 minutes)
8. Copy the URL (e.g., `https://shl-assessment-api.onrender.com`)

### Step 3: Deploy Frontend

1. Go to https://render.com/dashboard
2. Click "New +" → "Web Service"
3. Connect the same GitHub repository
4. Configure:
   - **Name**: `shl-assessment-frontend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
   - **Instance Type**: Free
5. Add Environment Variables:
   - `PYTHON_VERSION`: `3.11.9`
   - `API_URL`: `https://shl-assessment-api.onrender.com` (from Step 2)
6. Click "Create Web Service"
7. Wait for deployment (5-10 minutes)
8. Copy the URL (e.g., `https://shl-assessment-frontend.onrender.com`)

### Step 4: Test Deployment

1. Open backend URL + `/health` to verify API is running
2. Open frontend URL to test the full application
3. Try a sample query like "Python developer"

## Alternative: One-Click Deploy

You can also use the `render.yaml` file for one-click deployment:

1. Push code to GitHub
2. Go to https://render.com/dashboard
3. Click "New +" → "Blueprint"
4. Connect your repository
5. Render will automatically detect `render.yaml` and deploy both services

## Important Notes

- **Free Tier Limitations**: Services spin down after 15 minutes of inactivity and take ~30 seconds to restart
- **ChromaDB Data**: The vector database is included in the repository (`./chroma_db`)
- **No API Keys Needed**: This system uses local embeddings (all-MiniLM-L6-v2)
- **Cold Start**: First request may take 30-60 seconds on free tier

## Submission URLs

After deployment, you'll have:
- **Backend API**: `https://shl-assessment-api.onrender.com`
- **Frontend App**: `https://shl-assessment-frontend.onrender.com`
- **Health Check**: `https://shl-assessment-api.onrender.com/health`
- **API Docs**: `https://shl-assessment-api.onrender.com/docs`

## Troubleshooting

### If backend fails to start:
- Check logs in Render dashboard
- Ensure `requirements.txt` includes all dependencies
- Verify Python version is 3.11.x

### If frontend can't connect to backend:
- Check `API_URL` environment variable in frontend
- Ensure backend health check is passing
- Wait for backend cold start (~30 seconds)

### If ChromaDB errors occur:
- Ensure `./chroma_db` directory is committed to git
- Check that embeddings were generated correctly
