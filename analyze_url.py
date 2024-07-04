import subprocess
import json
import re
import requests
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By

from xvfbwrapper import Xvfb

logging.basicConfig(level=logging.INFO)


def carbonResults(url):
    try:
        url = url.replace(r"http://", "").replace(r"https://", "")
        url = "https://" + url
        logging.info(url)
        res = subprocess.run(["node", "carbon.js", url], capture_output=True, text=True)

        ret = json.loads(res.stdout)
        ret["url"] = url
        return ret
    except (subprocess.SubprocessError, json.JSONDecodeError, AttributeError):
        try:
            url = url.replace(r"http://", "").replace(r"https://", "")
            url = "http://" + url
            logging.info(url)
            res = subprocess.run(
                ["node", "carbon.js", url], capture_output=True, text=True
            )

            ret = json.loads(res.stdout)
            ret["url"] = url
            return ret
        except (subprocess.SubprocessError, json.JSONDecodeError, AttributeError):
            logging.error("Error {}".format(url))
            return {"lighthouse": "Error", "score": 0, "url": url}


def checkBootstrap(url):
    try:
        url = url.replace(r"http://", "").replace(r"https://", "")
        url = "https://" + url
        logging.info(url)
        res = subprocess.run(
            ["node", "checkBootstrap.js", url], capture_output=True, text=True
        )

        ret = json.loads(res.stdout)
        ret["url"] = url
    except (subprocess.SubprocessError, json.JSONDecodeError, AttributeError) as e:
        logging.debug("stdout {}".format(res.stdout))
        logging.debug(e)
        try:
            url = url.replace(r"http://", "").replace(r"https://", "")
            url = "http://" + url
            logging.info(url)
            res = subprocess.run(
                ["node", "checkBootstrap.js", url], capture_output=True, text=True
            )
            ret = json.loads(res.stdout)
            ret["url"] = url
        except (subprocess.SubprocessError, json.JSONDecodeError, AttributeError) as e:
            logging.debug(e)
            logging.debug("stdout {}".format(res.stdout))
            logging.error("Error {}".format(url))
            return {"bootstrap": "Error", "url": url}

    bootstrapGen = False
    bootstrapItalia = False
    for (k, e) in ret.items():
        if re.match(r".*(js|css)$", k, re.IGNORECASE):
            logging.debug("key {} matches".format(k))
            if re.match(
                r".*bootstrap.{0,16}italia.*", "{}".format(k), re.IGNORECASE
            ) or re.match(r".*bootstrap.{0,16}italia.*", "{}".format(e), re.IGNORECASE):
                bootstrapItalia = True

            if re.match(r".*bootstrap.*", "{}".format(k), re.IGNORECASE) or re.match(
                r".*bootstrap.*", "{}".format(e), re.IGNORECASE
            ):
                bootstrapGen = True

    ret = {"bootstrap": bootstrapGen, "bootstrapItalia": bootstrapItalia}
    return ret

BI_patterns={
        "bootstrapItalia": r"bootstrap.{0,16}italia",
        "boostrap": r"bootstrap"
}

# Function to fetch and search content
def fetch_and_search(url, patterns):
    logging.debug("fetch_and_search {}".format(url))
    ret={}

    try:
        response = requests.get(url)
        content = response.text
        for pat_name,pattern in patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                ret[pat_name]=True
                logging.debug(f"Pattern '{pattern}' found in {url}")
    except requests.RequestException as e:
        logging.debug(f"Failed to fetch {url}: {e}")

    return ret

def checkBootstrap2(url):
    logging.info("checkBootstrap2 {}".format(url))
    ret={}
    with Xvfb() as xvfb:
        webdrv = webdriver.Firefox()
        try:
            url = url.replace(r"http://", "").replace(r"https://", "")
            url = "https://" + url
            logging.info("checkBootstrap2 {}".format(url))

            webdrv.get(url)
            ret["url"] = url
            ret["bootstrapItaliaVariable"]=webdrv.execute_script('return window.BOOTSTRAP_ITALIA_VERSION;')
            ret["bootstrapItaliaMethod"]=webdrv.execute_script('return getComputedStyle(document.body).getPropertyValue("--bootstrap-italia-version");')

            js_files = webdrv.find_elements(By.XPATH, "//script[@src]")
            css_files = webdrv.find_elements(By.XPATH, "//link[@rel='stylesheet'][@href]")

            # Extract the URLs
            js_urls = [js.get_attribute('src') for js in js_files]
            css_urls = [css.get_attribute('href') for css in css_files]

            logging.debug("js_urls {}".format(js_urls))
            logging.debug("css_urls {}".format(css_urls))

            # Search patterns in JS files
            for url in js_urls:
                ret.update(fetch_and_search(url, BI_patterns))

            # Search patterns in CSS files
            for url in css_urls:
                ret.update(fetch_and_search(url, BI_patterns))


        except Exception as e:
            logging.debug(e)
            try:
                url = url.replace(r"http://", "").replace(r"https://", "")
                url = "http://" + url
                logging.info("checkBootstrap2 {}".format(url))
                webdrv.get(url)
                ret["url"] = url
                ret["bootstrapItaliaVariable"]=webdrv.execute_script('return window.BOOTSTRAP_ITALIA_VERSION;')
                ret["bootstrapItaliaMethod"]=webdrv.execute_script('return getComputedStyle(document.body).getPropertyValue("--bootstrap-italia-version");')

                js_files = webdrv.find_elements(By.XPATH, "//script[@src]")
                css_files = webdrv.find_elements(By.XPATH, "//link[@rel='stylesheet'][@href]")

                # Extract the URLs
                js_urls = [js.get_attribute('src') for js in js_files]
                css_urls = [css.get_attribute('href') for css in css_files]

                logging.debug("js_urls {}".format(js_urls))
                logging.debug("css_urls {}".format(css_urls))

                # Search patterns in JS files
                for url in js_urls:
                    ret.update(fetch_and_search(url, BI_patterns))

                # Search patterns in CSS files
                for url in css_urls:
                    ret.update(fetch_and_search(url, BI_patterns))

            except Exception as e:
                logging.debug(e)
                ret["url"] = url
                ret["bootstrapItaliaVariable"]=None
                ret["bootstrapItaliaMethod"]=None
                ret["bootstrapItalia"]=None
                ret["bootstrap"]=None
        webdrv.quit()


    return ret

def analyze_url(url):
    carbonRes = carbonResults(url)

    # remove useless screenshots
    if "rawResult" in carbonRes:
        del carbonRes["rawResult"]["audits"]["screenshot-thumbnails"]
        #del carbonRes["rawResult"]["audits"]["final-screenshot"]
        #del carbonRes["rawResult"]["audits"]["full-page-screenshot"]

    res = None

    try:
        res = {
            "url": carbonRes["url"],
            "lighthouseScore": carbonRes["score"],
            "first-meaningful-paint": carbonRes["rawResult"]["audits"]["first-meaningful-paint"],
            "total-byte-weight": carbonRes["rawResult"]["audits"]["total-byte-weight"],
            "resource-summary": carbonRes["rawResult"]["audits"]["resource-summary"],
            "accessibility": carbonRes["rawResult"]["categories"]["accessibility"]["score"],
            "final-screenshot": carbonRes["rawResult"]["audits"]["final-screenshot"],
            "full-page-screenshot": carbonRes["rawResult"]["audits"]["full-page-screenshot"],
#            "lighthouseRawResult": carbonRes["rawResult"],
        }
    except Exception as e:
        logging.error("Error {}".format(e))

    #bootstrapRes = checkBootstrap(url)
    #res["bootstrapItalia"] = bootstrapRes
    bootstrapRes2 = checkBootstrap2(url)
    res["bootstrapItalia"] = bootstrapRes2

    return res

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze a single URL.")
    parser.add_argument("url", type=str, help="URL to analyze")
    parser.add_argument("-o", "--output", type=str, help="Output file", default=None)
    args = parser.parse_args()

    result = analyze_url(args.url)
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))


