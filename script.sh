#!/bin/bash

CODICE_IPA=$1
SITO_ISTITUZIONALE=$2
RESULTS_DIR=$3
OUTPUT_FILE=$4

# Run the Docker command
docker run --cap-add=SYS_ADMIN --rm -v "$(pwd)/$RESULTS_DIR":/app/results lhci-node "$SITO_ISTITUZIONALE" "$OUTPUT_FILE"

# Check if the output file was created
if [ ! -f "$RESULTS_DIR/$OUTPUT_FILE" ]; then
  echo "Error: LHCI report was not generated for $CODICE_IPA."
  exit 1
fi

# Print a message indicating success
echo "Final JSON report created for $CODICE_IPA at $RESULTS_DIR/${CODICE_IPA}.json"

