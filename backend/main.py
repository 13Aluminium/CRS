from __future__ import annotations

import argparse
import re
from functools import lru_cache
from typing import List, Optional

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class NewsItem(BaseModel):
    id: int
    title: str
    content: str
    category: str
    snippet: str


class RecommendationRequest(BaseModel):
    query: Optional[str] = None
    liked_ids: Optional[List[int]] = None
    limit: int = 10


class RecommendationResponseItem(BaseModel):
    id: int
    title: str
    category: str
    score: float
    snippet: str


class NewsRecommender:
    def __init__(self, max_items: int = 2000) -> None:
        self.max_items = max_items
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=6000)
        self.items: List[NewsItem] = []
        self.matrix = None
        self._load_and_fit()

    @staticmethod
    def _parse_title(raw_text: str) -> str:
        subject_match = re.search(r"^Subject: (.+)$", raw_text, re.MULTILINE)
        if subject_match:
            return subject_match.group(1).strip()
        cleaned = re.sub(r"\s+", " ", raw_text).strip()
        return cleaned[:80] + ("..." if len(cleaned) > 80 else "") or "Untitled"

    @staticmethod
    def _clean_content(raw_text: str) -> str:
        no_headers = re.sub(r"^Lines:.*$", "", raw_text, flags=re.MULTILINE)
        no_headers = re.sub(r"^From:.*$", "", no_headers, flags=re.MULTILINE)
        no_headers = re.sub(r"^Subject:.*$", "", no_headers, flags=re.MULTILINE)
        return no_headers.strip()

    def _load_and_fit(self) -> None:
        dataset = fetch_20newsgroups(subset="train", remove=("footers",), shuffle=True, random_state=42)
        limit = min(self.max_items, len(dataset.data))
        texts = dataset.data[:limit]
        targets = dataset.target[:limit]
        target_names = dataset.target_names

        processed_contents: List[str] = []
        items: List[NewsItem] = []
        for idx, (text, target) in enumerate(zip(texts, targets)):
            content = self._clean_content(text)
            title = self._parse_title(text)
            snippet = (content[:260] + "...") if len(content) > 260 else content
            items.append(
                NewsItem(
                    id=idx,
                    title=title or "Untitled",
                    content=content,
                    category=target_names[target],
                    snippet=snippet,
                )
            )
            processed_contents.append(content)

        self.matrix = self.vectorizer.fit_transform(processed_contents)
        self.items = items

    def _vector_for_query(self, query: str) -> np.ndarray:
        return self.vectorizer.transform([query])

    def _vector_for_items(self, ids: List[int]) -> np.ndarray:
        rows = [self.matrix[i] for i in ids if 0 <= i < self.matrix.shape[0]]
        if not rows:
            return self.matrix[0:1]
        stacked = rows[0]
        for row in rows[1:]:
            stacked = stacked + row
        return stacked

    def recommend(self, query: Optional[str], liked_ids: Optional[List[int]], limit: int = 10) -> List[RecommendationResponseItem]:
        limit = max(1, min(limit, 50))
        candidate_vector = None

        if query:
            candidate_vector = self._vector_for_query(query)
        if liked_ids:
            liked_vector = self._vector_for_items(liked_ids)
            candidate_vector = liked_vector if candidate_vector is None else candidate_vector + liked_vector

        if candidate_vector is None:
            candidate_vector = self.matrix.mean(axis=0)

        similarities = cosine_similarity(candidate_vector, self.matrix).flatten()

        liked_set = set(liked_ids or [])
        ranked_indices = [i for i in similarities.argsort()[::-1] if i not in liked_set]
        top_indices = ranked_indices[:limit]

        recommendations: List[RecommendationResponseItem] = []
        for idx in top_indices:
            item = self.items[idx]
            recommendations.append(
                RecommendationResponseItem(
                    id=item.id,
                    title=item.title,
                    category=item.category,
                    score=float(similarities[idx]),
                    snippet=item.snippet,
                )
            )
        return recommendations


@lru_cache(maxsize=1)
def get_recommender() -> NewsRecommender:
    return NewsRecommender()


app = FastAPI(title="Content Recommender", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/items", response_model=List[NewsItem])
def list_items(limit: int = 40) -> List[NewsItem]:
    recommender = get_recommender()
    limit = max(1, min(limit, len(recommender.items)))
    return recommender.items[:limit]


@app.post("/recommendations", response_model=List[RecommendationResponseItem])
def recommend(payload: RecommendationRequest) -> List[RecommendationResponseItem]:
    recommender = get_recommender()
    return recommender.recommend(payload.query, payload.liked_ids, payload.limit)


def main() -> None:
    parser = argparse.ArgumentParser(description="Content recommender service")
    parser.add_argument("--check", action="store_true", help="Load data and run a sample recommendation")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    recommender = get_recommender()

    if args.check:
        sample = recommender.recommend("space exploration", liked_ids=None, limit=3)
        for rec in sample:
            print(f"{rec.score:.3f} - {rec.title} [{rec.category}]")
        return

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
