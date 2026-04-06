import requests

def send_indexnow(url):
    data = {
        "host": "alagme.com",
        "key": "800e60e37753412893002525b148ce17",
        "keyLocation": "https://alagme.com/800e60e37753412893002525b148ce17.txt",
        "urlList": [url]
    }

    requests.post("https://api.indexnow.org/indexnow", json=data)