const fs = require('fs');
const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const url = process.argv[2];

(async () => {
  const chrome = await chromeLauncher.launch({chromeFlags: ['--headless','--nosandbox']});
  //const options = {logLevel: 'info', output: 'html', onlyCategories: ['performance'], port: chrome.port};
  const options = {logLevel: 'info', output: 'html', port: chrome.port};
  const runnerResult = await lighthouse(url, options);

  // `.report` is the HTML report as a string
  //const reportHtml = runnerResult.report;
  //fs.writeFileSync('lhreport.html', reportHtml);

  // `.lhr` is the Lighthouse Result as a JS object
  //console.log('Report is done for', runnerResult.lhr.finalUrl);
  //console.log('Performance score was', runnerResult.lhr.categories.performance.score * 100);
  
  result={"url":runnerResult.lhr.finalUrl,"score":runnerResult.lhr.categories.performance.score * 100., "rawResult": runnerResult.lhr};

  console.log(JSON.stringify(result));

  await chrome.kill();
})();
