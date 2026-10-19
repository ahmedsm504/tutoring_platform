"""يضيف أسئلة شائعة بإجاباتها من content_seed/questions.py (مرة واحدة).
السؤال اللي عنوانه أو رابطه موجود أصلًا مبيتكررش."""
import re
from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def _plain(text, limit=155):
    t = re.sub(r'^\s*(#{2,3}|[-•*>]|\d+[.)])\s+', '', text, flags=re.M)
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', t)
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
    t = re.sub(r'^\|.*$', '', t, flags=re.M)
    t = re.sub(r'\s+', ' ', t).strip()
    return t if len(t) <= limit else t[:limit - 1].rsplit(' ', 1)[0] + '…'


def seed(apps, schema_editor):
    from content_seed.questions import ASKER, QNA_CATEGORIES, QUESTIONS_WAVE1 as QUESTIONS

    User = apps.get_model('accounts', 'User')
    Cat = apps.get_model('qna', 'QuestionCategory')
    Q = apps.get_model('qna', 'PublicQuestion')
    A = apps.get_model('qna', 'QuestionAnswer')

    team = User.objects.filter(is_superuser=True).order_by('id').first()
    cats = {}
    for slug, (name, icon, desc, order) in QNA_CATEGORIES.items():
        cats[slug], _ = Cat.objects.get_or_create(slug=slug, defaults={'name': name, 'icon': icon, 'description': desc, 'order': order})

    now = timezone.now()
    for i, (cat, title, question, answer) in enumerate(QUESTIONS):
        if Q.objects.filter(title=title).exists():
            continue
        slug = re.sub(r'[^\w\-]', '', title.strip().replace(' ', '-'))[:240]
        base, n = slug, 1
        while Q.objects.filter(slug=slug).exists():
            slug, n = f'{base}-{n}', n + 1
        q = Q.objects.create(
            visitor_name=ASKER.get(cat, 'زوار الموقع'), title=title, question_text=question,
            category=cats[cat], status='approved', is_frequent=True, slug=slug,
            meta_description=_plain(answer),
        )
        # تواريخ متدرجة عشان الترتيب يبقى ثابت (الأحدث فوق)
        Q.objects.filter(pk=q.pk).update(created_at=now - timedelta(minutes=len(QUESTIONS) - i))
        A.objects.create(question=q, answer_text=answer, answered_by=team, is_featured=True)


class Migration(migrations.Migration):
    dependencies = [
        ('qna', '0003_alter_uservote_options_communityanswer_and_more'),
        ('accounts', '0004_fcmtoken_user'),
    ]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
