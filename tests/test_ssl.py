#!/usr/bin/env python3
import sys
import json
import ssl
import socket
from urllib.parse import urlparse
from typing import Any, Dict

def check_https_connection(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Checks if an HTTPS connection works and validates the certificate.
    
    Parameters:
        url (str): The HTTPS URL to check.
        timeout (int): Connection timeout in seconds (default: 30).
    
    Returns:
        dict: A dictionary with connection and certificate details.
    """
    parsed_url = urlparse(url)
    
    # Validate URL scheme
    if parsed_url.scheme != 'https':
        return {
            "url": url,
            "https_working": False,
            "certificate_valid": False,
            "error": "URL must use HTTPS scheme."
        }
    
    hostname = parsed_url.netloc
    if not hostname:
        return {
            "url": url,
            "https_working": False,
            "certificate_valid": False,
            "error": "Invalid URL: Hostname could not be determined."
        }
    
    try:
        # Establish an SSL connection using a default context
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                
                # Extract certificate details
                issuer = cert.get("issuer")
                subject = cert.get("subject")
                not_before = cert.get("notBefore")
                not_after = cert.get("notAfter")
                
                return {
                    "url": url,
                    "https_working": True,
                    "certificate_valid": True,
                    "certificate_issuer": issuer,
                    "certificate_subject": subject,
                    "certificate_valid_from": not_before,
                    "certificate_valid_to": not_after,
                    "message": "HTTPS connection established and certificate is valid."
                }
    
    except ssl.SSLCertVerificationError as e:
        return {
            "url": url,
            "https_working": False,
            "certificate_valid": False,
            "error": f"Certificate verification failed: {e}"
        }
    except socket.timeout as e:
        return {
            "url": url,
            "https_working": False,
            "certificate_valid": False,
            "error": f"Connection timed out: {e}"
        }
    except socket.gaierror as e:
        return {
            "url": url,
            "https_working": False,
            "certificate_valid": False,
            "error": f"Address-related error connecting to server: {e}"
        }
    except Exception as e:
        return {
            "url": url,
            "https_working": False,
            "certificate_valid": False,
            "error": str(e)
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_https.py <https_url>", file=sys.stderr)
        sys.exit(1)
    
    url = sys.argv[1]
    result = check_https_connection(url)
    print(json.dumps(result, indent=4))
    
    # Exit with a non-zero status if the connection or certificate check failed
    sys.exit(0 if result.get("https_working") and result.get("certificate_valid") else 1)

if __name__ == "__main__":
    main()
