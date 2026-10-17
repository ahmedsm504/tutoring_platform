"""محاكاة رسالة واردة من واتساب (للتجربة المحلية من غير Meta):

    python manage.py chat_simulate_inbound 201012345678 "السلام عليكم يا أستاذة"
"""
import time
import uuid

from django.core.management.base import BaseCommand

from chat.services import process_webhook


class Command(BaseCommand):
    help = 'محاكاة رسالة واتساب واردة على رقم المنصة'

    def add_arguments(self, parser):
        parser.add_argument('phone')
        parser.add_argument('text')
        parser.add_argument('--name', default='')

    def handle(self, phone, text, name='', **opts):
        payload = {'object': 'whatsapp_business_account', 'entry': [{'changes': [{'field': 'messages', 'value': {
            'messaging_product': 'whatsapp',
            'contacts': [{'wa_id': phone, 'profile': {'name': name}}],
            'messages': [{'from': phone, 'id': f'wamid.SIM{uuid.uuid4().hex}', 'timestamp': str(int(time.time())),
                          'type': 'text', 'text': {'body': text}}],
        }}]}]}
        process_webhook(payload)
        self.stdout.write(self.style.SUCCESS('تم استقبال الرسالة - افتحي /chat/admin/'))
