"""IndexNow: بنبلّغ Bing وYandex وSeznam وNaver (ومنهم محركات زي DuckDuckGo وYahoo وبحث ChatGPT
اللي بتعتمد على Bing) بأي صفحة جديدة أو متعدّلة، فبتتفهرس خلال ساعات بدل أسابيع."""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)
ENDPOINT = "https://api.indexnow.org/indexnow"


def _payload(urls):
    host = getattr(settings, 'CANONICAL_HOST', 'alagme.com')
    key = getattr(settings, 'INDEXNOW_KEY', '800e60e37753412893002525b148ce17')
    return {"host": host, "key": key, "keyLocation": f"https://{host}/{key}.txt", "urlList": list(urls)}


def send_indexnow_batch(urls, timeout=15):
    """بيبعت لحد 10000 رابط في طلب واحد. بيرجع True لو اتقبلت. مابيرميش أخطاء."""
    urls = [u for u in urls if u]
    if not urls:
        return True
    ok = True
    for i in range(0, len(urls), 10000):
        try:
            r = requests.post(ENDPOINT, json=_payload(urls[i:i + 10000]), timeout=timeout)
            if r.status_code not in (200, 202):
                logger.warning("IndexNow رجّع %s (%s رابط)", r.status_code, len(urls[i:i + 10000]))
                ok = False
        except requests.RequestException:
            logger.exception("فشل إرسال IndexNow")
            ok = False
    return ok


def send_indexnow(url):
    """رابط واحد (بيستخدمه الأدمن لما ينشر مقال أو يعتمد سؤال)"""
    if settings.DEBUG:
        return False
    return send_indexnow_batch([url], timeout=5)
