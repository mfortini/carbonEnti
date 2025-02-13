#!/usr/bin/env python3

import sys
import json
import argparse
import logging
import cfscrape
import requests

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_https_connection(url: str, timeout: int = 30, verify_ssl: bool = False) -> dict:
    """
    Checks if an HTTPS connection to the given URL works and follows redirects.
    
    Note: SSL verification is disabled by default, which can be insecure.
    
    Args:
        url (str): The URL to test.
        timeout (int, optional): Request timeout in seconds. Defaults to 30.
        verify_ssl (bool, optional): Whether to enable SSL certificate verification. Defaults to False.
    
    Returns:
        dict: A dictionary containing:
            - original_url: The input URL.
            - final_url: The final URL after following redirects.
            - status_code: HTTP status code of the response.
            - https_working: True if status code is less than 400, otherwise False.
            - redirected: True if the URL was redirected.
            - details: A summary string.
            - error: Error message if an exception occurred.
    """
    scraper = cfscrape.create_scraper()  # Initialize the cfscrape scraper
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }

    try:
        response = scraper.get(url, headers=headers, timeout=timeout, 
                                 allow_redirects=True, verify=verify_ssl)
        https_working = response.status_code < 400
        final_url = response.url
        redirected = url != final_url

        result = {
            "original_url": url,
            "final_url": final_url,
            "status_code": response.status_code,
            "https_working": https_working,
            "redirected": redirected,
            "details": f"HTTPS GET request returned {response.status_code}, redirected: {redirected}"
        }
        logger.info("Connection check successful: %s", result)
        return result

    except requests.exceptions.RequestException as req_err:
        logger.error("RequestException for URL %s: %s", url, req_err)
        return {
            "original_url": url,
            "https_working": False,
            "error": str(req_err)
        }
    except Exception as ex:
        logger.exception("Unexpected error for URL %s", url)
        return {
            "original_url": url,
            "https_working": False,
            "error": str(ex)
        }

def main():
    parser = argparse.ArgumentParser(
        description="Check if an HTTPS connection works and follows redirects using cfscrape."
    )
    parser.add_argument("url", help="The URL to test.")
    parser.add_argument("--timeout", type=int, default=30, 
                        help="Timeout for the request in seconds (default: 30).")
    parser.add_argument("--verify", action="store_true", 
                        help="Enable SSL certificate verification (default: disabled).")
    parser.add_argument("--verbose", action="store_true", 
                        help="Increase output verbosity for debugging.")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    result = check_https_connection(args.url, timeout=args.timeout, verify_ssl=args.verify)
    print(json.dumps(result, indent=4))
    sys.exit(0 if result.get("https_working", False) else 1)

if __name__ == "__main__":
    main()
