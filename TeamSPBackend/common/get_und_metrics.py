import json
import sys
import os

# using Understand for analyze Metrics
# For Linux Server
UND_PATH = '~/comp90082sp/understand/scitools/bin/linux64/'
sys.path.append(UND_PATH)
sys.path.append(UND_PATH+'Python')
import understand

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UND_FILE_PATH = os.path.dirname(BASE_DIR)  # '/home/ec2-user/comp90082sp/COMP90082_Software_Project_Database_Backend/'
METRICS_FILE_PATH = BASE_DIR + '/resource/understand/'

if __name__ == '__main__':
    und_file_name = sys.argv[1]
    metrics_file_name = sys.argv[2]
    und_file = UND_FILE_PATH + und_file_name
    metrics_file = METRICS_FILE_PATH + metrics_file_name
    # print('BASE_DIR : ', BASE_DIR)
    # print('und_file : ', und_file)
    # print('metrics_file : ', metrics_file)
    # open a project und
    udb = understand.open(und_file)
    # get all project metrics
    metrics = udb.metric(udb.metrics())
    # write the metrics result to metrics_file (.json)
    with open(metrics_file, 'w') as fp:
        json.dump(metrics, fp, indent=4)
