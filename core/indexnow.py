import logging

import requests

logger = logging.getLogger(__name__)


def send_indexnow(url):
    """يبلّغ IndexNow بالرابط. مابيرميش أي خطأ (مش لازم الزائر/الأدمن يتأثر لو IndexNow وقع)
    وفيه timeout عشان الطلب ماعلّقش الـ worker."""
    data = {
        "host": "alagme.com",
        "key": "800e60e37753412893002525b148ce17",
        "keyLocation": "https://alagme.com/800e60e37753412893002525b148ce17.txt",
        "urlList": [url]
    }
    try:
        response = requests.post("https://api.indexnow.org/indexnow", json=data, timeout=5)
        if response.status_code not in (200, 202):
            logger.warning("IndexNow رجّع %s للرابط %s", response.status_code, url)
            return False
        return True
    except requests.RequestException:
        logger.exception("فشل إرسال IndexNow للرابط %s", url)
        return False
