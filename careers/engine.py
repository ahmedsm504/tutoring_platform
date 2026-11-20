"""التحقق من إجابات أي نموذج توظيف حسب أسئلته المحفوظة في الأدمن."""
import os
import re

AR_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')
MB = 1024 * 1024
IMG_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}
EXT_SETS = {'images': IMG_EXT | {'.pdf'}, 'docs': IMG_EXT | {'.pdf', '.doc', '.docx'}}
AUDIO_EXT = {'.webm', '.ogg', '.oga', '.opus', '.mp3', '.m4a', '.mp4', '.aac', '.wav', '.amr', '.3gp'}
MIME_OF = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp',
           '.heic': 'image/heic', '.heif': 'image/heif', '.pdf': 'application/pdf', '.doc': 'application/msword',
           '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
           '.webm': 'audio/webm', '.ogg': 'audio/ogg', '.oga': 'audio/ogg', '.opus': 'audio/ogg', '.mp3': 'audio/mpeg',
           '.m4a': 'audio/mp4', '.mp4': 'audio/mp4', '.aac': 'audio/aac', '.wav': 'audio/wav', '.amr': 'audio/amr',
           '.3gp': 'audio/3gpp'}
FILE_MAX = 8 * MB
AUDIO_MAX = 15 * MB
TOTAL_MAX = 45 * MB
REQ = 'هذا الحقل مطلوب.'


def digits(v):
    return str(v or '').translate(AR_DIGITS).strip()


def _file_ext(f, allowed, audio):
    ext = os.path.splitext(f.name or '')[1].lower()
    if ext in allowed:
        return ext
    ctype = (f.content_type or '').split(';')[0].lower()
    for e in allowed:
        if MIME_OF.get(e) == ctype:
            return e
    if audio and ctype in ('video/webm', 'audio/x-m4a', 'video/mp4', 'audio/webm', 'audio/ogg'):
        return '.m4a' if 'mp4' in ctype or 'm4a' in ctype else ('.ogg' if 'ogg' in ctype else '.webm')
    return None


def validate(questions, post, files):
    """يرجع (answers, files_out, meta, errors).
    answers: [{'q','step','label','type','value'}] ، files_out: [(question, label, name, mime, bytes)]
    meta: {'name','phone','age','city'} ، errors: {key: رسالة}"""
    answers, files_out, errors, meta, total = [], [], {}, {}, 0
    for q in questions:
        if q.qtype == 'info':
            continue
        key = q.key
        value = None
        if q.qtype in ('files', 'audio'):
            items = [f for f in files.getlist(key) if f and f.size]
            if not items:
                if q.required:
                    errors[key] = 'من فضلك سجّلي أو ارفعي الملف الصوتي.' if q.qtype == 'audio' else 'من فضلك ارفعي الملف المطلوب.'
                continue
            audio = q.qtype == 'audio'
            limit = 1 if audio else max(1, q.max_files or 1)
            if len(items) > limit:
                errors[key] = f'أقصى عدد للملفات هنا {limit}.'
                continue
            allowed = AUDIO_EXT if audio else EXT_SETS.get(q.file_kind, EXT_SETS['images'])
            names = []
            for f in items:
                ext = _file_ext(f, allowed, audio)
                if not ext:
                    errors[key] = 'نوع الملف غير مسموح هنا.'
                    break
                maxs = AUDIO_MAX if audio else FILE_MAX
                if f.size > maxs:
                    errors[key] = f'حجم الملف أكبر من {maxs // MB} ميجا.'
                    break
                total += f.size
                name = os.path.basename(f.name or '')[:150] or f'file{ext}'
                if not name.lower().endswith(ext):
                    name = f'{os.path.splitext(name)[0] or "file"}{ext}'
                files_out.append((q, q.label, name, MIME_OF.get(ext, 'application/octet-stream'), f.read()))
                names.append(name)
            value = '، '.join(names)
        elif q.qtype == 'checkboxes':
            opts = q.choice_list()
            vals = [v for v in post.getlist(key) if v in opts]
            if not vals and q.required:
                errors[key] = 'من فضلك اختاري إجابة واحدة على الأقل.'
                continue
            value = '، '.join(vals)
        elif q.qtype == 'agree':
            if post.get(key) != 'on':
                if q.required:
                    errors[key] = q.reject_message or 'من فضلك وافقي على هذا الشرط للمتابعة.'
                continue
            value = 'موافقة ✓'
        else:
            raw = (post.get(key) or '').strip()
            if not raw:
                if q.required:
                    errors[key] = 'من فضلك اختاري إجابة.' if q.qtype in ('radio', 'select', 'yesno') else REQ
                continue
            if q.qtype in ('radio', 'select', 'yesno') and raw not in q.choice_list():
                errors[key] = 'من فضلك اختاري إجابة من الاختيارات.'
                continue
            if q.qtype == 'number':
                m = re.search(r'\d+', digits(raw))
                n = int(m.group()) if m else None
                if n is None or (q.min_value is not None and n < q.min_value) or (q.max_value is not None and n > q.max_value):
                    rng = ''
                    if q.min_value is not None and q.max_value is not None:
                        rng = f' (من {q.min_value} إلى {q.max_value})'
                    errors[key] = (q.reject_message if n is not None and q.reject_message
                                   else f'اكتبي رقمًا صحيحًا بالأرقام{rng}.')
                    continue
                raw = str(n)
            elif q.qtype == 'phone':
                v = re.sub(r'[\s\-()]', '', digits(raw))
                if v.startswith('00'):
                    v = '+' + v[2:]
                if not re.fullmatch(r'\+?\d{9,15}', v):
                    errors[key] = 'اكتبي رقمًا صحيحًا (مثال: 01012345678 أو ‎+201012345678).'
                    continue
                if re.fullmatch(r'01\d{9}', v):
                    v = '+2' + v
                raw = v
            else:
                raw = ' '.join(raw.split()) if q.qtype != 'textarea' else raw
                if q.min_words and len(raw.split()) < q.min_words:
                    errors[key] = 'من فضلك اكتبي الاسم ثلاثيًا.' if q.role == 'name' else f'اكتبي {q.min_words} كلمات على الأقل.'
                    continue
                if q.min_length and len(raw) < q.min_length:
                    errors[key] = 'من فضلك اكتبي إجابة أكثر تفصيلًا.'
                    continue
            if q.required_answer and raw != q.required_answer.strip():
                errors[key] = q.reject_message or f'هذا شرط أساسي: الإجابة المطلوبة «{q.required_answer}».'
                continue
            value = raw[:5000]
        if value is None:
            continue
        answers.append({'q': q.pk, 'step': q.step.title, 'label': q.label, 'type': q.qtype, 'value': value})
        if q.role and q.role not in meta:
            meta[q.role] = value[:150]
    if total > TOTAL_MAX:
        errors['__all__'] = 'إجمالي حجم المرفقات كبير جدًا. صغّري الصور أو التسجيلات وحاولي مرة أخرى.'
    return answers, files_out, meta, errors
