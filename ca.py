import certifi
import os
import sys
import subprocess
    
if os.geteuid() == 0:
    cafile = certifi.where()
    with open('chain.pem', 'rb') as infile:
        customca = infile.read()
    with open(cafile, 'ab') as outfile:
        outfile.write(customca)
else:
    print("Please run this script with sudo")
    subprocess.call(['sudo', 'python', *sys.argv])
    sys.exit()
