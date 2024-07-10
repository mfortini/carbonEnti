# Use an official Node runtime as a parent image
FROM node:21


# Install dependencies
RUN apt-get update && apt-get install -y wget gnupg
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get update && apt-get install -y google-chrome-stable jq python3-venv xvfb

# Set the CHROME_PATH environment variable
ENV CHROME_PATH=/usr/bin/google-chrome


# Set the working directory
WORKDIR /app

# Copy the package.json and package-lock.json files
#COPY package*.json ./

# Install dependencies
#RUN npm install

RUN python3 -mvenv venv
RUN venv/bin/pip install selenium geckodriver requests xvfbwrapper

# Install Lighthouse CI
RUN npm install -g @lhci/cli

# If you have a configuration file for LHCI, copy it into the container
#COPY .lighthouserc.js ./
COPY analyze_url.py /app/analyze_url.py

# Copy the entrypoint script into the container
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Make a directory for the results
RUN mkdir /app/results

# Define the command to run LHCI collect and save the results as JSON

# Set the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]


