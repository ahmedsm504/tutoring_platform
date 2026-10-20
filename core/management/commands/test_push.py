"""يتأكد إن إشعارات Firebase شغالة: بيطبع الحالة وعدد المشتركين، ويبعت إشعار تجريبي للأدمن.

تشغيل:  python manage.py test_push            (للأدمن بس)
        python manage.py test_push --everyone (لكل المشتركين)
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Check Firebase push setup and send a test notification'

    def add_arguments(self, parser):
        parser.add_argument('--everyone', action='store_true')

    def handle(self, *args, **opts):
        from accounts.models import FCMToken
        from accounts.notifications import _send, is_configured
        total = FCMToken.objects.count()
        admins = FCMToken.objects.filter(is_admin=True).count()
        self.stdout.write(f'Subscribed browsers: {total} (admins: {admins})')
        if not is_configured():
            self.stdout.write(self.style.ERROR('Firebase NOT configured: set FIREBASE_CREDENTIALS_JSON on the server.'))
            return
        qs = FCMToken.objects.all() if opts['everyone'] else FCMToken.objects.filter(is_admin=True)
        tokens = list(qs.values_list('token', flat=True))
        if not tokens:
            self.stdout.write(self.style.WARNING('No tokens to send to. Enable notifications from the site footer first.'))
            return
        res = _send(tokens, '🔔 إشعار تجريبي', 'إشعارات موقع العجمي شغالة', '/')
        ok = sum(r.success_count for _, r in (res or []))
        self.stdout.write(self.style.SUCCESS(f'Sent: {ok}/{len(tokens)}'))
