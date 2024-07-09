#! /bin/bash

docker run --rm --name lighthouse -it -v /path/to/your/report:/home/chrome/reports --cap-add=SYS_ADMIN femtopixel/google-lighthouse:v12.0.0 $1 --quiet --output=json --chrome-flags="--headless --disable-gpu --disable-dev-shm-usage" \
	| jq -c '{"url": .finalUrl, "score": (.categories.performance.score * 100.), "rawResult": . }' -
