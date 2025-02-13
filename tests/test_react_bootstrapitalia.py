import asyncio
import json
import argparse
import random
from urllib.parse import urlparse, urljoin
from pyppeteer import launch

async def collect_bootstrap_components_union(url, max_clicks=0, debug=False):
    """
    1. Go to the given `url`.
    2. Extract internal links (same domain or subdomains).
    3. Randomly shuffle them and take up to `max_clicks`.
    4. For each link, do a direct goto(...) so the SPA re-initializes and sets BOOTSTRAP_USED_COMPONENTS.
    5. Return the union of all components found across those visited links.
    """
    browser = None
    try:
        if debug:
            print(f"Launching headless browser for URL: {url}")
        browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = await browser.newPage()

        if debug:
            print(f"Visiting initial URL: {url}")
        await page.goto(url, waitUntil='networkidle2')

        # Determine the actual domain (after redirects)
        current_url = page.url
        base_domain = urlparse(current_url).netloc
        if debug:
            print(f"Actual starting domain after potential redirect: {base_domain}")

        # Helper to verify internal links (same domain or subdomains)
        def is_internal_link(link):
            parsed_link = urlparse(link)
            return parsed_link.netloc.endswith(base_domain)

        if debug:
            print("Extracting links from the initial page...")
        links = await page.evaluate('''() => Array.from(document.querySelectorAll('a'))
            .map(link => ({ href: link.href, text: link.innerText.trim() }))
            .filter(link => link.href.startsWith('http'))
        ''')

        # Normalize and filter links to include only internal ones
        filtered_links = [
            {"href": urljoin(current_url, link["href"]), "text": link["text"]}
            for link in links if is_internal_link(link["href"])
        ]
        if debug:
            print(f"Found {len(filtered_links)} internal links after filtering.")

        random.shuffle(filtered_links)
        links_to_visit = filtered_links[:max_clicks] if max_clicks > 0 else []
        if debug:
            print(f"Visiting {len(links_to_visit)} links (max_clicks={max_clicks}).")

        components_union = set()

        # Visit each selected link
        for idx, link in enumerate(links_to_visit, start=1):
            route = link["href"]
            if debug:
                print(f"\n[{idx}] Loading link: {route} (text: {link['text']})")
            try:
                await page.goto(route, waitUntil='networkidle2')
                # Allow time for SPA components to load
                await asyncio.sleep(2)
                route_components = await page.evaluate('window.BOOTSTRAP_USED_COMPONENTS || []')
                if debug:
                    print(f" -> Found components: {route_components}")
                components_union.update(route_components)
            except Exception as link_error:
                if debug:
                    print(f"Failed to load {route}: {link_error}")
                continue

        return list(components_union)

    except Exception as e:
        if debug:
            print(f"Encountered error: {e}")
        return []
    finally:
        if browser:
            try:
                await browser.close()
                if debug:
                    print("Browser closed successfully.")
            except Exception as close_error:
                if debug:
                    print(f"Error closing browser: {close_error}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Collect the union of BOOTSTRAP_USED_COMPONENTS across random internal links."
    )
    parser.add_argument(
        "url",
        help="The starting URL of the site to check, e.g. https://example.com"
    )
    parser.add_argument(
        "--max-clicks",
        type=int,
        default=20,
        help="Maximum number of links to visit (0 means don't visit any)."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output."
    )
    args = parser.parse_args()

    try:
        union_components = asyncio.run(
            collect_bootstrap_components_union(args.url, max_clicks=args.max_clicks, debug=args.debug)
        )
        result = {
            "status": "success",
            "url": args.url,
            "max_clicks": args.max_clicks,
            "bootstrap_components": union_components,
        }
    except Exception as main_error:
        result = {
            "status": "error",
            "url": args.url,
            "max_clicks": args.max_clicks,
            "error_message": str(main_error),
        }

    print(json.dumps(result, indent=4))
