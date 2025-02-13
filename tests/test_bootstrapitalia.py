import asyncio
import json
from pyppeteer import launch

async def verify_bootstrap_italia(url: str) -> dict:
    """
    Verify the presence of Bootstrap Italia version information on a given URL.
    
    This function navigates to the specified URL using a headless browser,
    retrieves the JavaScript version from `window.BOOTSTRAP_ITALIA_VERSION`, and 
    the CSS version from the CSS variable `--bootstrap-italia-version`. It returns 
    a dictionary containing these values along with the URL and any error encountered.
    
    :param url: The URL of the webpage to test.
    :return: A dictionary with keys: 'url', 'js_version', 'css_version', and optionally 'error'.
    """
    browser = None
    try:
        browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = await browser.newPage()

        # Navigate to the URL with a timeout (e.g., 30 seconds)
        await page.goto(url, timeout=30000)
        # Wait until the <body> element is present to ensure the page has loaded
        await page.waitForSelector('body')

        # Extract JavaScript version from the global variable
        js_version = await page.evaluate('window.BOOTSTRAP_ITALIA_VERSION || null')

        # Extract the CSS version from the CSS variable and clean it up
        css_version = await page.evaluate('''() => {
            const styles = getComputedStyle(document.documentElement);
            return styles.getPropertyValue('--bootstrap-italia-version')?.trim() || null;
        }''')
        if css_version:
            css_version = css_version.strip('"').strip("'")
        
        result = {
            "url": url,
            "js_version": js_version,
            "css_version": css_version
        }
    except Exception as e:
        result = {
            "url": url,
            "js_version": None,
            "css_version": None,
            "error": str(e)
        }
    finally:
        # Ensure the browser is closed to avoid stray processes
        if browser:
            await browser.close()

    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print(json.dumps({
            "error": "Usage: python check_bootstrap_italia.py <url>"
        }))
        sys.exit(1)

    url = sys.argv[1]
    result = asyncio.run(verify_bootstrap_italia(url))
    print(json.dumps(result, indent=4))
