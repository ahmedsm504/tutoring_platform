"""عميل بسيط لـ WhatsApp Cloud API (Meta).

الإعدادات (متغيرات بيئة - شوفي settings.py):
  WHATSAPP_TOKEN            توكن دائم (System User) من Meta Business
  WHATSAPP_PHONE_NUMBER_ID  معرّف رقم المنصة في WhatsApp Manager
  WHATSAPP_APP_SECRET       App Secret للتحقق من توقيع الـ webhook
  WHATSAPP_VERIFY_TOKEN     كلمة سر بتكتبيها إنتِ في إعدادات الـ webhook عند Meta
  WHATSAPP_API_VERSION      افتراضيًا v23.0
"""
import hashlib
import hmac
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GRAPH = 'https://graph.facebook.com'
TIMEOUT = 15


class WhatsAppError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


def _cfg(name, default=''):
    return getattr(settings, name, default) or default


def is_configured():
    return bool(_cfg('WHATSAPP_TOKEN') and _cfg('WHATSAPP_PHONE_NUMBER_ID'))


def _base():
    return f"{GRAPH}/{_cfg('WHATSAPP_API_VERSION', 'v23.0')}"


def _headers():
    return {'Authorization': f"Bearer {_cfg('WHATSAPP_TOKEN')}"}


def verify_signature(raw_body, signature_header):
    """X-Hub-Signature-256: sha256=<hmac>"""
    secret = _cfg('WHATSAPP_APP_SECRET')
    if not secret or not signature_header or not signature_header.startswith('sha256='):
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header.split('=', 1)[1])


def _raise_for(resp):
    try:
        data = resp.json()
    except ValueError:
        data = {}
    if resp.status_code >= 400 or 'error' in data:
        err = data.get('error', {}) if isinstance(data, dict) else {}
        code = err.get('code')
        msg = err.get('message') or resp.text[:300]
        details = (err.get('error_data') or {}).get('details')
        if details:
            msg = f"{msg} - {details}"
        raise WhatsAppError(msg, code=code)
    return data


def _post_message(payload):
    if not is_configured():
        raise WhatsAppError('ربط واتساب (WhatsApp Cloud API) لسه مش متظبط في إعدادات السيرفر.')
    url = f"{_base()}/{_cfg('WHATSAPP_PHONE_NUMBER_ID')}/messages"
    body = {'messaging_product': 'whatsapp', 'recipient_type': 'individual'}
    body.update(payload)
    try:
        resp = requests.post(url, json=body, headers=_headers(), timeout=TIMEOUT)
    except requests.RequestException as e:
        raise WhatsAppError(f'تعذر الاتصال بواتساب: {e}')
    data = _raise_for(resp)
    try:
        return data['messages'][0]['id']
    except (KeyError, IndexError, TypeError):
        raise WhatsAppError(f'رد غير متوقع من واتساب: {data}')


def send_text(to, text):
    return _post_message({'to': to, 'type': 'text', 'text': {'preview_url': False, 'body': text[:4096]}})


def send_template(to, name, lang='ar', body_params=None):
    template = {'name': name, 'language': {'code': lang}}
    if body_params:
        template['components'] = [{
            'type': 'body',
            'parameters': [{'type': 'text', 'text': str(p)[:1000]} for p in body_params],
        }]
    return _post_message({'to': to, 'type': 'template', 'template': template})


def send_media(to, kind, media_id, caption='', filename=''):
    obj = {'id': media_id}
    if caption and kind in ('image', 'video', 'document'):
        obj['caption'] = caption[:1024]
    if filename and kind == 'document':
        obj['filename'] = filename[:240]
    return _post_message({'to': to, 'type': kind, kind: obj})


def upload_media(fileobj, mime, filename):
    if not is_configured():
        raise WhatsAppError('ربط واتساب لسه مش متظبط.')
    url = f"{_base()}/{_cfg('WHATSAPP_PHONE_NUMBER_ID')}/media"
    try:
        resp = requests.post(
            url, headers=_headers(), timeout=60,
            data={'messaging_product': 'whatsapp', 'type': mime},
            files={'file': (filename, fileobj, mime)},
        )
    except requests.RequestException as e:
        raise WhatsAppError(f'تعذر رفع الملف لواتساب: {e}')
    return _raise_for(resp)['id']


def download_media(media_id):
    """يرجّع (bytes, mime). روابط واتساب بتنتهي بعد دقايق، بس الـ media_id صالح ~30 يوم."""
    if not is_configured():
        raise WhatsAppError('ربط واتساب لسه مش متظبط.')
    try:
        meta = _raise_for(requests.get(f"{_base()}/{media_id}", headers=_headers(), timeout=TIMEOUT))
        resp = requests.get(meta['url'], headers=_headers(), timeout=60)
    except requests.RequestException as e:
        raise WhatsAppError(f'تعذر تحميل الملف من واتساب: {e}')
    if resp.status_code >= 400:
        raise WhatsAppError(f'تعذر تحميل الملف ({resp.status_code})')
    return resp.content, meta.get('mime_type') or resp.headers.get('Content-Type', 'application/octet-stream')


def mark_read(wa_message_id):
    """يعلّم رسالة ولي الأمر كمقروءة (علامتين زرق) - مش ضروري ومش بيرمي أخطاء"""
    if not is_configured() or not wa_message_id:
        return
    try:
        requests.post(
            f"{_base()}/{_cfg('WHATSAPP_PHONE_NUMBER_ID')}/messages",
            json={'messaging_product': 'whatsapp', 'status': 'read', 'message_id': wa_message_id},
            headers=_headers(), timeout=5,
        )
    except requests.RequestException:
        pass
