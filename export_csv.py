import csv
from pymongo import MongoClient
import argparse
from datetime import datetime
import sys

def list_crawl_ids():
    client = MongoClient("mongodb://localhost:27017")
    db = client["website_crawler"]
    crawl_results_col = db["crawl_results"]

    crawl_ids = crawl_results_col.distinct("crawl_id")
    if crawl_ids:
        print("Crawl IDs disponibili:")
        for cid in crawl_ids:
            print(f" - {cid}")
    else:
        print("Nessun crawl_id trovato nel database.")

def extract_data(crawl_id, output_file="output.csv"):
    client = MongoClient("mongodb://localhost:27017")
    db = client["website_crawler"]
    websites_col = db["websites"]
    crawl_results_col = db["crawl_results"]

    crawl_docs = crawl_results_col.find({"crawl_id": crawl_id})
    rows = []
    
    fixed_test_names = {"test_lighthouse", "test_bootstrapitalia"}

    for doc in crawl_docs:
        website_id = doc.get("website_id")
        website = websites_col.find_one({"_id": website_id})
        if not website:
            continue

        row = {}
        row["Codice_IPA"] = website.get("Codice_IPA", "")

        test_ssl = next((t for t in doc.get("tests", []) if t.get("test_name") == "test_ssl"), {})
        row["url"] = test_ssl.get("url", "")

        test_lighthouse = next((t for t in doc.get("tests", []) if t.get("test_name") == "test_lighthouse"), {})
        row["lighthouseScore"] = test_lighthouse.get("lighthouseScore", "")
        row["firstMeaningfulPaint"] = test_lighthouse.get("largestContentfulPaint", "")
        row["totalByteWeight"] = test_lighthouse.get("totalByteWeight", "")
        row["accessibilityScore"] = test_lighthouse.get("accessibilityScore", "")

        row["bootstrap"] = ""
        row["bootstrapItalia"] = ""

        test_bootstrap = next((t for t in doc.get("tests", []) if t.get("test_name") == "test_bootstrapitalia"), {})
        row["bootstrap2_js"] = test_bootstrap.get("js_version", "")
        row["bootstrap2_css"] = test_bootstrap.get("css_version", "")

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

    fixed_columns = [
        "Codice_IPA", "url", "lighthouseScore", "firstMeaningfulPaint", "accessibilityScore",
        "totalByteWeight", "bootstrap", "bootstrapItalia", "bootstrap2_js", "bootstrap2_css"
    ]

    dynamic_columns = set()
    for row in rows:
        for key in row.keys():
            if key not in fixed_columns:
                dynamic_columns.add(key)
    dynamic_columns = sorted(dynamic_columns)

    final_columns = fixed_columns + dynamic_columns

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
    parser.add_argument("crawl_id", nargs="?", help="The crawl_id to filter crawl_results")
    parser.add_argument("--output", type=str, default="output.csv", help="Output CSV file name")
    args = parser.parse_args()

    if not args.crawl_id:
        list_crawl_ids()
        sys.exit(0)

    extract_data(args.crawl_id, args.output)
