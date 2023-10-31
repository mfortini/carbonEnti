import argparse
import yaml
import pandas as pd
import os
import json
import subprocess
from datetime import datetime
import re
import logging
from multiprocessing.pool import ThreadPool

logging.basicConfig(level=logging.DEBUG)


def usage():
    print("Usage")
    print("crawl -c config.yaml")


def parseArguments():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("-c", "--config", type=str, help="config file")

    args = parser.parse_args()

    return args


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


def crawlComune(comune, outputDir, cfg):
    logging.info("crawlComune {}".format(comune["Denominazione_ente"]))
    tsNow = datetime.now().timestamp()
    codiceIPA = comune["Codice_IPA"]
    rerun = True
    with open(os.path.join(outputDir, codiceIPA + ".json"), "a+") as f:
        try:
            f.seek(0)
            existData = json.load(f)
            ts = existData["ts"]
            logging.info(
                "tsNow {} ts {} diff {} TTL {}".format(
                    tsNow, ts, tsNow - ts, cfg["TTL"]
                )
            )
            if (tsNow - ts) < cfg["TTL"]:
                rerun = False
        except json.JSONDecodeError:
            logging.warning("Cannot decode JSON")
            pass

        if rerun:
            carbonRes = carbonResults(comune["Sito_istituzionale"])

            del carbonRes["rawResult"]["audits"]["screenshot-thumbnails"]
            del carbonRes["rawResult"]["audits"]["final-screenshot"]
            del carbonRes["rawResult"]["audits"]["full-page-screenshot"]

            res = None

            try:
                res = {
                    "Codice_IPA": codiceIPA,
                    "ts": tsNow,
                    "url": carbonRes["url"],
                    "lighthouseScore": carbonRes["score"],
                    "first-meaningful-paint": carbonRes["rawResult"]["audits"][
                        "first-meaningful-paint"
                    ],
                    "total-byte-weight": carbonRes["rawResult"]["audits"][
                        "total-byte-weight"
                    ],
                    "resource-summary": carbonRes["rawResult"]["audits"][
                        "resource-summary"
                    ],
                    "accessibility": carbonRes["rawResult"]["categories"]["accessibility"]["score"],
                    "lighthouseRawResult": carbonRes["rawResult"],
                }
            except KeyError:
                print("Error carbonRes", carbonRes)

            bootstrapRes = checkBootstrap(comune["Sito_istituzionale"])

            res["bootstrapItalia"] = bootstrapRes

            if res is not None:
                print(res)
                f.seek(0)
                f.truncate(0)
                json.dump(res, f)


def main():
    args = parseArguments()

    with open(args.config, "r") as f:
        cfg = yaml.safe_load(f)

    logging.info(cfg)

    crawlList = pd.read_csv(cfg["list"])

    comuniList = crawlList[crawlList["Codice_natura"] == 2430]

    outputDir = cfg["outputDir"]

    try:
        os.mkdir(outputDir)
    except OSError:
        pass

    tp = ThreadPool()
    for idx, comune in comuniList.iterrows():
        tp.apply_async(crawlComune, (comune, outputDir, cfg))
        #crawlComune(comune, outputDir, cfg)

    tp.close()
    tp.join()


if __name__ == "__main__":
    main()
