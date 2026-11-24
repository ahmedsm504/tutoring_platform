"""اختبار تحديد المستوى (5 أسئلة) -> البرنامج والباقة المناسبين وزرار حجز.
بيشتغل من السيرفر (فورم GET)، فمش محتاج جافاسكربت."""

QUESTIONS = [
    ('who', 'مين اللي هيتعلم؟', [
        ('kid', 'طفل من 4 لـ 9 سنين'), ('teen', 'طفل أو مراهق من 10 لـ 15 سنة'), ('adult', 'كبير (16 سنة أو أكتر)')]),
    ('reading', 'بيقرأ العربي إزاي؟', [
        ('none', 'لسه مبيقرأش أو بيتعلم الحروف'), ('weak', 'بيقرأ بس ببطء أو بأخطاء'), ('good', 'بيقرأ كويس من المصحف')]),
    ('memorized', 'حافظ قد إيه من القرآن؟', [
        ('little', 'ولا حاجة أو سور قصيرة'), ('amma', 'جزء عمّ أو قريب منه'), ('more', 'أكتر من جزء')]),
    ('goal', 'إيه أهم هدف دلوقتي؟', [
        ('hifz', 'الحفظ والمراجعة'), ('tajweed', 'تصحيح التلاوة والتجويد'), ('sunnah', 'دراسة الأحاديث (الأربعين النووية)')]),
    ('times', 'كام مرة في الأسبوع تقدر تحضر؟', [
        ('1', 'مرة واحدة'), ('2', 'مرتين'), ('3', '3 مرات')]),
]
VALID = {k: {v for v, _ in opts} for k, _, opts in QUESTIONS}


def answers_from(get):
    a = {k: get.get(k) for k in VALID}
    return a if all(a[k] in VALID[k] for k in VALID) else None


def recommend(a):
    """يرجع (slug البرنامج، عدد الحصص في الشهر، مدة الحصة بالدقايق، أسباب)"""
    reasons = []
    if a['goal'] == 'sunnah' and a['reading'] != 'none':
        slug = 'arbaeen'
        reasons.append('هدفك دراسة الأحاديث، ودي دورة منهجية في الأربعين النووية.')
    elif a['reading'] == 'none' and a['who'] != 'kid':
        slug = 'nour-albayan'
        reasons.append('الأول لازم القراءة الصحيحة للحروف والكلمات، ونور البيان بتأسس ده خطوة بخطوة قبل الحفظ.')
    elif a['who'] == 'kid':
        slug = 'nourania'
        reasons.append('للأطفال الصغيرين بنبدأ بالتلقين والتشجيع والألعاب التعليمية، والمعلمة بتشرح المعاني ببساطة.')
        if a['reading'] == 'none':
            reasons.append('الطفل لسه مبيقرأش، فالحفظ هيكون بالتلقين مع تعليم الحروف بالتدريج.')
    elif a['goal'] == 'tajweed' or a['reading'] == 'weak':
        slug = 'ghiras'
        reasons.append('التلاوة محتاجة تصحيح الأول (المخارج والأحكام)، عشان اللي هيتحفظ يتحفظ صح.')
    elif a['who'] == 'teen':
        slug = 'himma'
        reasons.append('في السن ده الحفظ بتدرج مع متابعة أسبوعية بيمشي كويس جنب المدرسة.')
    else:
        slug = 'sufaraa'
        reasons.append('للكبار: خطة حفظ ومراجعة على قد وقتك، سواء بتبدأ أو بتكمّل.')
    if a['memorized'] == 'more' and slug in ('himma', 'sufaraa', 'nourania'):
        reasons.append('حافظ أكتر من جزء، فالخطة هتهتم بالمراجعة والتثبيت مع الجديد.')
    count = {'1': 4, '2': 8, '3': 12}[a['times']]
    minutes = 30 if a['who'] == 'kid' else (60 if a['times'] == '1' and a['who'] == 'adult' else 30)
    if minutes == 60:
        reasons.append('حصة واحدة في الأسبوع للكبار الأحسن تبقى ساعة، عشان يبقى فيه وقت للتسميع والجديد.')
    return slug, count, minutes, reasons


def note_for(a, slug):
    labels = {k: dict(opts) for k, _, opts in QUESTIONS}
    return ('اختبار المستوى: ' + '، '.join(labels[k][a[k]] for k in ('who', 'reading', 'memorized', 'goal', 'times'))
            + f' — الترشيح: {slug}')[:300]
