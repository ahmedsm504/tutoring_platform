"""منطق الواجبات والنقاط: الرفع، الفلترة، الإشعارات، الأوسمة."""
import logging
import mimetypes
import os
from datetime import datetime, time

from django.conf import settings
from django.db.models import Count, Q, Sum
from django.urls import reverse
from django.utils import timezone

from chat.filters import scan
from chat.services import _background

from .models import Homework, StudentActivity, Submission

logger = logging.getLogger(__name__)

AUDIO_MIMES = {'audio/webm', 'audio/ogg', 'audio/mpeg', 'audio/mp4', 'audio/aac', 'audio/wav', 'audio/x-wav',
               'audio/x-m4a', 'audio/m4a', 'audio/mp3', 'audio/opus', 'video/webm', 'audio/amr', 'audio/3gpp'}
AUDIO_EXT = {'.webm', '.ogg', '.oga', '.opus', '.mp3', '.m4a', '.mp4', '.aac', '.wav', '.amr', '.3gp'}
MAX_AUDIO_MB = 20

# نقاط
POINTS_SUBMIT = 10            # أول تسليم لكل واجب
POINTS_PER_STAR = 4           # لما المعلمة تقبل الواجب
GAME_DAILY_CAP = 60
LISTEN_POINTS = 2
LISTEN_DAILY_CAP = 10

LEVELS = [(0, 'برعم القرآن 🌱'), (60, 'زهرة القرآن 🌷'), (150, 'نجم الحلقة ⭐'), (300, 'فارس الحفظ 🏇'),
          (500, 'بطل التلاوة 🏆'), (800, 'سفير القرآن 🕌'), (1200, 'تاج الوقار 👑')]


class Refused(Exception):
    pass


def clean_text(text, *, who, student, field='الرسالة'):
    """نفس فلتر الشات: أي رقم/لينك/حساب بيتمنع، وبيتسجل للإدارة."""
    text = (text or '').strip()
    if not text:
        return ''
    if len(text) > 3000:
        raise Refused(f'{field} طويلة جدًا.')
    res = scan(text)
    if res.is_strong:
        _alert(student, who)
        raise Refused('ممنوع كتابة أرقام تليفونات أو روابط أو حسابات تواصل. كل التواصل جوه المنصة بس.')
    return text


def _alert(student, who):
    try:
        from core.models import TeacherActivity
        if student.teacher_id:
            TeacherActivity.log_chat_flag(student.teacher, student.name, 'blocked' if who == 'teacher' else 'student')
    except Exception:
        logger.exception('فشل تسجيل تنبيه الواجب')


def clean_audio(upload, required=False):
    if not upload:
        if required:
            raise Refused('سجّل صوتك الأول قبل التسليم 🎙️')
        return None, ''
    mime = (getattr(upload, 'content_type', '') or '').split(';')[0].strip().lower()
    ext = os.path.splitext(upload.name or '')[1].lower()
    if mime not in AUDIO_MIMES:
        mime = (mimetypes.guess_type(upload.name or '')[0] or '').lower()
    if mime not in AUDIO_MIMES or (ext and ext not in AUDIO_EXT):
        raise Refused('الملف لازم يكون تسجيل صوتي.')
    if upload.size > MAX_AUDIO_MB * 1024 * 1024:
        raise Refused(f'التسجيل أكبر من {MAX_AUDIO_MB} ميجا. سجّل جزء أقصر.')
    if upload.size < 800:
        raise Refused('التسجيل فاضي أو قصير جدًا. جرّب تاني.')
    if not ext:
        upload.name = 'recording' + (mimetypes.guess_extension(mime) or '.webm')
    if mime == 'video/webm':
        mime = 'audio/webm'
    return upload, mime


# ---------------------------------------------------------------- إنشاء وتسليم
def create_homework(*, teacher, students, data, teacher_audio=None):
    created = []
    audio, _ = clean_audio(teacher_audio)
    instructions = clean_text(data.get('instructions'), who='teacher', student=students[0], field='التعليمات')
    title = clean_text(data.get('title'), who='teacher', student=students[0], field='العنوان')
    for st in students:
        hw = Homework(teacher=teacher, student=st, kind=data['kind'], title=title,
                      surah=data.get('surah'), ayah_from=data.get('ayah_from'), ayah_to=data.get('ayah_to'),
                      instructions=instructions, due_date=data.get('due_date'))
        if not hw.title:
            hw.title = (dict(Homework.KIND_CHOICES)[hw.kind] + (' - ' + hw.range_label if hw.surah else ''))[:160]
        if audio:
            audio.seek(0)
            hw.teacher_audio.save(audio.name, audio, save=False)
        hw.save()
        created.append(hw)
    for hw in created:
        notify_student_new(hw)
    return created


def submit(hw, *, audio, note, user):
    if hw.status() in ('submitted', 'approved'):
        raise Refused('الواجب ده اتسلّم خلاص.' if hw.status() == 'approved' else 'التسليم مستني المعلمة تسمعه.')
    upload, mime = clean_audio(audio, required=True)
    note = clean_text(note, who='student', student=hw.student, field='الملاحظة')
    first = not hw.submissions.exists()
    sub = Submission.objects.create(homework=hw, audio=upload, audio_mime=mime, note=note)
    if first:
        StudentActivity.objects.create(student=hw.student, kind='homework', detail=f'hw{hw.pk}', points=POINTS_SUBMIT)
    notify_teacher_submitted(sub)
    return sub


def review(sub, *, status, stars, feedback, feedback_audio, teacher):
    if status not in ('approved', 'redo'):
        raise Refused('اختاري: ممتاز أو يعيد التسجيل.')
    feedback = clean_text(feedback, who='teacher', student=sub.homework.student, field='التعليق')
    audio, _ = clean_audio(feedback_audio)
    try:
        stars = max(1, min(5, int(stars or 5))) if status == 'approved' else None
    except (TypeError, ValueError):
        stars = 5
    sub.status, sub.stars, sub.feedback = status, stars, feedback
    if audio:
        sub.feedback_audio = audio
    sub.reviewed_at = timezone.now()
    sub.feedback_seen = False
    sub.save()
    if status == 'approved' and stars:
        StudentActivity.objects.get_or_create(student=sub.homework.student, kind='homework', detail=f'ok{sub.homework_id}',
                                              defaults={'points': stars * POINTS_PER_STAR})
    notify_student_reviewed(sub)
    return sub


# ---------------------------------------------------------------- نقاط الألعاب والاستماع
def award(student, kind, detail, points):
    """بيرجع النقاط اللي اتضافت فعلًا (بعد الحد اليومي)."""
    today = timezone.localdate()
    start = timezone.make_aware(datetime.combine(today, time.min))
    cap, per = (GAME_DAILY_CAP, max(0, min(int(points), 10))) if kind == 'game' else (LISTEN_DAILY_CAP, LISTEN_POINTS)
    used = StudentActivity.objects.filter(student=student, kind=kind, created_at__gte=start).aggregate(t=Sum('points'))['t'] or 0
    pts = max(0, min(per, cap - used))
    StudentActivity.objects.create(student=student, kind=kind, detail=(detail or '')[:60], points=pts)
    return pts


def level_for(points):
    cur, nxt = LEVELS[0], None
    for i, lv in enumerate(LEVELS):
        if points >= lv[0]:
            cur = lv
            nxt = LEVELS[i + 1] if i + 1 < len(LEVELS) else None
    pct = 100 if not nxt else int((points - cur[0]) * 100 / (nxt[0] - cur[0]))
    return {'name': cur[1], 'next_name': nxt[1] if nxt else '', 'next_at': nxt[0] if nxt else None,
            'to_next': (nxt[0] - points) if nxt else 0, 'pct': pct}


def stats(student):
    agg = StudentActivity.objects.filter(student=student).aggregate(
        total=Sum('points'), games=Count('id', filter=Q(kind='game')), listens=Count('id', filter=Q(kind='listen')))
    total = agg['total'] or 0
    approved = Submission.objects.filter(homework__student=student, status='approved').values('homework').distinct().count()
    five = Submission.objects.filter(homework__student=student, status='approved', stars=5).count()
    streak = StudentActivity.streak(student)
    badges = [
        ('🎙️', 'أول تسجيل', 'سلّمت أول واجب بصوتك', Submission.objects.filter(homework__student=student).exists()),
        ('📚', 'مجتهد', '5 واجبات مقبولة', approved >= 5),
        ('🌟', 'خمس نجوم', 'أخدت 5 نجوم من المعلمة', five >= 1),
        ('🎮', 'لعّيب', 'لعبت 10 ألعاب', (agg['games'] or 0) >= 10),
        ('🎧', 'مستمع', 'سمعت 10 مرات', (agg['listens'] or 0) >= 10),
        ('🔥', 'مواظب', '7 أيام ورا بعض', streak >= 7),
        ('🏆', 'بطل', '300 نجمة', total >= 300),
    ]
    return {'points': total, 'streak': streak, 'approved': approved, 'level': level_for(total),
            'badges': badges, 'badges_won': sum(1 for b in badges if b[3])}


def student_counts(student):
    """للـ badge في القائمة: واجبات جديدة/محتاجة إعادة + تصحيحات جديدة"""
    hws = Homework.objects.filter(student=student).prefetch_related('submissions')
    todo = sum(1 for h in hws if h.status() in ('new', 'redo'))
    fresh = Submission.objects.filter(homework__student=student, reviewed_at__isnull=False, feedback_seen=False).count()
    return todo, fresh


def teacher_pending(teacher):
    return Submission.objects.filter(homework__teacher=teacher, status='submitted').count()


# ---------------------------------------------------------------- الإشعارات
def _base():
    return settings.CANONICAL_URL.rstrip('/')


def notify_student_new(hw):
    st = hw.student
    if not st.user_id:
        return
    url = _base() + reverse('learning_student_homework', args=[hw.pk])

    def job():
        from accounts.notifications import send_user_notification
        send_user_notification([st.user], '📝 واجب جديد من معلمتك', hw.title, url=url, tag=f'hw-{hw.pk}')
    _background(job)


def notify_teacher_submitted(sub):
    hw = sub.homework
    t = hw.teacher
    if not t.user_id:
        return
    url = _base() + reverse('learning_teacher_detail', args=[hw.pk])

    def job():
        from accounts.notifications import send_user_notification
        send_user_notification([t.user], f'🎙️ {hw.student.name} سلّم الواجب', hw.title, url=url, tag=f'hw-{hw.pk}')
    _background(job)


def notify_student_reviewed(sub):
    hw = sub.homework
    st = hw.student
    if not st.user_id:
        return
    url = _base() + reverse('learning_student_homework', args=[hw.pk])
    title = '🌟 المعلمة صححت واجبك' if sub.status == 'approved' else '🔁 المعلمة طالبة تسجيل تاني'
    body = ('⭐' * (sub.stars or 0)) + ' ' + hw.title

    def job():
        from accounts.notifications import send_user_notification
        send_user_notification([st.user], title, body.strip(), url=url, tag=f'hw-{hw.pk}')
    _background(job)
