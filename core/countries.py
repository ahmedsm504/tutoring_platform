"""صفحات «تحفيظ القرآن أونلاين في <دولة>».

كل صفحة فيها حاجات مفيدة فعلًا لأهل البلد دي، مش نفس الكلام بتغيير الاسم:
- فرق التوقيت مع القاهرة (صيفي وشتوي محسوب من tz database)
- مواعيد الحصص المتاحة بتوقيتهم، محسوبة من مواعيد عمل المعلمات (السبت–الخميس، 9 الصبح–12 بالليل بتوقيت القاهرة)
- الأسعار بعملتهم (core/pricing.py)
- نصائح خاصة بنظام الدراسة والإجازات واللغة عندهم
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

CAIRO = ZoneInfo('Africa/Cairo')
TEACHER_START, TEACHER_END = 9, 24  # بتوقيت القاهرة
TEACHER_DAYS_AR = 'السبت إلى الخميس'

COUNTRIES = [
    {
        'slug': 'saudi-arabia', 'name': 'السعودية', 'in': 'في السعودية', 'tz': 'Asia/Riyadh', 'currency': 'SAR',
        'people': 'الأسر في السعودية',
        'weekend': 'الجمعة والسبت',
        'intro': 'في السعودية حلقات التحفيظ في المساجد منتشرة، لكن كتير من الأسر بقت تفضّل الحصة الفردية أونلاين: المعلمة مع طفل واحد بس، والمواعيد بعد المدرسة ومن غير مشاوير، خصوصًا في المدن الكبيرة وزحمة الطرق.',
        'tips': [
            'اليوم الدراسي في السعودية بيخلص غالبًا قبل الظهر أو بعده بشوية، فالفترة من بعد العصر لقبل المغرب مناسبة لأغلب الأطفال.',
            'لو طفلك في حلقة مسجد، الحصة الفردية ممكن تبقى للتصحيح والتثبيت والمراجعة، والمسجد للحفظ الجديد، أو العكس.',
            'في رمضان كتير من الأسر بتنقل الحصة لبعد التراويح أو قبل السحور، والمواعيد عندنا بتتغير معاك بسهولة.',
            'الإجازة الصيفية الطويلة فرصة لختم جزء كامل بخطة مكثفة: 12 حصة في الشهر بدل 8.',
        ],
        'faq': [
            ('هل المعلمات سعوديات؟', 'المعلمات مصريات مُجازات ومتقنات للتجويد، بيقرأوا برواية حفص اللي بيقرأ بيها أغلب أهل السعودية، ولهجتهم واضحة ومفهومة للأطفال هناك.'),
            ('الحصة تتعارض مع حلقة المسجد؟', 'لا، بنحدد الموعد اللي يناسبك، وكتير من طلابنا بيجمعوا بين الاتنين.'),
        ],
    },
    {
        'slug': 'uae', 'name': 'الإمارات', 'in': 'في الإمارات', 'tz': 'Asia/Dubai', 'currency': 'AED',
        'people': 'الأسر في الإمارات',
        'weekend': 'السبت والأحد (والجمعة نص يوم في المدارس الحكومية)',
        'intro': 'في الإمارات أسر كتير من جنسيات مختلفة، وأطفال كتير في مدارس دولية لغتها إنجليزي، وده بيخلي الطفل محتاج معلمة صبورة تبدأ معاه من الحروف وتشرح ببساطة. الحصة الفردية أونلاين بتحل مشكلة المواعيد والمشاوير بين دبي وأبوظبي والشارقة.',
        'tips': [
            'بما إن الويك إند السبت والأحد، تقدر تحط حصة الصبح في الإجازة لما الطفل يكون فايق.',
            'لو طفلك في مدرسة دولية ولغته العربية ضعيفة، ابدأ بدورة نور البيان للقراءة الصحيحة قبل الحفظ.',
            'التوقيت متقدم ساعة أو ساعتين عن القاهرة حسب التوقيت الصيفي، فمواعيد بالليل عندكم بتكون لسه بدري عند المعلمة.',
        ],
        'faq': [
            ('طفلي بيتكلم إنجليزي أكتر من عربي، ينفع؟', 'أيوه، المعلمة بتبدأ من مستواه وبتشرح ببساطة، ولو محتاج شرح بالإنجليزي بلّغنا في الحجز ونرشحلك معلمة مناسبة.'),
            ('ينفع أكتر من طفل في نفس الوقت؟', 'كل طفل ليه حصته الفردية، لكن ممكن نحط حصص الإخوات ورا بعض في نفس اليوم.'),
        ],
    },
    {
        'slug': 'kuwait', 'name': 'الكويت', 'in': 'في الكويت', 'tz': 'Asia/Kuwait', 'currency': 'KWD',
        'people': 'الأسر في الكويت',
        'weekend': 'الجمعة والسبت',
        'intro': 'الأسر في الكويت مهتمة جدًا بالمسابقات القرآنية وحفظ الأجزاء، وكتير منهم عايز متابعة فردية دقيقة تثبّت الحفظ قبل المسابقات. الحصة أونلاين بتدي الطفل معلمة ليه لوحده بمواعيد مرنة.',
        'tips': [
            'لو طفلك بيستعد لمسابقة، قول للمعلمة الأجزاء المطلوبة وموعد المسابقة، وهي تعمل خطة مراجعة مكثفة قبلها.',
            'التوقيت قريب جدًا من القاهرة (ساعة فرق أو مفيش فرق في الصيف)، فأي وقت بعد المدرسة متاح تقريبًا.',
            'في الصيف الحر بيخلي الأطفال في البيت أغلب اليوم، فدي فرصة لزيادة عدد الحصص.',
        ],
        'faq': [
            ('ممكن تحضّروا طفلي لمسابقة حفظ؟', 'أيوه، المعلمة بتعمل خطة مراجعة واختبارات تسميع على الأجزاء المطلوبة.'),
            ('السعر بالدينار؟', 'أيوه، الأسعار في الصفحة دي بالدينار الكويتي.'),
        ],
    },
    {
        'slug': 'qatar', 'name': 'قطر', 'in': 'في قطر', 'tz': 'Asia/Qatar', 'currency': 'QAR',
        'people': 'الأسر في قطر',
        'weekend': 'الجمعة والسبت',
        'intro': 'في قطر أسر عربية كتير بتدور على معلمة قرآن ثابتة لأولادها بمواعيد تناسب الشغل والمدرسة. الحصة الفردية أونلاين بتوفر الوقت، والمعلمة بتعرف الطالب كويس مع الوقت.',
        'tips': [
            'التوقيت ساعة قدام القاهرة في الشتا، ومفيش فرق في الصيف، فالمواعيد سهلة جدًا.',
            'الأطفال الصغار (6–8 سنين) بيستفيدوا أكتر من 4 حصص في الشهر في الأول، وبعدين تزوّد.',
            'خلي الحصة في نفس الموعد كل أسبوع، الثبات بيفرق جدًا مع الأطفال.',
        ],
        'faq': [
            ('ممكن أغير الموعد لو سافرنا؟', 'أيوه، بلغنا بالتوقيت الجديد والمعلمة تظبط معاك.'),
            ('السعر بالريال القطري؟', 'أيوه، الأسعار في الصفحة دي بالريال القطري.'),
        ],
    },
    {
        'slug': 'egypt', 'name': 'مصر', 'in': 'في مصر', 'tz': 'Africa/Cairo', 'currency': 'EGP',
        'people': 'الأسر في مصر',
        'weekend': 'الجمعة (والسبت في أغلب المدارس)',
        'intro': 'في مصر الكتاتيب ومراكز التحفيظ موجودة في كل مكان، لكن الحصة الفردية أونلاين بتدي الطفل اهتمام كامل من المعلمة، ومن غير مشاوير ولا مواصلات، وفي الوقت اللي يناسب الدروس والمذاكرة.',
        'tips': [
            'المعلمات على نفس توقيتك، فأي ميعاد من 9 الصبح لـ 12 بالليل متاح.',
            'في أيام الامتحانات ممكن تقلل الحصص بدل ما توقف خالص، عشان الطفل ميفقدش اللي حفظه.',
            'باقة 4 حصص بداية كويسة للأطفال الصغيرين، وبعدين تزود لما الطفل يتعود.',
        ],
        'faq': [
            ('ليه أسعار مصر مختلفة؟', 'أسعار مصر بالجنيه المصري ومعمولة تناسب السوق المصري.'),
            ('ينفع الدفع فودافون كاش أو إنستاباي؟', 'طرق الدفع المتاحة بنتفق عليها معاك بعد الحلقة التجريبية، اسألنا على واتساب.'),
        ],
    },
    {
        'slug': 'usa', 'name': 'أمريكا', 'in': 'في أمريكا', 'tz': 'America/New_York', 'currency': 'USD',
        'people': 'الأسر العربية والمسلمة في أمريكا',
        'weekend': 'السبت والأحد',
        'extra_zones': [('الساحل الغربي (لوس أنجلوس)', 'America/Los_Angeles'), ('الوسط (شيكاغو)', 'America/Chicago')],
        'intro': 'الأسر المسلمة في أمريكا بتواجه تحدي إن الطفل لغته الأولى إنجليزي، وأقرب مسجد أو مدرسة ويك إند ممكن يكون بعيد. الحصة الفردية أونلاين بتدي الطفل معلمة متقنة من بيته، وفي ويك إند الصبح أو بعد المدرسة.',
        'tips': [
            'فرق التوقيت كبير (7 ساعات في الساحل الشرقي، و10 في الغربي)، فأنسب وقت غالبًا الصبح بدري قبل المدرسة أو ويك إند الصبح والضهر.',
            'السبت عندكم يوم شغل عند المعلمات، فحصص السبت الصبح مناسبة جدًا. الجمعة إجازة عند المعلمات.',
            'لو الطفل بيقرأ العربي بصعوبة، ابدأ بنور البيان، وفي النسخة الإنجليزي من الموقع شرح كامل بالإنجليزي.',
            'التوقيت الصيفي في أمريكا بيتغير في مواعيد مختلفة عن مصر، فممكن الحصة تتحرك ساعة لمدة أسبوعين في مارس ونوفمبر؛ المعلمة بتأكد معاك.',
        ],
        'faq': [
            ('هل في معلمة بتتكلم إنجليزي؟', 'اكتب في الحجز إن الطالب بيتكلم إنجليزي، ونرشحلك معلمة تقدر تشرح بالإنجليزي.'),
            ('السعر بالدولار؟', 'أيوه، الأسعار في الصفحة دي بالدولار الأمريكي.'),
        ],
    },
    {
        'slug': 'canada', 'name': 'كندا', 'in': 'في كندا', 'tz': 'America/Toronto', 'currency': 'CAD',
        'people': 'الأسر العربية والمسلمة في كندا',
        'weekend': 'السبت والأحد',
        'extra_zones': [('فانكوفر', 'America/Vancouver')],
        'intro': 'في كندا الجالية العربية كبيرة في تورونتو ومونتريال وأوتاوا وكالجاري، والأطفال بيكبروا وهما بيتكلموا إنجليزي أو فرنساوي. الحصة الفردية أونلاين بتحافظ على صلتهم بالقرآن والعربي بمعلمة ثابتة.',
        'tips': [
            'فرق التوقيت مع القاهرة 7 ساعات في تورونتو ومونتريال، فأنسب وقت الصبح في الويك إند أو قبل المدرسة.',
            'الشتا الطويل والأيام القصيرة بتخلي الأطفال في البيت أكتر، فرصة لزيادة الحصص.',
            'لو الطفل في مدرسة فرنساوي في كيبيك، بلغنا عشان المعلمة تبسط الشرح بالعربي أكتر.',
        ],
        'faq': [
            ('السعر بالدولار الكندي؟', 'أيوه، الأسعار في الصفحة دي بالدولار الكندي.'),
            ('ينفع حصص يوم الأحد؟', 'أيوه، الأحد يوم شغل عند المعلمات.'),
        ],
    },
    {
        'slug': 'uk', 'name': 'بريطانيا', 'in': 'في بريطانيا', 'tz': 'Europe/London', 'currency': 'GBP',
        'people': 'الأسر العربية والمسلمة في بريطانيا',
        'weekend': 'السبت والأحد',
        'intro': 'في بريطانيا مدارس نهاية الأسبوع والمساجد بتعلم القرآن، لكن أعداد الأطفال في الفصل كبيرة. الحصة الفردية أونلاين بتدي طفلك معلمة ليه لوحده، تصحح كل حرف، وبمواعيد بعد المدرسة.',
        'tips': [
            'فرق التوقيت مع القاهرة ساعتين أغلب السنة، فبعد المدرسة عندك (4–7 مساءً) وقت مثالي عند المعلمات.',
            'الإجازات المدرسية القصيرة (half term) فرصة لحصص مكثفة ومراجعة.',
            'لو طفلك في مدرسة نهاية أسبوع، الحصة الفردية تكمّلها بالتصحيح والتثبيت.',
        ],
        'faq': [
            ('السعر بالإسترليني؟', 'أيوه، الأسعار في الصفحة دي بالجنيه الإسترليني.'),
            ('في شرح بالإنجليزي؟', 'اكتب ده في الحجز ونرشحلك معلمة تقدر تشرح بالإنجليزي، وفي كمان نسخة إنجليزي كاملة من الموقع.'),
        ],
    },
    {
        'slug': 'germany', 'name': 'ألمانيا', 'in': 'في ألمانيا', 'tz': 'Europe/Berlin', 'currency': 'EUR',
        'people': 'الأسر العربية والمسلمة في ألمانيا',
        'weekend': 'السبت والأحد',
        'intro': 'في ألمانيا أسر عربية كتير وصلت في السنين الأخيرة، والأطفال بيتعلموا ألماني في المدرسة وبيبعدوا عن العربي بسرعة. الحصة الفردية أونلاين بتحافظ على القرآن واللغة مع معلمة عربية متقنة.',
        'tips': [
            'فرق التوقيت مع القاهرة ساعة واحدة أغلب السنة، فالمواعيد سهلة جدًا: بعد المدرسة أو بالليل.',
            'المدارس الألمانية بتخلص بدري في أيام كتير، فوقت الضهر والعصر متاح للحصص.',
            'لو الطفل بقى يقرأ العربي بصعوبة، ابدأ بنور البيان قبل الحفظ.',
        ],
        'faq': [
            ('السعر باليورو؟', 'أيوه، الأسعار في الصفحة دي باليورو.'),
            ('المعلمة بتتكلم ألماني؟', 'الشرح بالعربي البسيط، والمعلمة بتبدأ مع الطفل من مستواه مهما كان.'),
        ],
    },
    {
        'slug': 'france', 'name': 'فرنسا', 'in': 'في فرنسا', 'tz': 'Europe/Paris', 'currency': 'EUR',
        'people': 'الأسر العربية والمسلمة في فرنسا',
        'weekend': 'السبت والأحد (والأربع بعد الضهر إجازة في مدارس كتير)',
        'intro': 'في فرنسا أسر كتير من المغرب العربي ومصر والشام، والأطفال لغتهم الأولى فرنساوي. الحصة الفردية أونلاين بتدي الطفل معلمة صبورة تعلمه القراءة الصحيحة والحفظ خطوة بخطوة.',
        'tips': [
            'الأربع بعد الضهر إجازة في مدارس كتير في فرنسا، وده وقت ممتاز للحصة.',
            'فرق التوقيت ساعة واحدة أغلب السنة، فالمواعيد مرنة.',
            'لو الأسرة مغاربية وبتقرأ برواية ورش، قولنا في الحجز؛ إحنا بنعلّم برواية حفص، والمعلمة هتوضحلك الفرق.',
        ],
        'faq': [
            ('السعر باليورو؟', 'أيوه، الأسعار في الصفحة دي باليورو.'),
            ('بتعلموا برواية ورش؟', 'التعليم عندنا برواية حفص عن عاصم.'),
        ],
    },
]
BY_SLUG = {c['slug']: c for c in COUNTRIES}

# النسخة الإنجليزي للدول اللي أطفالها لغتهم الأولى غالبًا إنجليزي/لغة أوروبية
EN = {
    'usa': {
        'name': 'the USA', 'title_name': 'USA', 'people': 'Muslim families in the USA', 'weekend': 'Saturday and Sunday',
        'extra_zones': [('West Coast (Los Angeles)', 'America/Los_Angeles'), ('Central (Chicago)', 'America/Chicago')],
        'intro': "Many Muslim children in America speak English first, and the nearest mosque or weekend school can be a long drive away. A one-to-one online class gives your child a qualified Quran teacher at home, before school or on weekend mornings.",
        'tips': [
            'Cairo is 7 hours ahead of the East Coast and 10 hours ahead of the West Coast, so early mornings before school and weekend mornings usually work best.',
            'Saturday is a working day for our teachers, so Saturday morning classes are easy to book. Friday is their day off.',
            'If your child struggles to read Arabic, start with the Noor Al-Bayan reading course before memorisation.',
            'The US changes its clocks on different dates from Egypt, so for a couple of weeks in spring and autumn the class may move by an hour; the teacher will confirm with you.',
        ],
        'faq': [
            ('Can the teacher explain in English?', "Write in the booking form that the student speaks English and we will match you with a teacher who can explain in English."),
            ('Are prices in US dollars?', 'Yes, the prices on this page are in US dollars.'),
        ],
    },
    'canada': {
        'name': 'Canada', 'title_name': 'Canada', 'people': 'Muslim families in Canada', 'weekend': 'Saturday and Sunday',
        'extra_zones': [('Vancouver', 'America/Vancouver')],
        'intro': 'Large Arab and Muslim communities live in Toronto, Montreal, Ottawa and Calgary, and children grow up speaking English or French. One-to-one online classes keep them connected to the Quran with the same teacher every week.',
        'tips': [
            'Toronto and Montreal are 7 hours behind Cairo, so weekend mornings or early mornings before school fit best.',
            'Long winters keep children indoors more, which is a good time to add classes.',
            'If your child attends a French school in Quebec, let us know so the teacher keeps explanations especially simple.',
        ],
        'faq': [
            ('Are prices in Canadian dollars?', 'Yes, the prices on this page are in Canadian dollars.'),
            ('Can we book Sunday classes?', 'Yes, Sunday is a working day for our teachers.'),
        ],
    },
    'uk': {
        'name': 'the UK', 'title_name': 'UK', 'people': 'Muslim families in the UK', 'weekend': 'Saturday and Sunday',
        'intro': 'Mosques and weekend schools across the UK teach the Quran, but classes are often large. A one-to-one online class gives your child their own teacher who corrects every letter, at a time that suits school.',
        'tips': [
            'The UK is 2 hours behind Cairo for most of the year, so after school (4–7 pm) is an ideal time.',
            'Half-term breaks are a good chance for extra classes and revision.',
            'If your child already attends a weekend school, one-to-one classes can focus on correction and revision.',
        ],
        'faq': [
            ('Are prices in pounds?', 'Yes, the prices on this page are in pounds sterling.'),
            ('Can the teacher explain in English?', 'Mention it in the booking form and we will match you with a teacher who can explain in English.'),
        ],
    },
    'germany': {
        'name': 'Germany', 'title_name': 'Germany', 'people': 'Muslim families in Germany', 'weekend': 'Saturday and Sunday',
        'intro': 'Many Arab families have settled in Germany in recent years, and children quickly lose their Arabic as they learn German at school. One-to-one online classes keep the Quran and the language alive with a qualified Arabic-speaking teacher.',
        'tips': [
            'Germany is 1 hour behind Cairo for most of the year, so after-school and evening times are easy.',
            'German schools often finish early, so early afternoon is often free for a class.',
            'If your child reads Arabic with difficulty, start with Noor Al-Bayan before memorisation.',
        ],
        'faq': [
            ('Are prices in euros?', 'Yes, the prices on this page are in euros.'),
            ('Does the teacher speak German?', 'Explanations are in simple Arabic, and the teacher starts from your child\'s level, whatever it is.'),
        ],
    },
    'france': {
        'name': 'France', 'title_name': 'France', 'people': 'Muslim families in France', 'weekend': 'Saturday and Sunday (and Wednesday afternoons off in many schools)',
        'intro': 'Many families in France come from North Africa, Egypt and the Levant, and their children speak French first. A one-to-one online class gives your child a patient teacher who builds correct reading and memorisation step by step.',
        'tips': [
            'Many French schools are off on Wednesday afternoons, which is an excellent time for a class.',
            'France is 1 hour behind Cairo for most of the year, so times are flexible.',
            'We teach the Hafs narration; if your family reads Warsh, mention it and the teacher will explain the differences.',
        ],
        'faq': [
            ('Are prices in euros?', 'Yes, the prices on this page are in euros.'),
            ('Do you teach the Warsh narration?', 'We teach the Hafs an Asim narration.'),
        ],
    },
}


def _hour_label_en(h):
    h = int(h) % 24
    if h == 0:
        return 'midnight'
    if h == 12:
        return 'noon'
    return f'{h} am' if h < 12 else f'{h - 12} pm'


def _offset_en(h):
    if h == 0:
        return 'same time as Cairo'
    n = abs(h)
    n = int(n) if n == int(n) else n
    return f'{n} hour{"s" if n != 1 else ""} {"ahead of" if h > 0 else "behind"} Cairo'


def time_info_en(tz, year=None):
    year = year or datetime.now().year
    rows = []
    for label, when in (('Winter (January)', datetime(year, 1, 15, 12)), ('Summer (July)', datetime(year, 7, 15, 12))):
        off = _offset_hours(tz, when)
        rows.append({'season': label, 'offset': _offset_en(off),
                     'window': f'{_hour_label_en(TEACHER_START + off)} to {_hour_label_en(TEACHER_END + off)}'})
    same = rows[0]['offset'] == rows[1]['offset']
    return {'rows': rows[:1] if same else rows, 'same_all_year': same}


SLOTS_EN = [('Before school', 7), ('Midday', 13), ('After school', 16), ('Early evening', 19), ('Evening', 21)]


def slots_en(tz, when=None):
    when = when or datetime.now().replace(tzinfo=None)
    off = _offset_hours(tz, when)
    return [{'label': label, 'local': _hour_label_en(h), 'cairo': _hour_label_en(h - off),
             'ok': TEACHER_START <= h - off <= TEACHER_END - 1} for label, h in SLOTS_EN]


def context_en(slug):
    from .pricing import context as price_ctx
    c, e = BY_SLUG[slug], EN[slug]
    extra = [{'name': n, **time_info_en(z)} for n, z in e.get('extra_zones', [])]
    return {'country': c, 'c': e, 'times': time_info_en(c['tz']), 'extra_times': extra,
            'slots': slots_en(c['tz']), **price_ctx(c['currency'], en=True)}


def _offset_hours(tz, when):
    z = ZoneInfo(tz)
    a = when.replace(tzinfo=z).utcoffset() - when.replace(tzinfo=CAIRO).utcoffset()
    return a.total_seconds() / 3600


def _fmt_offset(h):
    if h == 0:
        return 'نفس توقيت القاهرة'
    n = abs(h)
    n = int(n) if n == int(n) else n
    unit = 'ساعة' if n == 1 else ('ساعتين' if n == 2 else f'{n} ساعات')
    if n in (1, 2):
        return f'{unit} {"قدام" if h > 0 else "ورا"} القاهرة'
    return f'{unit} {"قدام" if h > 0 else "ورا"} القاهرة'


def _hour_label(h):
    h = int(h) % 24
    if h == 0:
        return '12 بالليل'
    if h <= 3:
        return f'{h} بعد نص الليل'
    if h <= 5:
        return f'{h} الفجر'
    if h <= 11:
        return f'{h} الصبح'
    if h == 12:
        return '12 الضهر'
    h12 = h - 12
    if h12 <= 2:
        return f'{h12} الضهر'
    if h12 <= 5:
        return f'{h12} العصر'
    return f'{h12} بالليل'


def time_info(tz, year=None):
    """فرق التوقيت شتا/صيف، ومواعيد الحصص المتاحة بتوقيت البلد"""
    year = year or datetime.now().year
    winter, summer = datetime(year, 1, 15, 12), datetime(year, 7, 15, 12)
    rows = []
    for label, when in (('في الشتا (يناير)', winter), ('في الصيف (يوليو)', summer)):
        off = _offset_hours(tz, when)
        start, end = TEACHER_START + off, TEACHER_END + off
        rows.append({'season': label, 'offset': _fmt_offset(off),
                     'window': f'من {_hour_label(start)} لـ {_hour_label(end)}'})
    same = rows[0]['offset'] == rows[1]['offset'] and rows[0]['window'] == rows[1]['window']
    return {'rows': rows[:1] if same else rows, 'same_all_year': same}


SLOTS = [('قبل المدرسة', 7), ('الضهر', 13), ('بعد المدرسة', 16), ('بعد المغرب', 19), ('بالليل', 21)]


def slots(tz, when=None):
    """مواعيد شائعة بتوقيت البلد: متاحة ولا لأ، وكام الساعة عند المعلمة"""
    when = when or datetime.now().replace(tzinfo=None)
    off = _offset_hours(tz, when)
    out = []
    for label, h in SLOTS:
        cairo = h - off
        ok = TEACHER_START <= cairo <= TEACHER_END - 1
        out.append({'label': label, 'local': _hour_label(h), 'cairo': _hour_label(cairo), 'ok': ok})
    return out


def context(country):
    from .pricing import context as price_ctx
    info = time_info(country['tz'])
    extra = [{'name': n, **time_info(z)} for n, z in country.get('extra_zones', [])]
    return {'country': country, 'times': info, 'extra_times': extra, 'slots': slots(country['tz']),
            'teacher_days': TEACHER_DAYS_AR, **price_ctx(country['currency'])}
