"""إشعار واحد للمحتوى الجديد اللي اتضاف دفعة واحدة (مقالات أو أسئلة من الـ seed) بدل عشرات الإشعارات.

بيشتغل مع كل deploy (في الـ Procfile). المحتوى اللي اتبعت عنه إشعار قبل كده مبيتحسبش.
تشغيل يدوي:  python manage.py send_content_digest [--dry-run]
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Send one push notification summarising newly added posts/questions'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--days', type=int, default=3, help='Only content published in the last N days')

    def handle(self, *args, **opts):
        from accounts.notifications import is_configured, send_public_notification
        from blog.models import Post
        from qna.models import PublicQuestion

        since = timezone.now() - timedelta(days=opts['days'])
        posts = Post.objects.filter(status='published', push_sent_at__isnull=True, published_at__gte=since).order_by('-published_at')
        questions = PublicQuestion.objects.filter(status='approved', push_sent_at__isnull=True, created_at__gte=since,
                                                  official_answer__isnull=False).order_by('-created_at')
        n_posts, n_questions = posts.count(), questions.count()
        if not (n_posts or n_questions):
            self.stdout.write('No new content to announce.')
            return

        if n_posts == 1 and not n_questions:
            p = posts.first()
            title, message, url = '📖 مقال جديد في مدونة العجمي', p.title, f'/blog/{p.slug}/'
        elif n_questions == 1 and not n_posts:
            q = questions.first()
            title, message, url = '❓ سؤال جديد مُجاب', q.title, f'/questions/question/{q.slug}/'
        else:
            parts = []
            if n_posts:
                parts.append(f'{n_posts} مقال')
            if n_questions:
                parts.append(f'{n_questions} سؤال مُجاب')
            title = '📚 محتوى جديد في موقع العجمي'
            newest = posts.first() if n_posts else None
            message = 'أضفنا ' + ' و'.join(parts) + (f'، منها: {newest.title}' if newest else '')
            url = '/blog/' if n_posts else '/questions/'

        self.stdout.write(f'Digest: {title} | {message} | {url}')
        if opts['dry_run']:
            return
        if not is_configured():
            # منعلّمش المحتوى إنه اتبعت: أول ما Firebase يتظبط، أول deploy بعدها هيبعت الإشعار المجمّع
            self.stdout.write(self.style.WARNING('Firebase not configured; nothing sent (content stays pending).'))
            return
        now = timezone.now()
        posts.update(push_sent_at=now)
        questions.update(push_sent_at=now)
        send_public_notification(title=title, message=message[:200], url=url)
        self.stdout.write(self.style.SUCCESS('Digest notification sent.'))
