import json
import os
import argparse
from collections import defaultdict

parser = argparse.ArgumentParser(description="MQTT JSON Parser to find differences in values among like mq messages for every key")
parser.add_argument('dirpath', type=str, help="The full path to the location with all the messages you wish to compare and get the different reported values.")
args = parser.parse_args()

#ignore_keys = ['ams', 'temper', 'speed', 'fan_gear', 'gcode_start_time', 'mc_remaining_time', 'gcode_file_prepare_percent', 'mc_percent', 'sequence_id']  # keys to ignore
ignore_keys = []
pdata = defaultdict(set)  # store unique values for each key

def extract_values(d, parent_key=""):
    if isinstance(d, dict):
        for k, v in d.items():
            key = parent_key + k if parent_key else k
            if isinstance(v, (dict, int)):
                extract_values(v, key + ".")
            elif isinstance(v, list):
                for item in v:
                    extract_values(item, key + ".")
            elif k not in ignore_keys:
                pdata[key].add(v)
    elif isinstance(d, int) and parent_key not in ignore_keys:
        pdata[parent_key].add(d)

# Directory containing the JSON files
dir_path = args.dirpath

# Loop through all JSON files in the directory
for filename in os.listdir(dir_path):
    if filename.endswith(".json"):
        with open(os.path.join(dir_path, filename)) as f:
            file_data = json.load(f)
            extract_values(file_data)

# Convert the values from sets to lists
pdata = {k: list(v) for k, v in pdata.items()}

dkeys = []
for k in pdata.keys():
    for ex in ignore_keys:
        if ex in k:
            dkeys.append(k)

for dk in dkeys:
    pdata.pop(dk, None)

# Output the unique values for each key to a file
with open(dir_path + "_differences.json", "w") as f:
    json.dump(dict(pdata), f, indent=4)

file_count = len(os.listdir(dir_path))
print('Processed ', str(file_count), ' files in ', dir_path)