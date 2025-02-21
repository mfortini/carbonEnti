import csv
from pymongo import MongoClient
import argparse
from datetime import datetime

def extract_data(crawl_id, output_file="output.csv"):
    # Connect to MongoDB (adjust connection string and database name as needed)
    client = MongoClient("mongodb://localhost:27017")
    db = client["website_crawler"]
    websites_col = db["websites"]
    crawl_results_col = db["crawl_results"]

    # Query crawl_results based on the provided crawl_id
    crawl_docs = crawl_results_col.find({"crawl_id": crawl_id})
    rows = []
    
    # These test names will be handled in a fixed way (or skipped in the dynamic part)
    fixed_test_names = {"test_lighthouse", "test_firstMeaningfulPaint", "test_totalByteWeight", "test_bootstrapitalia"}

    for doc in crawl_docs:
        # Retrieve the corresponding website document using website_id.
        website_id = doc.get("website_id")
        website = websites_col.find_one({"_id": website_id})
        if not website:
            continue

        row = {}

        # Fixed field: Codice_IPA from the website document.
        row["Codice_IPA"] = website.get("Codice_IPA", "")

        # Determine the URL: first try the website document's url;
        # if not valid (e.g. "NaN"), fall back to the test_bootstrapitalia url.
        website_url = website.get("url", "")
        if isinstance(website_url, dict):
            website_url = website_url.get("$numberDouble", "")
        if website_url == "NaN" or not website_url:
            test_bootstrap = next((t for t in doc.get("tests", []) if t.get("test_name") == "test_bootstrapitalia"), {})
            row["url"] = test_bootstrap.get("url", "")
        else:
            row["url"] = website_url

        # Fixed columns left empty as specified.
        row["lighthouseScore"] = ""
        row["firstMeaningfulPaint"] = ""
        row["totalByteWeight"] = ""
        row["bootstrap"] = ""
        row["bootstrapItalia"] = ""

        # For test_bootstrapitalia, add additional columns for js and css versions.
        test_bootstrap = next((t for t in doc.get("tests", []) if t.get("test_name") == "test_bootstrapitalia"), {})
        row["bootstrap2_js"] = test_bootstrap.get("js_version", "")
        row["bootstrap2_css"] = test_bootstrap.get("css_version", "")

        # Process any additional tests not handled in the fixed columns.
        # For each such test, add dynamic columns: <test_name>_status, <test_name>_details, and <test_name>_execution_timestamp.
        for test in doc.get("tests", []):
            test_name = test.get("test_name", "")
            if test_name in fixed_test_names:
                continue
            status_key = f"{test_name}_status"
            details_key = f"{test_name}_details"
            timestamp_key = f"{test_name}_execution_timestamp"

            row[status_key] = test.get("status", "")
            row[details_key] = test.get("details", "")
            exec_ts = test.get("execution_timestamp", "")
            if exec_ts and hasattr(exec_ts, "isoformat"):
                row[timestamp_key] = exec_ts.isoformat()
            else:
                row[timestamp_key] = exec_ts if exec_ts is not None else ""

        rows.append(row)

    # Fixed header columns in the required order.
    fixed_columns = [
        "Codice_IPA", "url", "lighthouseScore", "firstMeaningfulPaint",
        "totalByteWeight", "bootstrap", "bootstrapItalia", "bootstrap2_js", "bootstrap2_css"
    ]

    # Collect dynamic columns from all rows (those not in the fixed columns).
    dynamic_columns = set()
    for row in rows:
        for key in row.keys():
            if key not in fixed_columns:
                dynamic_columns.add(key)
    dynamic_columns = sorted(dynamic_columns)

    final_columns = fixed_columns + dynamic_columns

    # Write the output CSV file.
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=final_columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Data extracted to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract website test results for a specific crawl_id and output a CSV file with fixed and dynamic columns."
    )
    parser.add_argument("crawl_id", type=str, help="The crawl_id to filter crawl_results")
    parser.add_argument("--output", type=str, default="output.csv", help="Output CSV file name")
    args = parser.parse_args()

    extract_data(args.crawl_id, args.output)
