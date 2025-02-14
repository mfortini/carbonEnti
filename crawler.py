import threading
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED, TimeoutError
from datetime import datetime, timedelta
import subprocess
import json
import pymongo
import psutil
from logger_setup import setup_logger
import os
import argparse
import sys
import time

# Configuration
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "website_crawler"
CRAWL_INTERVAL = timedelta(days=30)
MAX_WORKERS = 4                # Website-level executor max workers
MAX_CPU_USAGE = 80
MAX_RAM_USAGE = 80
TEST_TIMEOUT = 120             # Timeout for each test in seconds
MAX_CONCURRENT_TESTS = 10      # Maximum number of test tasks running concurrently
MAX_QUEUE_SIZE = 1000          # Maximum number of website tasks allowed in the queue

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
            try:
                os.killpg(process.pid, signal.SIGTERM)
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                logger.error(f"Test {test_name} did not terminate after SIGTERM for {url} ({name}). Forcing kill with SIGKILL.")
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate(timeout=5)
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
                pgid = process.pid
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.pid == process.pid:
                            continue
                        if os.getpgid(proc.pid) == pgid:
                            logger.info(f"Killing stray process {proc.pid} ({proc.name()}) from test {test_name}.")
                            proc.kill()
                    except (psutil.NoSuchProcess, ProcessLookupError):
                        continue
            except Exception as cleanup_error:
                logger.debug(f"Error during process group cleanup for test {test_name}: {cleanup_error}")

def spawn_crawl_script(website, crawl_id, test_executor):
    """
    For a given website, schedule its tests as independent tasks in the global test executor.
    Returns immediately after scheduling.
    """
    # If shutdown has been requested, do not schedule new tests.
    if shutdown_event.is_set():
        logger.info("Shutdown event detected. Skipping scheduling of new tests.")
        return

    # We'll use a consistent document per website & crawl.
    run_timestamp = datetime.now()
    test_names = ["test_dns", "test_http", "test_ssl", "test_bootstrapitalia", "test_react_bootstrapitalia"]

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

    # Schedule each test as an independent task in the test_executor.
    for test_name in test_names:
        if check_existing_test(website["_id"], test_name, crawl_id):
            continue
        future = test_executor.submit(run_test_script, normalized_url, test_name, name)
        # Attach metadata to the future for later use.
        future.website_id = website["_id"]
        future.test_name = test_name
        future.run_timestamp = run_timestamp
        future.add_done_callback(lambda fut, cid=crawl_id: handle_test_result(fut, cid))

def handle_test_result(future, crawl_id):
    """
    Callback to handle an individual test result and store it.
    """
    try:
        result = future.result()
    except Exception as e:
        logger.exception("Error in test callback: %s", e)
        result = {
            "test_name": getattr(future, "test_name", "unknown"),
            "status": "fail",
            "error": str(e),
            "execution_timestamp": datetime.now()
        }
    website_id = getattr(future, "website_id", None)
    if website_id is not None:
        store_crawl_result(website_id, crawl_id, [result])

def store_crawl_result(website_id, crawl_id, new_tests):
    """
    Stores or appends crawl results to the database for a specific website and crawl.
    A single document per (website_id, crawl_id) is maintained.
    """
    if shutdown_event.is_set():
        logger.info("Shutdown event detected. Skipping result storage.")
        return

    logger.info(f"Storing results for website_id={website_id}, crawl_id={crawl_id}")
    existing_run = results_collection.find_one({
        "website_id": website_id,
        "crawl_id": crawl_id
    })

    if existing_run:
        existing_tests = existing_run.get("tests", [])
        for new_test in new_tests:
            if not any(test.get("test_name") == new_test.get("test_name") for test in existing_tests):
                existing_tests.append(new_test)
        results_collection.update_one(
            {"_id": existing_run["_id"]},
            {"$set": {"tests": existing_tests}}
        )
        logger.debug(f"Updated existing crawl result for website_id={website_id}")
    else:
        results_collection.insert_one({
            "website_id": website_id,
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

# Bounded submission for website tasks using a semaphore to limit queued tasks.
website_semaphore = threading.Semaphore(MAX_QUEUE_SIZE)
def bounded_submit(executor, fn, *args, **kwargs):
    website_semaphore.acquire()
    future = executor.submit(fn, *args, **kwargs)
    # Release semaphore when the task is done.
    future.add_done_callback(lambda f: website_semaphore.release())
    return future

def main():
    """
    Main function to orchestrate the crawling process.
    This design uses one executor for website-level tasks and a separate global executor for tests,
    with the test executor limiting the number of tests running concurrently.
    Bounded submission prevents queuing an excessive number of website tasks.
    """
    parser = argparse.ArgumentParser(description="Website Crawler")
    parser.add_argument("--crawl_id", required=True, help="Unique identifier for this crawl")
    args = parser.parse_args()
    crawl_id = args.crawl_id

    logger.info(f"Starting crawler with crawl_id={crawl_id}...")

    # Global executor for test tasks limited to MAX_CONCURRENT_TESTS.
    test_executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TESTS)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as website_executor:
        try:
            # Resume any incomplete tests from a previous crawl.
            incomplete_tests = fetch_incomplete_tests(crawl_id)
            if incomplete_tests:
                logger.info("Resuming incomplete tests from previous crawl...")
                for test in incomplete_tests:
                    if shutdown_event.is_set():
                        logger.info("Shutdown event detected. Exiting resume loop.")
                        break
                    bounded_submit(website_executor, spawn_crawl_script, test, crawl_id, test_executor)

            # Process websites in batches.
            for batch in fetch_websites_to_crawl(batch_size=100):
                if shutdown_event.is_set():
                    logger.info("Shutdown event detected. Breaking out of website batch loop.")
                    break
                for website in batch:
                    if shutdown_event.is_set():
                        logger.info("Shutdown event detected. Skipping scheduling new website tasks.")
                        break
                    bounded_submit(website_executor, spawn_crawl_script, website, crawl_id, test_executor)
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt detected. Exiting gracefully.")
        finally:
            website_executor.shutdown(wait=True)
            test_executor.shutdown(wait=True)
            client.close()
            logger.info("MongoDB connection closed.")
            logger.info("Crawler shutdown complete.")

if __name__ == "__main__":
    ensure_indexes()
    main()
