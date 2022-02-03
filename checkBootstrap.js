'use strict';
const url = process.argv[2];

const puppeteer = require('puppeteer');
const request_client = require('request-promise-native');

(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    const result = {};

    await page.setRequestInterception(true);

    page.on('request', request => {
        request_client({
            uri: request.url(),
            resolveWithFullResponse: true,
        }).then(response => {
            const request_url = request.url();
            const request_headers = request.headers();
            const request_post_data = request.postData();
            const response_headers = response.headers;
            const response_size = response_headers['content-length'];
            const response_body = response.body;

            if (response_headers['content-type'].match('application/javascript') || response_headers['content-type'].match('text/css')) {
                result[request_url]={
                    "request_headers":request_headers,
                    "request_post_data":request_post_data,
                    "response_headers":response_headers,
                    "response_size":response_size,
                    "response_body":response_body,
                }
            } else {
            }


            request.continue();
        }).catch(error => {
            console.error(error);
            request.abort();
        });
    });

    await page.goto(url, {
        waitUntil: 'networkidle0',
    });

    console.log(JSON.stringify(result));
    await browser.close();
})();
