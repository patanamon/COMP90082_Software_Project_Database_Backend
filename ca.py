import certifi
import os
import sys
import ctypes
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
        print("WARNING: Please update server cert chain scheme, local cert chain is just a temporary mitigation")
        
        
    def update_ca():
        """Updates CA with provided chain.pem"""
        cafile = certifi.where()
        with open('chain.pem', 'rb') as infile:
            customca = infile.read()     
        with open(cafile, 'ab') as outfile:
            outfile.write(customca)
        check_cert('chain.pem')
            
    def is_admin():
        """Check admin in windows"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False        
            

    print('Adding local cert chain to Certifi store...')
    if os.name == 'nt':  # for win
        if is_admin():
            update_ca()
        else:
            print("Please run this script with Administrator")
    else:  # for unix
        if os.geteuid() == 0:
            update_ca()
        else:
            print("Please run this script with sudo")
            subprocess.call(['sudo', 'python', *sys.argv])
            sys.exit()

