#!/usr/bin/env python3
import sys
import json
import socket
import argparse
from urllib.parse import urlparse

def check_dns_resolution(url):
    """
    Resolves the DNS name for the given URL.

    If the URL does not include a scheme, it assumes 'http://'.
    Returns a dictionary with resolution details or an error message.
    """
    try:
        parsed = urlparse(url)
        # If no scheme is provided, assume HTTPS and re-parse.
        if not parsed.scheme:
            url = "https://" + url
            parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("Invalid URL: no hostname found.")
        ip_address = socket.gethostbyname(hostname)
        return {
            "hostname": hostname,
            "ip_address": ip_address,
            "resolved": True,
            "details": f"Resolved to {ip_address}"
        }
    except Exception as e:
        return {
            "hostname": url,
            "resolved": False,
            "error": str(e)
        }

def main():
    parser = argparse.ArgumentParser(description="Check DNS resolution for a given URL.")
    parser.add_argument("url", help="The URL to resolve (e.g., http://www.example.com)")
    args = parser.parse_args()

    result = check_dns_resolution(args.url)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("resolved") else 1)

if __name__ == "__main__":
    main()
