"""
Code Execution Tool (Safe CSV Read/Write)

This tool wraps the CSV utilities in a controlled way.
Allowed operations:
- Safe read of inbox.csv, knowledge_base.csv, tickets.csv
- Safe write of the same files (append or replace)
"""

import logging
from pathlib import Path
import pandas as pd

# Logging setup
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[CODE_EXEC] %(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Allowed dataset filenames
ALLOWED_FILES = {
    "inbox.csv",
    "knowledge_base.csv",
    "tickets.csv",
}

def _get_datasets_path() -> Path:
    """Resolve the /datasets directory relative to this file."""
    return Path(__file__).resolve().parents[2] / "datasets"


def _assert_allowed(filename: str):
    """Ensure only approved dataset files can be accessed."""
    if filename not in ALLOWED_FILES:
        raise PermissionError(
            f"File '{filename}' not allowed. Must be one of: {sorted(ALLOWED_FILES)}"
        )


def exec_read_csv(filename: str):
    """
    Safely read a CSV file and return a Python list of dict rows.
    """
    _assert_allowed(filename)
    datasets_path = _get_datasets_path()

    file_path = datasets_path / filename
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} does not exist.")

    logger.info(f"Reading CSV: {filename}")

    df = pd.read_csv(file_path)
    return df.to_dict(orient="records")


def exec_write_csv(df_like, filename: str):
    """
    Safely write a DataFrame-like object (list of dicts or DataFrame)
    into one of the allowed CSVs.
    """

    _assert_allowed(filename)
    datasets_path = _get_datasets_path()
    file_path = datasets_path / filename

    logger.info(f"Writing CSV: {filename}")

    if isinstance(df_like, pd.DataFrame):
        df = df_like
    elif isinstance(df_like, list):
        df = pd.DataFrame(df_like)
    else:
        raise ValueError("df_like must be a pandas DataFrame or list of dicts.")

    df.to_csv(file_path, index=False)
    return True


def list_valid_files():
    """Return list of allowed dataset filenames."""
    return sorted(ALLOWED_FILES)
