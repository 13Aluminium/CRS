# Content Recommendation System

A Pinterest-style text recommendation experience that serves article-like snippets from the 20 Newsgroups dataset. The backend uses FastAPI with TF-IDF embeddings and cosine similarity, while the frontend is a static grid UI you can host on GitHub Pages or Netlify.

## Features
- **Content-based recommendations** using TF-IDF vectors and cosine similarity.
- **User signals**: free-text interest query plus optional liked posts blended into a profile vector.
- **Public dataset**: 20 Newsgroups (titles parsed from `Subject` headers, categories preserved).
- **Simple web UI** with a masonry-like grid, like buttons, and live recommendations via API.

## Project layout
```
backend/
  main.py              # FastAPI app + recommender logic
  requirements.txt     # Backend dependencies
frontend/
  index.html           # UI shell
  styles.css           # Pinterest-style styling
  script.js            # Fetches feed & recommendations
```

## Getting started (local)
1. Create a virtual environment and install dependencies:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Warm up the model (downloads the dataset and prints sample recommendations):
   ```bash
   python main.py --check
   ```
3. Start the API server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Open `frontend/index.html` in a browser (or serve the `frontend/` directory). Point the **API base URL** box to your backend (default: `http://localhost:8000`).

## API
- `GET /health` → `{ "status": "ok" }`
- `GET /items?limit=40` → array of feed items: `{id, title, content, category, snippet}`
- `POST /recommendations` with body `{ query: string | null, liked_ids: number[] | null, limit?: number }` → ranked items with `score` (cosine similarity)

## Deployment
### Backend (Render example)
1. Push this repo to GitHub.
2. On Render, create a new **Web Service**:
   - Build command: `pip install -r backend/requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Root directory: `backend`
3. Once deployed, copy the service URL (e.g., `https://your-app.onrender.com`).

**Alternative:** deploy to Hugging Face Spaces with a FastAPI Space — use the same commands above.

### Frontend (GitHub Pages or Netlify)
- GitHub Pages: set the publishing source to the `frontend/` folder (e.g., with Pages from `main`/`root` and specify `/frontend`).
- Netlify: drag-and-drop the `frontend/` folder or configure a site with **build command** empty and **publish directory** `frontend`.

Update the **API base URL** field in the UI to point to your deployed backend URL.

## Notes
- Recommendations default to the overall corpus profile if no query or likes are supplied.
- TF-IDF is fast and light; you can swap in SentenceTransformers embeddings by replacing the vectorizer and similarity logic in `backend/main.py`.
