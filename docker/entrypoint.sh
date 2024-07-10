#!/bin/sh

# Check if URL is provided
if [ -z "$1" ]; then
  echo "Error: No URL provided."
  echo "Usage: docker run <image> <URL> <output-file>"
  exit 1
fi

# Check if output file name is provided
if [ -z "$2" ]; then
  echo "Error: No output file name provided."
  echo "Usage: docker run <image> <URL> <output-file>"
  exit 1
fi

URL=$1
OUTPUT_FILE=$2

# Run LHCI collect with the provided URL and output JSON to the results directory
lhci collect --url=$URL --output=json --collect.settings.chromeFlags="--no-sandbox --headless --disable-gpu --disable-dev-shm-usage" --numberOfRuns=1 


jq -c 'del (.audits."screenshot-thumbnails") | {"ts": (now | strflocaltime("%s")), "url": .finalUrl, "lighthouseScore": (.categories.performance.score * 100.), "first-meaningful-paint": .audits."first-meaningful-paint", "total-byte-weight": .audits."total-byte-weight", "resource-summary": .audits."resource-summary", "accessibility": .categories.accessibility.score, "final-screenshot": .finalScreenshot, "rawResult": . }' /app/.lighthouseci/lhr-*.json > lighthouse.json

./venv/bin/python analyze_url.py "$URL" -o bootstrap.json

jq -c -s '.[0] * .[1]' lighthouse.json bootstrap.json > /app/results/$OUTPUT_FILE

# Check if the report was moved successfully
if [ ! -f /app/results/$OUTPUT_FILE ]; then
  echo "LHCI report was not generated."
  exit 1
fi

# Print a message indicating success
echo "LHCI report generated at /app/results/$OUTPUT_FILE"

