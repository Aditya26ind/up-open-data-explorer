import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

try:
    from .utils import get_logger
except ImportError:
    from utils import get_logger

OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"


class Analyzer:
    def __init__(self, dataset):
        self.dataset = dataset
        os.makedirs(OUTPUTS_DIR, exist_ok=True)

    def _save(self, fig, filename):
        path = OUTPUTS_DIR / filename
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        get_logger("Analyzer").info(f"Saved chart: {path}")

    def analyze(self):
        logger = get_logger("Analyzer")

        # --- Top organisations ---
        org_counts = (
            self.dataset.groupby("organization")["dataset_id"]
            .nunique()
            .sort_values(ascending=False)
            .head(10)
        )
        logger.info("Processing number of datasets per organisation")
        fig, ax = plt.subplots(figsize=(10, 6))
        org_counts.sort_values().plot(kind="barh", ax=ax, color="steelblue")
        ax.set_title("Top 10 Organisations by Dataset Count")
        ax.set_xlabel("Number of Datasets")
        self._save(fig, "top_organisations.png")

        # --- Sector distribution (replaces format_distribution — formats unavailable from API) ---
        sector_counts = (
            self.dataset.groupby("sector")["dataset_id"]
            .nunique()
            .sort_values(ascending=False)
            .head(10)
        )
        logger.info("Processing distribution of datasets by sector")
        fig, ax = plt.subplots(figsize=(10, 6))
        sector_counts.sort_values().plot(kind="barh", ax=ax, color="darkorange")
        ax.set_title("Dataset Count by Sector (formats unavailable from API)")
        ax.set_xlabel("Number of Datasets")
        self._save(fig, "format_distribution.png")

        # --- Data freshness ---
        self.dataset["year_modified"] = pd.to_datetime(
            self.dataset["metadata_modified"], errors="coerce"
        ).dt.year
        freshness = self.dataset["year_modified"].value_counts().sort_index()
        logger.info("Processing data freshness by year last modified")
        fig, ax = plt.subplots(figsize=(10, 5))
        freshness.plot(kind="bar", ax=ax, color="seagreen")
        ax.set_title("Datasets by Year Last Modified")
        ax.set_xlabel("Year")
        ax.set_ylabel("Number of Datasets")
        self._save(fig, "data_freshness.png")

        # --- Top tags ---
        top_tags = (
            self.dataset["tags"]
            .dropna()
            .str.split("|")
            .explode()
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .value_counts()
            .head(20)
        )
        logger.info("Processing top tags across datasets")
        fig, ax = plt.subplots(figsize=(10, 8))
        top_tags.sort_values().plot(kind="barh", ax=ax, color="mediumpurple")
        ax.set_title("Top 20 Tags Across UP Datasets")
        ax.set_xlabel("Frequency")
        self._save(fig, "top_tags.png")

        insights = {
            "top_organizations": org_counts,
            "top_sectors":       sector_counts,
            "data_freshness":    freshness,
            "top_tags":          top_tags,
        }

        logger.info("Analysis complete.")
        return insights


if __name__ == "__main__":
    csv_path = Path(__file__).parent.parent / "data" / "processed" / "up_dataset_catalog.csv"
    dataset = pd.read_csv(csv_path)
    analyzer = Analyzer(dataset)
    results = analyzer.analyze()

    print("\n--- Top Organisations ---")
    print(results["top_organizations"].to_string())
    print("\n--- Top Sectors ---")
    print(results["top_sectors"].to_string())
    print("\n--- Data Freshness (by year) ---")
    print(results["data_freshness"].to_string())
    print("\n--- Top 20 Tags ---")
    print(results["top_tags"].to_string())
