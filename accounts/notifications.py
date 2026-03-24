import requests
import json

ONESIGNAL_APP_ID = "7cf73c03-afd6-43ff-af0f-856b49862d15"
ONESIGNAL_API_KEY = "os_v2_app_pt3tya5p2zb77lypqvvutbrncuc7xhs3wyxeac4rjwyplhngrzlvh7dxrxfoq5v4xxygtdqfaaph7rxmjxlqnvj4vhf44p55fk3hgka"

def send_push_notification(title, message, url="https://alagme.com"):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Basic {ONESIGNAL_API_KEY}"
    }

    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["All"],
        "headings": {"ar": title, "en": title},
        "contents": {"ar": message, "en": message},
        "url": url
    }

    try:
        response = requests.post(
            "https://api.onesignal.com/notifications",
            headers=headers,
            data=json.dumps(payload)
        )
        return response.json()
    except Exception as e:
        print(f"OneSignal Error: {e}")
        return None

# تجربة الإرسال
result = send_push_notification("تجربة", "رسالة تجربة")
print(result)