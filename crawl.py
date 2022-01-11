import argparse
import yaml
import pandas as pd
import os
import json
import subprocess
from datetime import datetime
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
                }
                print(res)
                f.seek(0)
                f.truncate(0)
                json.dump(res, f)
            except KeyError:
                print("Error carbonRes", carbonRes)


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

    tp = ThreadPool(None)
    for idx, comune in comuniList.iterrows():
        tp.apply_async(crawlComune, (comune, outputDir,cfg))
        # crawlComune(comune)

    tp.close()
    tp.join()


if __name__ == "__main__":
    main()
