import argparse
import yaml
import pandas as pd
import os
import json
import subprocess
from datetime import datetime
import logging

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
        url.replace("http://", "").replace("https://", "")
        url = "https://" + url
        logging.info(url)
        res = subprocess.run(["node", "carbon.js", url], capture_output=True, text=True)

        return json.loads(res.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError, AttributeError):
        logging.error("Error", url)
        return {"lighthouse": "Error"}


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

    for idx, comune in comuniList.iterrows():
        tsNow = datetime.now().timestamp()
        codiceIPA = comune["Codice_IPA"]
        rerun = True
        with open(os.path.join(outputDir, codiceIPA + ".json"), "a+") as f:
            try:
                f.seek(0)
                existData = json.load(f)
                ts = existData["ts"]
                logging.info("tsNow {} ts {}".format(tsNow, ts))
                if tsNow - ts < cfg["TTL"]:
                    rerun = False
            except json.JSONDecodeError:
                logging.warning("Cannot decode JSON")
                pass
            f.seek(0)

            if rerun:
                carbonRes = carbonResults(comune["Sito_istituzionale"])

                res = {"Codice_IPA": codiceIPA, "ts": tsNow, "lighthouse": carbonRes}
                json.dump(res, f)


if __name__ == "__main__":
    main()
