import certifi
import os
import sys
import subprocess
import requests
import datetime
import OpenSSL

if __name__ == '__main__':
    def check_cert(filename):
        """Checks local cert expire date"""
        with open(filename, "r") as f:
            cert = f.read()

        cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)

        expires = datetime.datetime.strptime(str(cert.get_notAfter().decode("utf-8")), '%Y%m%d%H%M%SZ')
        days = (expires - datetime.datetime.now()).days
        print("Local cert chain expires on: " + str(expires))
        print("Days to expiration: " + str(days))
    
    try:
        requests.get('https://jira.cis.unimelb.edu.au:8444/')
        print('Using local cert chain')
        check_cert('chain.pem')
        print('Connection to Jira OK.') 
    except requests.exceptions.SSLError as e:
        print('Jira intermediate cert missing')
        print('Adding local cert chain to Certifi store...')
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

