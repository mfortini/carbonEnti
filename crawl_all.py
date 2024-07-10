import csv
import os
import json
import subprocess
from datetime import datetime
import random
from concurrent.futures import ProcessPoolExecutor, as_completed

CSV_FILE = 'enti.csv'
RESULTS_DIR = 'entiRes2'
TIME_THRESHOLD = 864000  # 10 days in seconds
MAX_WORKERS = 2  # Number of parallel processes

def get_current_timestamp():
    return int(datetime.now().timestamp())

def process_csv(file_path):
    tasks = []
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            codice_ipa = row['Codice_IPA']
            sito_istituzionale = row['Sito_istituzionale']
            if not sito_istituzionale.startswith(('http://', 'https://')):
                sito_istituzionale = 'https://' + sito_istituzionale
            tasks.append((codice_ipa, sito_istituzionale))
    return tasks

def process_codice_ipa(task):
    rerun=True
    codice_ipa, sito_istituzionale = task
    json_file_path = os.path.join(RESULTS_DIR, f"{codice_ipa}.json")
    if os.path.isfile(json_file_path):
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            if 'ts' in data:
                ts = data['ts']
                current_ts = get_current_timestamp()
                if (current_ts - ts) < TIME_THRESHOLD:
                    rerun= False
            else:
                print(f"No 'ts' attribute found in {json_file_path}.")
    else:
        print(f"No file found for {codice_ipa}.")
    if rerun:
        call_external_script(codice_ipa, sito_istituzionale)

def call_external_script(codice_ipa, sito_istituzionale):
    output_file = f"{codice_ipa}.json"
    try:
        subprocess.run(['./script.sh', codice_ipa, sito_istituzionale, RESULTS_DIR, output_file], check=True)
        print(f"Script executed for {codice_ipa}, results saved to {output_file}.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing script for {codice_ipa}: {e}")

if __name__ == "__main__":
    tasks = process_csv(CSV_FILE)
    random.shuffle(tasks)
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_codice_ipa, task) for task in tasks]
        for future in as_completed(futures):
            future.result()  # To raise exceptions if any

