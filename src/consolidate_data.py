import json
import os
import pandas as pd
from pathlib import Path

try:
    from .utils import get_logger
except ImportError:
    from utils import get_logger

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "up_dataset_catalog.csv"


def _first(val):
    """Return first element if list, else the value itself, else None."""
    if isinstance(val, list):
        return val[0] if val else None
    return val


def _flatten_row(row):
    """Extract and rename fields from one raw API record into a flat dict."""
    node_alias = _first(row.get("node_alias"))
    source_url = f"https://www.data.gov.in{node_alias}" if node_alias else None

    keywords = row.get("keywords", [])
    tags = "|".join(str(k).strip() for k in keywords) if keywords else None

    return {
        "dataset_id":        _first(row.get("uuid")),
        "title":             _first(row.get("title")),
        "organization":      _first(row.get("field_ministry_department:name")),
        "sector":            _first(row.get("field_sector:name")),
        "tags":              tags,
        "formats":           None,   # not provided by this API endpoint
        "num_resources":     None,   # not provided by this API endpoint
        "metadata_created":  _first(row.get("created")),
        "metadata_modified": _first(row.get("changed")),
        "description":       _first(row.get("body:value")),
        "source_url":        source_url,
    }


class Transformation:
    def __init__(self, name, function):
        self.name = name
        self.function = function

    def transform(self, df):
        get_logger("Transformation").info(f"Applying transformation: {self.name}")
        return self.apply(df)

    def apply(self, df):
        return self.function(df)


def _parse_timestamps(df):
    for col in ("metadata_created", "metadata_modified"):
        df[col] = pd.to_datetime(df[col], unit="s", errors="coerce").dt.strftime("%Y-%m-%d")
    return df


def _strip_strings(df):
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda c: c.str.strip())
    return df


def _fill_missing(df):
    for col in ("title", "organization", "sector", "description", "source_url", "tags"):
        df[col] = df[col].fillna("")
    return df


def _deduplicate(df):
    before = len(df)
    df = df.drop_duplicates(subset="dataset_id", keep="first").reset_index(drop=True)
    get_logger("Consolidation").info(f"Deduplication removed {before - len(df)} duplicate rows")
    return df


def load_raw_files():
    logger = get_logger("Consolidation")
    records = []

    page_files = sorted(RAW_DIR.glob("page_*.json"))
    if not page_files:
        logger.warning("No page_*.json files in data/raw/ — run collect_data.py first.")
        return records

    for path in page_files:
        try:
            with open(path, encoding="utf-8") as f:
                rows = json.load(f)
            up_rows = [
                _flatten_row(row)
                for row in rows
                if "Uttar Pradesh" in row.get("field_asset_jurisdiction:name", [])
            ]
            records.extend(up_rows)
            logger.info(f"{path.name}: {len(up_rows)} UP records extracted")
        except Exception as e:
            logger.error(f"Failed to read {path.name}: {e} — skipping")

    logger.info(f"Total records loaded before dedup: {len(records)}")
    return records


def consolidate():
    logger = get_logger("Consolidation")

    records = load_raw_files()
    if not records:
        logger.error("No records to consolidate.")
        return

    df = pd.DataFrame(records)

    transformations = [
        Transformation("parse_timestamps", _parse_timestamps),
        Transformation("strip_strings",    _strip_strings),
        Transformation("fill_missing",     _fill_missing),
        Transformation("deduplicate",      _deduplicate),
    ]

    for t in transformations:
        df = t.transform(df)

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Saved {len(df)} rows to {OUTPUT_FILE}")
    print(df[["dataset_id", "title", "organization", "sector", "metadata_modified"]].head(10).to_string())


if __name__ == "__main__":
    consolidate()
