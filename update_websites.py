import pandas as pd
import pymongo
from datetime import datetime

# Configuration
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "website_crawler"
WEBSITES_COLLECTION = "websites"

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
websites_collection = db[WEBSITES_COLLECTION]

def update_websites_from_csv(csv_file):
    """
    Updates the websites collection in MongoDB from a CSV file.
    """
    # Load CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Ensure required columns are present
    required_columns = ["Codice_IPA", "Sito_istituzionale"]
    if not all(column in df.columns for column in required_columns):
        raise ValueError(f"CSV must contain the following columns: {required_columns}")

    for _, row in df.iterrows():
        codice_ipa = row["Codice_IPA"]
        url = row["Sito_istituzionale"]

        # Check if the entry exists
        existing_entry = websites_collection.find_one({"Codice_IPA": codice_ipa})

        if existing_entry:
            # Update the URL if it has changed
            if existing_entry["url"] != url:
                websites_collection.update_one(
                    {"Codice_IPA": codice_ipa},
                    {"$set": {"url": url}}
                )
        else:
            # Insert new entry
            websites_collection.insert_one({
                "Codice_IPA": codice_ipa,
                "url": url,
                "last_crawl": None  # Set last_crawl to None for new entries
            })

    print("Websites collection updated successfully.")

# Example usage
update_websites_from_csv("enti.csv")

