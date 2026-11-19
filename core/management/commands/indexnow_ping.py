"""يبلّغ IndexNow بكل الصفحات الجديدة أو المتعدّلة اللي في السايت ماب.
بيشتغل تلقائيًا مع كل نشر (من الـ Procfile)، وبيبلّغ بس باللي اتغير من آخر مرة.

  python manage.py indexnow_ping            # الجديد والمتعدّل بس
  python manage.py indexnow_ping --all      # كل الروابط تاني
  python manage.py indexnow_ping --dry-run  # يعرض الروابط من غير ما يبعت
  python manage.py indexnow_ping --refresh  # + دفعة من الروابط اللي بقالها REFRESH_DAYS ما اتبلّغتش
                                            (بيشغله core/indexnow_scheduler.py تلقائي كل 3 ساعات)
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone


REFRESH_DAYS = 21
REFRESH_BATCH = 300


class Command(BaseCommand):
    help = 'تبليغ محركات البحث (IndexNow) بالصفحات الجديدة والمتعدلة'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--refresh', action='store_true')
        parser.add_argument('--force', action='store_true', help='يشتغل حتى لو DEBUG=True')

    def handle(self, *args, **opts):
        try:
            self._run(opts)
        except Exception as e:  # مايوقعش النشر أبدًا
            self.stderr.write(f'IndexNow: تخطّي ({e})')

    def _run(self, opts):
        if settings.DEBUG and not (opts['force'] or opts['dry_run']):
            self.stdout.write('IndexNow: DEBUG=True، مش هيبعت (استخدم --force)')
            return
        from config.urls import sitemaps
        from core.indexnow import send_indexnow_batch
        from core.models import IndexNowPing

        base = getattr(settings, 'CANONICAL_URL', 'https://alagme.com').rstrip('/')
        found = {}
        for cls in sitemaps.values():
            sm = cls() if isinstance(cls, type) else cls
            for item in sm.items():
                loc = sm.location(item) if hasattr(sm, 'location') else item.get_absolute_url()
                lastmod = None
                if hasattr(sm, 'lastmod'):
                    try:
                        lastmod = sm.lastmod(item) if callable(sm.lastmod) else sm.lastmod
                    except Exception:
                        lastmod = None
                found[base + loc] = lastmod

        done = {p.url: p.pinged_at for p in IndexNowPing.objects.filter(url__in=list(found))}
        todo = []
        for url, lastmod in found.items():
            if opts['all'] or url not in done:
                todo.append(url)
            elif lastmod and hasattr(lastmod, 'tzinfo') and lastmod > done[url]:
                todo.append(url)
        if opts['refresh'] and not opts['all']:
            # الروابط اللي بقالها مدة ما اتبلّغتش (الأقدم الأول) - بكميات صغيرة عشان Bing مايعتبرهاش سبام
            from datetime import timedelta
            cutoff = timezone.now() - timedelta(days=REFRESH_DAYS)
            stale = sorted((d, u) for u, d in done.items() if d < cutoff and u not in todo)
            todo += [u for _, u in stale[:REFRESH_BATCH]]

        self.stdout.write(f'IndexNow: {len(todo)} رابط جديد/متعدّل من {len(found)}')
        if opts['dry_run'] or not todo:
            for u in todo[:50]:
                self.stdout.write('  ' + u)
            return
        if send_indexnow_batch(todo):
            now = timezone.now()
            for u in todo:
                IndexNowPing.objects.update_or_create(url=u, defaults={'pinged_at': now})
            self.stdout.write(self.style.SUCCESS(f'IndexNow: اتبعت {len(todo)} رابط'))
