import threading
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from datetime import datetime, timedelta
import subprocess
import json
import pymongo
import psutil
from logger_setup import setup_logger
import os
import argparse
import sys
import time  # used for graceful delays if needed

# Configuration
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "website_crawler"
CRAWL_INTERVAL = timedelta(days=30)
MAX_WORKERS = 4
MAX_TEST_THREADS = 3
MAX_CPU_USAGE = 80
MAX_RAM_USAGE = 80
TEST_TIMEOUT = 120  # Timeout for each test in seconds

# Directory containing test scripts
TESTS_DIR = "tests"

# MongoDB Connection
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
websites_collection = db["websites"]
results_collection = db["crawl_results"]

# Initialize logger
logger = setup_logger("crawler")

# Shutdown event for graceful termination
shutdown_event = threading.Event()

def handle_sigterm(signal_number, frame):
    """
    Signal handler for SIGTERM and SIGINT to initiate a graceful shutdown.
    """
    logger.warning(f"Signal {signal_number} received. Initiating graceful shutdown...")
    shutdown_event.set()

# Register signal handlers for SIGTERM and SIGINT
signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

def monitor_resources():
    """
    Monitor system resources (CPU and RAM usage).
    If resource usage is too high, log a warning.
    """
    if shutdown_event.is_set():
        logger.info("Shutdown event detected. Stopping resource monitoring.")
        return False

    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    logger.debug(f"Resource check: CPU={cpu_usage}%, RAM={ram_usage}%")
    if cpu_usage >= MAX_CPU_USAGE or ram_usage >= MAX_RAM_USAGE:
        logger.warning("High resource usage detected; consider pausing new tasks.")
        return False
    return True

def fetch_incomplete_tests(crawl_id):
    """
    Fetch websites with incomplete tests from the previous crawl session.
    """
    logger.info("Fetching websites with incomplete tests...")
    incomplete_tests = results_collection.find({"crawl_id": crawl_id, "tests.status": {"$ne": "success"}})
    return [test for test in incomplete_tests]

def fetch_websites_to_crawl(batch_size=100):
    """
    Incrementally fetch websites that need to be crawled.
    """
    logger.info("Fetching websites to crawl incrementally...")
    cutoff_time = datetime.now() - CRAWL_INTERVAL

    query = {
        "$or": [
            {"last_crawl": {"$lt": cutoff_time}},
            {"last_crawl": None}
        ]
    }

    cursor = websites_collection.find(query).sort("last_crawl", 1)

    batch = []
    for website in cursor:
        if shutdown_event.is_set():
            logger.info("Shutdown event detected. Stopping incremental fetch.")
            break
        batch.append(website)
        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch

def normalize_url(url):
    """
    Normalize the URL by ensuring it starts with 'https://'.
    """
    if not url:
        raise ValueError("URL is missing or None.")
    if not isinstance(url, str):
        raise ValueError("URL is not a string")
    if url.startswith("http://"):
        return url.replace("http://", "https://", 1)
    elif not url.startswith("https://"):
        return f"https://{url}"
    return url

def check_existing_test(website_id, test_name, crawl_id):
    """
    Check if a specific test for a website has already been executed during this crawl.
    """
    result = results_collection.find_one({
        "website_id": website_id,
        "crawl_id": crawl_id,
        "tests": {"$elemMatch": {"test_name": test_name}}
    })
    return result is not None

def run_test_script(url, test_name, name):
    """
    Executes a specific test script located in TESTS_DIR for a website.
    Ensures that all spawned processes are terminated at the end of the test.
    Always returns a dict that includes 'test_name' and 'status'.
    """
    execution_timestamp = datetime.now()
    logger.info(f"Test {test_name} starting for website {url}.")

    if not isinstance(url, str):
        logger.error(f"Invalid URL provided to {test_name} for {name}: {url} (must be a string).")
        return {
            "test_name": test_name,
            "url": url,
            "status": "fail",
            "error": "Invalid URL (must be a string)",
            "execution_timestamp": execution_timestamp,
        }

    test_script_path = os.path.join(TESTS_DIR, f"{test_name}.py")
    if not os.path.isfile(test_script_path):
        logger.error(f"Test script {test_script_path} not found for {name}.")
        return {
            "test_name": test_name,
            "url": url,
            "status": "fail",
            "error": f"Test script {test_script_path} not found.",
            "execution_timestamp": execution_timestamp,
        }

    process = None
    try:
        # Start the test in a new process group.
        process = subprocess.Popen(
            ["python3", test_script_path, url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True
        )

        try:
            stdout, stderr = process.communicate(timeout=TEST_TIMEOUT)
        except subprocess.TimeoutExpired:
            logger.error(f"Test {test_name} timed out for {url} ({name}). Killing process group.")
            # Kill the entire process group.
            os.killpg(process.pid, signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=10)
            process.wait()
            return {
                "test_name": test_name,
                "url": url,
                "status": "fail",
                "error": "TimeoutExpired",
                "execution_timestamp": execution_timestamp,
            }

        if process.returncode == 0:
            try:
                test_result = json.loads(stdout)
            except json.JSONDecodeError:
                logger.error(f"Test {test_name} returned invalid JSON for {url} ({name}).")
                return {
                    "test_name": test_name,
                    "url": url,
                    "status": "fail",
                    "error": "Invalid JSON output",
                    "execution_timestamp": execution_timestamp,
                }
            # Ensure required keys are present.
            test_result["execution_timestamp"] = execution_timestamp
            test_result.setdefault("test_name", test_name)
            test_result.setdefault("status", "success")
            return test_result
        else:
            logger.error(f"Test {test_name} failed for {url} ({name}): {stderr}")
            return {
                "test_name": test_name,
                "url": url,
                "status": "fail",
                "error": stderr,
                "execution_timestamp": execution_timestamp,
            }
    except Exception as e:
        logger.exception(f"Error running test {test_name} for {url} ({name}): {e}")
        return {
            "test_name": test_name,
            "url": url,
            "status": "fail",
            "error": str(e),
            "execution_timestamp": execution_timestamp,
        }
    finally:
        # Cleanup: Ensure any stray processes in the test's process group are terminated.
        if process is not None:
            try:
                # With start_new_session=True, the process group ID is the same as the process PID.
                pgid = process.pid
                # Iterate over all processes to find those in the same process group.
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        # Skip the main test process.
                        if proc.pid == process.pid:
                            continue
                        # If the process is in the same process group, kill it.
                        if os.getpgid(proc.pid) == pgid:
                            logger.info(f"Killing stray process {proc.pid} ({proc.name()}) from test {test_name}.")
                            proc.kill()
                    except (psutil.NoSuchProcess, ProcessLookupError):
                        continue
            except Exception as cleanup_error:
                logger.debug(f"Error during process group cleanup for test {test_name}: {cleanup_error}")


def spawn_crawl_script(website, crawl_id):
    """
    Spawns test scripts in parallel for a single website after validating and normalizing the URL.
    Only tests that have not yet been executed for this crawl (based on crawl_id) are run.
    """
    run_timestamp = datetime.now()
    tests = []
    #test_names = ["test_dns", "test_http", "test_ssl", "test_bootstrapitalia", "test_react_bootstrapitalia"]
    test_names = ["test_dns", "test_http", "test_ssl", "test_bootstrapitalia"]
    #test_names = ["test_dns"]
    #test_names = ["test_dns", "test_http"]

    url = website.get("url")
    name = website.get("name") or website.get("_id", "Unknown")
    if not url:
        logger.error(f"Website ID {website['_id']} ({url}) is missing a URL. Skipping tests.")
        return

    try:
        normalized_url = normalize_url(url)
    except ValueError as e:
        logger.error(f"Error normalizing URL for website ID {website['_id']} ({url}): {e}")
        return

    logger.info(f"Starting crawl for website: {normalized_url} ({url})")

    # Only run tests that have not been executed yet for this crawl_id.
    with ThreadPoolExecutor(max_workers=MAX_TEST_THREADS) as executor:
        future_to_test = {
            executor.submit(run_test_script, normalized_url, test_name, name): test_name
            for test_name in test_names
            if not check_existing_test(website["_id"], test_name, crawl_id)
        }

        for future in as_completed(future_to_test):
            test_name = future_to_test[future]
            try:
                result = future.result()
                if result is not None:
                    # Enforce that both test_name and status are set
                    result.setdefault("test_name", test_name)
                    result.setdefault("status", "success")
                    tests.append(result)
                    logger.info(f"Test {test_name} completed for website {url}.")
            except Exception as e:
                logger.exception(f"Error running test {test_name} for {normalized_url} ({url}): {e}")

    if tests:
        store_crawl_result(website["_id"], run_timestamp, crawl_id, tests)

def store_crawl_result(website_id, run_timestamp, crawl_id, new_tests):
    """
    Stores or appends crawl results to the database for a specific run.
    """
    if shutdown_event.is_set():
        logger.info("Shutdown event detected. Skipping result storage.")
        return

    logger.info(f"Storing results for website_id={website_id}, run_timestamp={run_timestamp}, crawl_id={crawl_id}")
    existing_run = results_collection.find_one(
        {"website_id": website_id, "run_timestamp": run_timestamp, "crawl_id": crawl_id}
    )

    if existing_run:
        existing_tests = existing_run["tests"]
        for new_test in new_tests:
            # Only add tests that are not already stored (based on test_name)
            if not any(test["test_name"] == new_test["test_name"] for test in existing_tests):
                existing_tests.append(new_test)

        results_collection.update_one(
            {"_id": existing_run["_id"]},
            {"$set": {"tests": existing_tests}}
        )
        logger.debug(f"Updated existing crawl result for website_id={website_id}")
    else:
        results_collection.insert_one({
            "website_id": website_id,
            "run_timestamp": run_timestamp,
            "crawl_id": crawl_id,
            "tests": new_tests
        })
        logger.debug(f"Inserted new crawl result for website_id={website_id}")

def ensure_indexes():
    """
    Ensure MongoDB indexes are in place for optimal query performance.
    """
    logger.info("Ensuring MongoDB indexes...")
    websites_collection.create_index([("last_crawl", pymongo.ASCENDING)])
    results_collection.create_index([("crawl_id", pymongo.ASCENDING)])
    logger.info("Indexes created successfully.")

def main():
    """
    Main function to orchestrate the crawling process with incremental reading.
    """
    parser = argparse.ArgumentParser(description="Website Crawler")
    parser.add_argument("--crawl_id", required=True, help="Unique identifier for this crawl")
    args = parser.parse_args()

    crawl_id = args.crawl_id
    logger.info(f"Starting crawler with crawl_id={crawl_id}...")

    try:
        # Resume any incomplete tests from this crawl
        incomplete_tests = fetch_incomplete_tests(crawl_id)
        if incomplete_tests:
            logger.info("Resuming incomplete tests from previous crawl...")
            for test in incomplete_tests:
                if shutdown_event.is_set():
                    logger.info("Shutdown event detected. Exiting resume loop.")
                    break
                spawn_crawl_script(test, crawl_id)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for batch in fetch_websites_to_crawl(batch_size=100):
                if shutdown_event.is_set():
                    logger.info("Shutdown event detected. Breaking out of website batch loop.")
                    break
                futures = [executor.submit(spawn_crawl_script, website, crawl_id) for website in batch]

                for future in as_completed(futures):
                    if shutdown_event.is_set():
                        logger.info("Shutdown event detected. Waiting for active tasks to finish.")
                        break
                    try:
                        future.result()
                    except Exception as e:
                        logger.exception("Error in crawling process: %s", e)
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt detected. Exiting gracefully.")
    finally:
        # Ensure MongoDB client is closed to avoid resource leaks.
        client.close()
        logger.info("MongoDB connection closed.")
        logger.info("Crawler shutdown complete.")

if __name__ == "__main__":
    ensure_indexes()
    main()
