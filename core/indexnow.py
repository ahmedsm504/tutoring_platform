import requests

def send_indexnow(url):
    data = {
        "host": "alagme.com",
        "key": "b52bd4ea55c149459d7c6e1f2ca39c98",
        "keyLocation": "https://alagme.com/b52bd4ea55c149459d7c6e1f2ca39c98.txt",
        "urlList": [url]
    }

    requests.post("https://api.indexnow.org/indexnow", json=data)