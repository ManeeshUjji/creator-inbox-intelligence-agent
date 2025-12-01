"""
Safe CSV read/write wrapper.
"""

import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[CODE_EXEC] %(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

ALLOWED = {"inbox.csv", "knowledge_base.csv", "tickets.csv"}

def _get_datasets_path():
    return Path(__file__).resolve().parents[2] / "datasets"

def _assert_allowed(filename):
    if filename not in ALLOWED:
        raise PermissionError(f"{filename} not allowed. Allowed: {ALLOWED}")

def exec_read_csv(filename):
    _assert_allowed(filename)
    path = _get_datasets_path() / filename
    df = pd.read_csv(path)
    return df

def exec_write_csv(df_like, filename: str):
    _assert_allowed(filename)
    path = _get_datasets_path() / filename
    if isinstance(df_like, list):
        df_like = pd.DataFrame(df_like)
    df_like.to_csv(path, index=False)
    return True

def list_valid_files():
    return sorted(ALLOWED)
