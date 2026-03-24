import requests
import json
from django.conf import settings

def send_push_notification(title, message, url="https://alagme.com"):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Basic {settings.ONESIGNAL_API_KEY}"
    }

    payload = {
        "app_id": settings.ONESIGNAL_APP_ID,
        "included_segments": ["All"],  # جميع المشتركين
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