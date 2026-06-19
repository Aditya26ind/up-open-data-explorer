import requests
import json
import time
import os
from pathlib import Path
try:
    from .utils import get_logger, retry_on_exception
except ImportError:
    from utils import get_logger, retry_on_exception

BASE_URL = "https://www.data.gov.in/backend/dmspublic/v1/catalogs"
ROWS_PER_PAGE = 50
TARGET = 100
RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_OUTPUT = RAW_DIR / "datasets.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://www.data.gov.in/catalogs",
    "Accept": "application/json",
}


class Extraction:
    def __init__(self, url=BASE_URL):
        self.url = url
        self.datasets = []

    def _is_up_dataset(self, row):
        jurisdictions = row.get("field_asset_jurisdiction:name", [])
        return "Uttar Pradesh" in jurisdictions

    @retry_on_exception(max_retries=5, delay=2)
    def _fetch_page(self, offset):
        params = {
            "offset": offset,
            "limit": ROWS_PER_PAGE,
            "sort[field_asset_jurisdiction:name]": "asc",
        }
        response = requests.get(self.url, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()

    def extract(self):
        offset = 0
        logger = get_logger("Extraction")

        while True:
            body = self._fetch_page(offset)
            rows = body.get("data", {}).get("rows", [])

            if not rows:
                logger.info("No more rows returned, stopping.")
                break

            up_rows = [row for row in rows if self._is_up_dataset(row)]
            self.datasets.extend(up_rows)

            last_jurisdictions = rows[-1].get("field_asset_jurisdiction:name", [""])
            logger.info(
                f"offset={offset}: {len(up_rows)} UP records in batch "
                f"| total collected: {len(self.datasets)} "
                f"| last jurisdiction: {last_jurisdictions}"
            )

            # Save each page to raw/ for the assignment's data organisation requirement
            page_num = (offset // ROWS_PER_PAGE) + 1
            page_file = RAW_DIR / f"page_{page_num:03d}.json"
            os.makedirs(RAW_DIR, exist_ok=True)
            with open(page_file, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)

            if len(self.datasets) >= TARGET:
                logger.info(f"Reached target of {TARGET} datasets.")
                break

            # Stop scanning once jurisdictions have moved past 'U' alphabetically
            last_str = "".join(last_jurisdictions)
            if last_str and last_str[0] > "U":
                logger.info("Passed 'U' jurisdictions, no more UP records expected.")
                break

            offset += ROWS_PER_PAGE
            time.sleep(0.5)

        get_logger("Extraction").info(f"Extraction complete. Total UP datasets: {len(self.datasets)}")
        return self.datasets

    def load(self, output_path=RAW_OUTPUT):
        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.datasets, f, indent=2, ensure_ascii=False)
        get_logger("Extraction").info(f"Saved {len(self.datasets)} datasets to {output_path}")


if __name__ == "__main__":
    extractor = Extraction()
    extractor.extract()
    extractor.load()
