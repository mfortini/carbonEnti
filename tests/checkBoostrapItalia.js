const puppeteer = require("puppeteer");

async function verifyBootstrapItalia(url) {
    const browser = await puppeteer.launch({
        args: ['--no-sandbox', '--disable-setuid-sandbox'], // Add these flags
    });
    const page = await browser.newPage();

    try {
        // Navigate to the website
        await page.goto(url);

        // Check for `window.BOOTSTRAP_ITALIA_VERSION`
        const jsVersion = await page.evaluate(() => {
            return window.BOOTSTRAP_ITALIA_VERSION || null;
        });

        // Check for CSS variable `--bootstrap-italia-version`
        const cssVersion = await page.evaluate(() => {
            const styles = getComputedStyle(document.documentElement);
            return styles.getPropertyValue("--bootstrap-italia-version")?.trim() || null;
        });

        // Close the browser
        await browser.close();

        // Return the results
        return { jsVersion, cssVersion };
    } catch (error) {
        console.error("Error verifying Bootstrap Italia:", error);
        await browser.close();
        return { jsVersion: null, cssVersion: null };
    }
}

// CLI Argument Handling
const url = process.argv[2];
if (!url) {
    console.error("Usage: node checkBootstrapItalia.js <url>");
    process.exit(1);
}

verifyBootstrapItalia(url).then((result) => {
    console.log("Bootstrap Italia Version Check:");
    console.log(`JS Version: ${result.jsVersion}`);
    console.log(`CSS Version: ${result.cssVersion}`);
});
