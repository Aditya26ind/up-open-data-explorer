import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from pathlib import Path

import collect_data
import consolidate_data
import analyse

CSV_PATH = Path(__file__).parent.parent / "data" / "processed" / "up_dataset_catalog.csv"


class Pipeline:
    def __init__(self):
        self.extractor = collect_data.Extraction()
        self.analyzer = None

    def run(self):
        # Step 1: collect
        self.extractor.extract()
        self.extractor.load()

        # Step 2: consolidate
        consolidate_data.consolidate()

        # Step 3: analyse
        df = pd.read_csv(CSV_PATH)
        self.analyzer = analyse.Analyzer(df)
        self.analyzer.analyze()


if __name__ == "__main__":
    pipeline = Pipeline()
    pipeline.run()
