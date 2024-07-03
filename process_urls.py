import argparse
import yaml
import pandas as pd
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from multiprocessing.pool import ThreadPool
from subprocess import run

logging.basicConfig(level=logging.DEBUG)

def usage():
    print("Usage")
    print("crawl -c config.yaml")

def parseArguments():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("-c", "--config", type=str, help="config file")

    args = parser.parse_args()

    return args

def crawlEnte(ente, outputDir, cfg):
    logging.info("crawlEnte {}".format(ente["Denominazione_ente"]))
    tsNow = datetime.now().timestamp()
    codiceIPA = ente["Codice_IPA"]
    rerun = True
    output_file = os.path.join(outputDir, codiceIPA + ".json")
    with open(output_file, "a+") as f:
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
            url = ente["Sito_istituzionale"]
            result_file = os.path.join(outputDir, f"{codiceIPA}_result.json")
            run(["python3", "analyze_url.py", url, "-o", result_file])

            with open(result_file, "r") as rf:
                res = json.load(rf)
                res["Codice_IPA"] = codiceIPA
                res["ts"] = tsNow

            Path(result_file).unlink(missing_ok=True)

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

    entiList = crawlList[crawlList["Codice_natura"] == 2430]

    # Randomize list
    entiList = entiList.sample(frac=1).reset_index(drop=True)

    outputDir = cfg["outputDir"]

    try:
        os.mkdir(outputDir)
    except OSError:
        pass

    tp = ThreadPool()
    for idx, ente in entiList.iterrows():
        tp.apply_async(crawlEnte, (ente, outputDir, cfg))

    tp.close()
    tp.join()

if __name__ == "__main__":
    main()

