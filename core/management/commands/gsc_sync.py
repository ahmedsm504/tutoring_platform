from django.core.management.base import BaseCommand

from core import gsc


class Command(BaseCommand):
    help = 'Google Search Console: إعادة إرسال السايت ماب + فحص حالة فهرسة الروابط + تقرير المشاكل (بيشتغل تلقائي يوميًا)'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None, help='أقصى عدد روابط تتفحص (الافتراضي 300)')
        parser.add_argument('--no-submit', action='store_true')
        parser.add_argument('--no-report', action='store_true')
        parser.add_argument('--check', action='store_true', help='اختبار الصلاحيات بس')

    def handle(self, *args, **o):
        try:
            if o['check']:
                gsc.submit_sitemap(gsc.session(), 'https://alagme.com/sitemap.xml')
                self.stdout.write(self.style.SUCCESS(f'تمام: {gsc.service_email()} عنده صلاحية على {gsc.SITE}'))
                return
            gsc.run(limit=o['limit'], submit=not o['no_submit'], report=not o['no_report'], stdout=self.stdout)
        except gsc.NotConfigured as e:
            self.stderr.write(f'GSC مش متظبط: {e}')
