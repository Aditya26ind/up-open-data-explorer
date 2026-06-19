# U.P. Data Catalog

This project collects, cleans, and analyzes metadata from government datasets related to Uttar Pradesh. These datasets are published on India’s Open Government Data (OGD) platform ([ www.data.gov.in](https://www.data.gov.in) ). 

It was built for the State Data Authority (SDA) of Uttar Pradesh as part of a data engineering project aimed at supporting the development of a statewide Metadata Registry.

## Project Structure

```
up-dataset-catalog/
├── src/
│   ├── collect_data.py       # Section 1: data collection
│   ├── consolidate_data.py   # Section 2: cleaning and transformation
│   ├── analyse.py            # Section 3: analysis and charts
│   └── utils.py              # shared logger and retry decorator
├── data/
│   ├── raw/                  # one JSON file per page of API results
│   └── processed/
│       └── up_dataset_catalog.csv
├── outputs/                  # saved charts
├── requirements.txt
└── README.md
```

---

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd up-dataset-catalog

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the Pipeline

Run each script from the project root in order:

```bash
# Step 1: collect raw metadata
python src/collect_data.py

# Step 2: clean and consolidate into CSV
python src/consolidate_data.py

# Step 3: analyze and save charts
python src/analyse.py

# Step 4 : pipeline
python src/run.py
```


---

## Section 1: Data Collection

**Script:** `src/collect_data.py`

According to the assignment, the public portal must support a CKAN API at the specified URL. However, during development, the endpoint was unavailable. Instead of JSON, it returned an HTML page, indicating that the organization had moved away from CKAN.

**Modified approach:** While researching, it was found using DevTools in the browser that there is an internal REST API for the public site. This API can be accessed with a search query using the following link:

```
GET https://www.data.gov.in/backend/dmspublic/v1/catalogs
    ?offset=0&limit=50&sort[field_asset_jurisdiction:name]=asc
```

The results will come back in JSON format. However, requests must include the User-Agent string for the browser to avoid being blocked by the server.

**Pagination and Filtering Strategy:** The API does not allow keyword searches through the exposed methods. Sorting by `field_asset_jurisdiction:name` in ascending order will cause `Uttar Pradesh` districts (Agra, Allahabad, Ambedkar Nagar, etc.) to appear on earlier pages. The script will paginate through the API, filtering results with `field_asset_jurisdiction:name` that include `Uttar Pradesh` and stop after reaching the `U` districts in alphabetical order.

Each set of raw results will save into a folder named `data/raw/page_NNN.json`, where `NNN` refers to the page order. A total of **114 datasets returned from 102 pages** for Uttar Pradesh.

## Section 2: Consolidation and Transformation

**Script:** `src/consolidate_data.py`

The script reads every `page_*.json` file from `data/raw/`, re-filters for UP records, flattens each record into a single row, applies a series of transformations, removes duplicates, and writes the final CSV.

**Field mapping from raw API to output columns:**

| Output column | Raw API field |
|---|---|
| `dataset_id` | `uuid[0]` |
| `title` | `title[0]` |
| `organization` | `field_ministry_department:name[0]` |
| `sector` | `field_sector:name[0]` |
| `tags` | `keywords` joined with `\|` |
| `metadata_created` | `created[0]` (Unix timestamp) |
| `metadata_modified` | `changed[0]` (Unix timestamp) |
| `description` | `body:value[0]` |
| `source_url` | `https://www.data.gov.in` + `node_alias[0]` |

**Transformation steps applied in order:**
1. `parse_timestamps` — converts Unix integer timestamps to `YYYY-MM-DD`
2. `strip_strings` — removes leading and trailing whitespace from all string columns
3. `fill_missing` — replaces `None` with `""` for text fields
4. `deduplicate` — removes duplicate `dataset_id` rows, keeping the first occurrence

**Handling missing values:** The `formats` and `num_resources` columns remain as `None`. The backend API does not provide resource-level details; obtaining them would require 114 additional HTTP requests, which is beyond the current scope. These gaps are noted in the output CSV and mentioned in the analysis.

---

## Section 3: Main Takeaways From The Analysis

The charts created from the data analysis are stored in `outputs/`. You can run the script located in `src/analyse.py` to regenerate these charts.

### Conclusion 1 - The Ministry of Housing And Urban Development Controls Most Open Data For Uttar Pradesh

Most open data for Uttar Pradesh (92%) comes from the Ministry of Housing And Urban Affairs through its Smart Cities Mission. The Ministry has provided 105 out of the total 114 datasets available. If the State Data Access (SDA) Registry is to successfully increase the availability of open data in Uttar Pradesh, it must target state government departments since none of these departments are currently represented on the National Open Data Portal.

### Conclusion 2 - Most Datasets Were Last Updated In 2025 With Many Outdated Records

Among the available datasets, 86 (75%) have a metadata modified date of 2025, indicating recency. However, 28 datasets have not been updated since before 2022, with some dating back to 2019. This points to a need for the SDA Registry to offer a way to track how current the data is, along with notifications to the responsible departments when datasets are no longer fresh.

### Conclusion 3 - The Datasets Focus On Urban Infrastructure

The top five tags used to classify the datasets (water, sanitation, sewerage, toilets, and households) and the top sector represented (Environment and Forest and Road Transport) are all directly tied to the Smart Cities Mission. Very few datasets are related to Agriculture, Education, and Social Welfare, which are key areas for the State Data Agency (SDA). The SDA Registry should prioritize assisting agencies that have not yet contributed data to improve the overall availability of open datasets in Uttar Pradesh.

## Limitations and Assumptions

- The CKAN API mentioned in the assignment (`/api/3/action/package_search`) is not functional on the live site. The adapted approach uses an internal endpoint that might change without notice.
- Obtaining `formats` and `num_resources` fields required individual HTTP requests per dataset, which was beyond the scope of the project.
- The collection stops paginating once the alphabetical order of jurisdictions moves past "U." This is reliable based on the sort order but could theoretically overlook datasets tagged with both a UP district and a later-alphabet non-UP jurisdiction.
- The dataset count (114) only includes datasets explicitly tagged with `"Uttar Pradesh"` in the jurisdiction field. Datasets relevant to UP that are labeled as All-India are not included.

# Upcoming Enhancements:

1. Implement idempotency in the workflow to prevent duplicate entries.
2. Introduce orchestration for batch processing at scheduled intervals.
3. Use cloud platforms like AWS.
4. Use PySpark Compute Engine to improve performance.
5. Apply salting and broadcasting techniques to reduce shuffling.
6. Transition to a serverless architecture.
7. Use a BI tool for better data visualization.
8. Move data to both a data lake and a data warehouse, executing transformations there.
9. Use dbt for data processing and Redshift for data storage.
10. Choose ELT instead of ETL methods.

# Information.

Just to show raw data i added json file in folder but practically not recommended to push big data files to github.