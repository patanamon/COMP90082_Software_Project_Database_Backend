import requests
import json

s = requests.Session()

def login():
    url = 'http://127.0.0.1:8000/api/v1/account/login'
    data = {'username':'admin', 'password':'admin'}
    res = s.post(url=url, json = data)
    print(json.loads(res.text))

login()

