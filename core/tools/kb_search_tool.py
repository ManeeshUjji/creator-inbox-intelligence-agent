"""
Knowledge Base Search Tool

- Loads knowledge_base.csv from the repo's datasets directory
- Builds a TF-IDF index on combined text fields
- Exposes search_kb(query, top_k=5) -> list[dict]
"""

from pathlib import Path
import logging
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------- Logging setup ----------------

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[KB_SEARCH] %(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ---------------- Globals for cached index ----------------

_KB_DF = None
_VECTORIZER = None
_KB_TFIDF = None


def _get_datasets_path() -> Path:
    """
    Resolve the /datasets directory relative to this file.

    core/tools/kb_search_tool.py
    -> repo_root = parents[2]
    -> datasets = repo_root / "datasets"
    """
    return Path(__file__).resolve().parents[2] / "datasets"


def build_kb_index(rebuild: bool = False):
    """
    Load knowledge_base.csv and build a TF-IDF index.

    This function caches the DataFrame, vectorizer, and TF-IDF matrix
    in module-level globals so repeated searches are fast.
    """
    global _KB_DF, _VECTORIZER, _KB_TFIDF

    if _KB_DF is not None and _VECTORIZER is not None and _KB_TFIDF is not None and not rebuild:
        return

    kb_path = _get_datasets_path() / "knowledge_base.csv"
    logger.info(f"Loading KB from: {kb_path}")

    kb_df = pd.read_csv(kb_path)

    # Build a combined text field for search
    text_cols = [c for c in ["title", "category", "tags", "content"] if c in kb_df.columns]
    if not text_cols:
        raise ValueError("knowledge_base.csv has no expected text columns.")

    kb_df["search_text"] = kb_df[text_cols].fillna("").agg(" ".join, axis=1)

    vectorizer = TfidfVectorizer(stop_words="english")
    kb_tfidf = vectorizer.fit_transform(kb_df["search_text"])

    _KB_DF = kb_df
    _VECTORIZER = vectorizer
    _KB_TFIDF = kb_tfidf

    logger.info(f"KB index built with {len(kb_df)} rows and {kb_tfidf.shape[1]} features.")


def search_kb(query: str, top_k: int = 5, min_score: float = 0.0):
    """
    Run a semantic-ish search over the KB.

    Args:
        query: User text query.
        top_k: Max number of rows to return.
        min_score: Minimum cosine similarity threshold.

    Returns:
        List of dicts, each containing the KB row plus a 'similarity_score'.
    """
    if not query or not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string.")

    if _KB_DF is None or _VECTORIZER is None or _KB_TFIDF is None:
        build_kb_index()

    logger.info(f"KB search called: query={query!r}, top_k={top_k}, min_score={min_score}")

    query_vec = _VECTORIZER.transform([query])
    scores = cosine_similarity(query_vec, _KB_TFIDF)[0]

    # Get indices of rows sorted by similarity, descending
    top_idx = scores.argsort()[::-1][:top_k]

    results = []
    for idx in top_idx:
        score = float(scores[idx])
        if score < min_score:
            continue
        row = _KB_DF.iloc[idx].to_dict()
        row["similarity_score"] = score
        results.append(row)

    logger.info(f"KB search returned {len(results)} results.")
    return results
