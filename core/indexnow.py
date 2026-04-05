import requests

def send_indexnow(url):
    data = {
        "host": "alagme.com",
        "key": "4de67fcf83f54455b2f2ac2911f398f2",
        "keyLocation": "https://alagme.com/4de67fcf83f54455b2f2ac2911f398f2.txt",
        "urlList": [url]
    }

    requests.post("https://api.indexnow.org/indexnow", json=data)