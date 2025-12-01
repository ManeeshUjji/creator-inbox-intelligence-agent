"""
Knowledge Base Search Tool
TF-IDF + cosine similarity
"""

from pathlib import Path
import logging
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[KB_SEARCH] %(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

_KB_DF = None
_VECTORIZER = None
_KB_TFIDF = None

def _get_datasets_path():
    return Path(__file__).resolve().parents[2] / "datasets"


def build_kb_index(rebuild=False):
    global _KB_DF, _VECTORIZER, _KB_TFIDF

    if _KB_DF is not None and not rebuild:
        return

    kb_path = _get_datasets_path() / "knowledge_base.csv"
    kb_df = pd.read_csv(kb_path)

    kb_df["search_text"] = kb_df[["title","category","tags","content"]].fillna("").agg(" ".join, axis=1)

    vectorizer = TfidfVectorizer(stop_words="english")
    kb_tfidf = vectorizer.fit_transform(kb_df["search_text"])

    _KB_DF = kb_df
    _VECTORIZER = vectorizer
    _KB_TFIDF = kb_tfidf


def search_kb(query, top_k=5, min_score=0.0):
    if _KB_DF is None:
        build_kb_index()

    query_vec = _VECTORIZER.transform([query])
    scores = cosine_similarity(query_vec, _KB_TFIDF)[0]

    idx = scores.argsort()[::-1][:top_k]
    results = []

    for i in idx:
        if scores[i] >= min_score:
            row = _KB_DF.iloc[i].to_dict()
            row["similarity_score"] = float(scores[i])
            results.append(row)

    return results
