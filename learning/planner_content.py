"""نصوص صفحات «خطة الختمة» و«خطة الحفظ» بالعربي والإنجليزي.
كل صفحة جاهزة (preset) ليها عنوان ووصف ومقدمة وأسئلة شائعة محسوبة من أرقامها هي (مش نص مكرر)."""
from . import planner as P

HADITH_7_AR = ('وقد قال النبي ﷺ لعبد الله بن عمرو رضي الله عنهما: «اقرأ القرآن في شهر»، فلما قال إنه يطيق أكثر، '
               'قال: «فاقرأه في سبع ولا تزد على ذلك» (متفق عليه).')
HADITH_3_AR = ('وفي الحديث: «لم يفقه من قرأ القرآن في أقل من ثلاث» (رواه أبو داود والترمذي وقال: حسن صحيح)، '
               'ولذلك جعل كثير من العلماء الثلاث أقل مدة للختم في الأحوال العادية، مع التدبر وحضور القلب.')
HADITH_7_EN = ('The Prophet ﷺ told \'Abdullah ibn \'Amr: "Recite the Quran in a month." When he said he could do more, '
               'the Prophet ﷺ said: "Then recite it in seven, and do not go beyond that" (al-Bukhari and Muslim).')
HADITH_3_EN = ('In another hadith: "Whoever recites the Quran in less than three days has not understood it" '
               '(Abu Dawud and at-Tirmidhi, who graded it hasan sahih). Many scholars therefore treated three days as the '
               'minimum for a khatam in normal circumstances, with reflection and presence of heart.')


def _juz_ar(st):
    per = 30 * st['khatmas'] / st['days']
    if per < 0.95:
        n = P._num(1 / per)
        return f'جزء كل {n} {"أيام" if n.isdigit() and 3 <= int(n) <= 10 else "يوم"}'
    txt = st['juz_per_day_txt']
    return {'1': 'جزء واحد', '2': 'جزآن', '3': '3 أجزاء', '10': '10 أجزاء'}.get(txt, f'{txt} جزء')


def _min_ar(m):
    return f'{m} {"دقائق" if 3 <= m <= 10 else "دقيقة"}'


def _juz_en(st):
    per = 30 * st['khatmas'] / st['days']
    if per < 0.95:
        return f'one juz every {P._num(1 / per)} days'
    return f'{st["juz_per_day_txt"]} juz'


def _faq_ld(faq):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]}


# ------------------------------------------------------------------ الختمة


def khatma_ar(slug=None):
    days, kh = P.KHATMA_PRESETS.get(slug, (30, 1))
    st = P.khatma_stats(days, kh)
    ramadan = bool(slug and slug.startswith('ramadan'))
    if slug:
        h1 = P.khatma_title(slug)
        title = f'{h1}: {st["pages_per_day_txt"]} صفحة يوميًا | جدول جاهز للطباعة'
        meta = (f'{h1}: {st["pages_per_day_txt"]} صفحة يوميًا ({_juz_ar(st)} تقريبًا)، '
                f'جدول يوم بيوم بالصفحات والسور والآيات، وتقسيم على الصلوات، مع حاسبة لخطتك.')
    else:
        h1 = 'حاسبة ختم القرآن: اعمل جدول ختمتك يوم بيوم'
        title = 'حاسبة ختم القرآن وجدول الختمة اليومي (رمضان، شهر، أسبوع) | العجمي'
        meta = ('حاسبة مجانية لختم القرآن: اختر عدد الأيام والختمات، واحصل على جدول يومي بالصفحات والسور، '
                'وتقسيم على الصلوات الخمس، للطباعة والمشاركة على واتساب.')
    intro = []
    if ramadan:
        intro.append(f'تريد أن تختم القرآن {P.AR_KH[kh]} في رمضان؟ القرآن في مصحف المدينة 604 صفحة، فـ{P.AR_KH[kh]} '
                     f'في 30 يومًا تعني قراءة <strong>{st["pages_per_day_txt"]} صفحة يوميًا</strong> '
                     f'({_juz_ar(st)} تقريبًا)، أي نحو <strong>{st["per_prayer_txt"]} صفحات بعد كل صلاة</strong> من الصلوات الخمس.')
        intro.append('الجدول بالأسفل جاهز يوم بيوم: من أي صفحة إلى أي صفحة، ومن أي سورة وآية إلى أين. '
                     'وإذا كان الشهر 29 يومًا أو بدأت متأخرًا، غيّر عدد الأيام أو صفحة البداية في الحاسبة وسيتعدل الجدول فورًا.')
    elif slug:
        intro.append(f'لختم القرآن الكريم في {P.AR_DAYS[days]} تحتاج إلى قراءة <strong>{st["pages_per_day_txt"]} صفحة يوميًا</strong> '
                     f'من مصحف المدينة (604 صفحة)، أي حوالي {_juz_ar(st)}{" في اليوم" if 30 * kh >= days else ""}، '
                     f'وتستغرق تقريبًا <strong>{_min_ar(st["minutes"])}</strong> بقراءة متأنية.')
        intro.append('الجدول بالأسفل يحدد لك كل يوم من أي صفحة تبدأ وعند أي آية تقف، ويمكنك تعديل عدد الأيام أو صفحة البداية، '
                     'وطباعة الجدول أو حفظه PDF أو إرساله على واتساب، وتعليم الأيام التي أنجزتها.')
    else:
        intro.append('اختر في كم يومًا تريد أن تختم القرآن، وكم ختمة، ومن أي صفحة تبدأ، وستحسب لك الأداة كم صفحة تقرأ يوميًا، '
                     'وكم صفحة بعد كل صلاة، وتعطيك جدولًا يومًا بيوم بالصفحات والسور والآيات على مصحف المدينة (604 صفحة).')
        intro.append('يمكنك طباعة الجدول أو حفظه PDF، وإرساله لأهلك وأصحابك على واتساب، وإضافة تذكير يومي في التقويم، '
                     'وتعليم الأيام التي أتممتها ليظهر لك تقدمك.')
    tips = [
        'اربط وردك بالصلوات: قسمة الورد على خمس صلوات تجعله خفيفًا ومستمرًا.',
        'إذا فاتك يوم، لا تحاول تعويضه كله مرة واحدة؛ وزّعه على الأيام التالية، أو غيّر صفحة البداية في الحاسبة.',
        'اقرأ من مصحف واحد ثابت، فالجدول على ترقيم مصحف المدينة؛ ومع مصحف آخر اعتمد على أسماء السور والآيات.',
        'اجعل للتدبر نصيبًا: اقرأ تفسير صفحة واحدة يوميًا من وردك.',
    ]
    if days <= 7:
        tips.insert(0, (HADITH_3_AR if days <= 3 else HADITH_7_AR))
    faq = [
        (f'كم صفحة أقرأ يوميًا لختم القرآن في {P.AR_DAYS[days] if not ramadan else "رمضان"}؟',
         f'{P.AR_KH[kh].capitalize() if kh > 1 else "الختمة"} في {days} يومًا = {st["pages_per_day_txt"]} صفحة يوميًا تقريبًا من مصحف المدينة '
         f'(604 صفحة)، أي حوالي {_juz_ar(st)}{" في اليوم" if 30 * kh >= days else ""}.'),
        ('كم دقيقة يحتاج الورد اليومي؟',
         f'حوالي {_min_ar(st["minutes"])} يوميًا، على أساس دقيقتين تقريبًا للصفحة بقراءة متأنية. تختلف المدة حسب سرعتك وإتقانك.'),
        ('ماذا أفعل إذا فاتني يوم؟',
         'لا تترك الختمة. وزّع الصفحات الفائتة على الأيام الباقية، أو اكتب في الحاسبة الصفحة التي وصلت إليها وعدد الأيام المتبقية لتحصل على جدول جديد.'),
        ('هل الجدول على مصحف المدينة؟',
         'نعم، على مصحف المدينة المنورة (رواية حفص، 604 صفحة، كل جزء 20 صفحة تقريبًا). ومع مصحف بترقيم مختلف اعتمد على أسماء السور وأرقام الآيات الموجودة في الجدول.'),
    ]
    if st['pages_per_day'] >= 5:
        faq.insert(2, ('كيف أقسم الورد على الصلوات الخمس؟',
         f'اقرأ حوالي {st["per_prayer_txt"]} صفحة بعد كل صلاة من الصلوات الخمس، فينتهي وردك اليومي دون أن تشعر بثقله.'))
    if ramadan:
        faq.insert(3, ('ماذا لو كان رمضان 29 يومًا؟',
                       f'اكتب 29 في خانة عدد الأيام وسيزيد الورد قليلًا ليصبح حوالي {P._num(604 * kh / 29)} صفحة يوميًا. '
                       'وبعض الناس يبدأون الخطة على 29 يومًا احتياطًا ثم يجعلون اليوم الأخير للمراجعة والدعاء.'))
    if days <= 7:
        faq.append(('هل يجوز ختم القرآن في أقل من ثلاثة أيام؟', HADITH_3_AR))
    return {'h1': h1, 'title': title, 'meta': meta[:160], 'intro': intro, 'tips': tips, 'faq': faq, 'faq_ld': _faq_ld(faq),
            'stats': st, 'days': days, 'khatmas': kh}


def khatma_en(slug=None):
    days, kh = P.KHATMA_PRESETS.get(slug, (30, 1))
    st = P.khatma_stats(days, kh)
    ramadan = bool(slug and slug.startswith('ramadan'))
    if slug:
        h1 = P.khatma_title(slug, en=True)
        title = f'{h1}: {st["pages_per_day_txt"]} Pages a Day | Printable Schedule'
        meta = (f'{h1}: read {st["pages_per_day_txt"]} pages a day (about {_juz_en(st)}). A printable day-by-day '
                f'schedule with pages, surahs and ayahs.')
    else:
        h1 = 'Quran Khatam Planner: Build Your Daily Reading Schedule'
        title = 'Quran Khatam Planner & Daily Reading Schedule (Ramadan, 30 Days) | Al-Agmi'
        meta = ('Free Quran khatam planner: choose your days and number of khatams and get a day-by-day schedule with '
                'pages, surahs and a per-prayer split. Print it or share it.')
    intro = []
    if ramadan:
        intro.append(f'Want to complete {EN_KH_TXT(kh)} of the Quran this Ramadan? The standard Madinah Mushaf has 604 pages, so '
                     f'{EN_KH_TXT(kh)} in 30 days means reading <strong>{st["pages_per_day_txt"]} pages a day</strong> '
                     f'(about {_juz_en(st)}), or roughly <strong>{st["per_prayer_txt"]} pages after each of the five prayers</strong>.')
        intro.append('The schedule below tells you exactly where to start and stop each day, by page, surah and ayah. If the month '
                     'turns out to be 29 days, or you start late, change the days or starting page and the schedule updates instantly.')
    elif slug:
        intro.append(f'To finish the Quran in {P.EN_DAYS[days].lower()} you need to read <strong>{st["pages_per_day_txt"]} pages a day</strong> '
                     f'from the standard Madinah Mushaf (604 pages), which is about {_juz_en(st)}{" a day" if 30 * kh >= days else ""} and roughly '
                     f'<strong>{st["minutes"]} minutes</strong> of steady recitation.')
        intro.append('The schedule below shows each day\'s start page and the ayah where you stop. You can change the number of days '
                     'or the starting page, print it or save it as a PDF, share it on WhatsApp, and tick off the days you complete.')
    else:
        intro.append('Choose how many days you want to finish the Quran in, how many khatams, and your starting page. The planner '
                     'works out how many pages to read each day and after each prayer, and builds a day-by-day schedule with pages, '
                     'surahs and ayahs, based on the standard Madinah Mushaf (604 pages).')
        intro.append('Print it, save it as a PDF, share it with family and friends on WhatsApp, add a daily calendar reminder, '
                     'and tick off each day as you go.')
    tips = [
        'Tie your daily portion to the prayers: splitting it across the five prayers makes it light and consistent.',
        'If you miss a day, don\'t try to catch up all at once. Spread it over the next days, or enter your current page in the planner.',
        'Use one Mushaf. The schedule follows the Madinah Mushaf page numbers; with another Mushaf, follow the surah and ayah references.',
        'Leave room for reflection: read the translation or a short tafsir of one page of your daily portion.',
    ]
    if days <= 7:
        tips.insert(0, HADITH_3_EN if days <= 3 else HADITH_7_EN)
    label = 'Ramadan' if ramadan else P.EN_DAYS[days].lower()
    faq = [
        (f'How many pages a day to finish the Quran in {label}?',
         f'{EN_KH_TXT(kh).capitalize()} in {days} days is about {st["pages_per_day_txt"]} pages a day of the Madinah Mushaf '
         f'(604 pages), which is roughly {_juz_en(st)}{" a day" if 30 * kh >= days else ""}.'),
        ('How long does the daily reading take?',
         f'About {st["minutes"]} minutes a day, assuming roughly two minutes per page at a steady pace. It varies with your fluency.'),
        ('What if I miss a day?',
         'Keep going. Spread the missed pages over the remaining days, or enter the page you reached and the days left in the planner to get a new schedule.'),
        ('Which Mushaf is the schedule based on?',
         'The standard Madinah Mushaf (Hafs, 604 pages, about 20 pages per juz). If your Mushaf has different page numbers (for example a 13-line Indo-Pak Mushaf), follow the surah and ayah references in the table.'),
    ]
    if st['pages_per_day'] >= 5:
        faq.insert(2, ('How do I split it across the five prayers?',
         f'Read about {st["per_prayer_txt"]} pages after each of the five daily prayers.'))
    if ramadan:
        faq.insert(3, ('What if Ramadan is 29 days?',
                       f'Enter 29 days and your daily portion becomes about {P._num(604 * kh / 29)} pages. Some people plan for 29 days '
                       'and keep the last day for revision and du\'a.'))
    if days <= 7:
        faq.append(('Is it allowed to finish the Quran in less than three days?', HADITH_3_EN))
    return {'h1': h1, 'title': title, 'meta': meta[:160], 'intro': intro, 'tips': tips, 'faq': faq, 'faq_ld': _faq_ld(faq),
            'stats': st, 'days': days, 'khatmas': kh}


def EN_KH_TXT(kh):
    return {1: 'one khatam', 2: 'two khatams', 3: 'three khatams'}[kh]


# ------------------------------------------------------------------ الحفظ


def hifz_ar(years=None):
    y = years or 3
    st = P.hifz_stats(y)
    if years:
        h1 = f'خطة حفظ القرآن في {P.HIFZ_PRESETS[y]}'
        title = f'{h1}: {st["pages_per_day_txt"]} صفحة يوميًا | جدول شهري جاهز'
        meta = (f'{h1}: {st["pages_per_day_txt"]} صفحة ({st["lines_per_day"]} سطرًا) يوميًا 5 أيام في الأسبوع، '
                f'وجدول شهري بالسور والأجزاء، ونظام مراجعة، وحاسبة لخطتك.')
    else:
        h1 = 'حاسبة خطة حفظ القرآن الكريم'
        title = 'حاسبة خطة حفظ القرآن: كم صفحة يوميًا؟ جدول شهري جاهز | العجمي'
        meta = ('حاسبة مجانية لخطة حفظ القرآن: اختر المدة وأيام الحفظ في الأسبوع والبداية، واحصل على مقدار الحفظ اليومي '
                'وجدول شهري بالسور والأجزاء.')
    intro = []
    if years:
        intro.append(f'لحفظ القرآن الكريم كاملًا في {P.HIFZ_PRESETS[y]} مع الحفظ 5 أيام في الأسبوع، تحتاج إلى حفظ '
                     f'<strong>{st["pages_per_day_txt"]} صفحة يوميًا</strong> تقريبًا، أي حوالي <strong>{st["lines_per_day"]} سطرًا</strong> '
                     f'من مصحف المدينة (15 سطرًا في الصفحة)، و{st["pages_per_week_txt"]} صفحة في الأسبوع.')
        intro.append('الجدول بالأسفل يوضح ما ستحفظه في كل شهر بالسور والأجزاء، ويبدأ افتراضيًا من جزء عمّ ثم تبارك ثم قد سمع… '
                     'لأن السور القصيرة أسهل وتعطي دفعة في البداية، ويمكنك تغييره ليبدأ من الفاتحة والبقرة.')
    else:
        intro.append('حدد في كم سنة تريد أن تحفظ القرآن، وكم يومًا في الأسبوع ستحفظ، ومن أين تبدأ، وستحسب لك الأداة مقدار الحفظ اليومي '
                     'بالصفحات والأسطر، وتعطيك جدولًا شهريًا بالسور والأجزاء على مصحف المدينة.')
        intro.append('الخطة الواقعية هي التي تستمر عليها؛ ولذلك ابدأ بمقدار أقل مما تظن أنك تستطيعه، واجعل المراجعة أولًا.')
    tips = [
        'المراجعة قبل الجديد: خصص لمراجعة المحفوظ وقتًا أطول من وقت الحفظ الجديد.',
        'راجع آخر 5 صفحات حفظتها يوميًا، ووزّع ما قبلها على أيام الأسبوع.',
        'اجعل يومًا في الأسبوع بلا حفظ جديد، للتثبيت وتسميع حفظ الأسبوع كاملًا.',
        'سمّع على معلم أسبوعيًا؛ فالمعلم يكتشف الأخطاء التي لا تشعر بها.',
        'احفظ من مصحف واحد ثابت حتى تثبت صورة الصفحة في ذهنك.',
    ]
    faq = [
        (f'كم صفحة أحفظ يوميًا لحفظ القرآن في {P.HIFZ_PRESETS[y]}؟',
         f'حوالي {st["pages_per_day_txt"]} صفحة يوميًا ({st["lines_per_day"]} سطرًا) إذا حفظت 5 أيام في الأسبوع، '
         f'أي {st["pages_per_week_txt"]} صفحة أسبوعيًا من مصحف المدينة (604 صفحة).'),
        ('كم ساعة أحتاج يوميًا؟',
         f'للحفظ الجديد حوالي {st["minutes"]} دقيقة، ومثلها أو أكثر للمراجعة. تختلف المدة من شخص لآخر حسب العمر والخبرة.'),
        ('من أين أبدأ الحفظ؟',
         'كثير من الحفاظ يبدؤون من جزء عمّ ثم تبارك ثم قد سمع لأن سورها قصيرة، وآخرون يبدؤون من البقرة. الأداة تتيح الطريقتين؛ المهم أن تثبت على اتجاه واحد.'),
        ('كيف أراجع حتى لا أنسى؟',
         'راجع المحفوظ الجديد يوميًا، وقسّم القديم على دورة أسبوعية، واقرأ من محفوظك في الصلوات. وقد قال النبي ﷺ: «تعاهدوا القرآن، فوالذي نفسي بيده لهو أشد تفصيًا من الإبل في عُقُلها» (متفق عليه).'),
        ('ماذا لو تأخرت عن الخطة؟',
         'لا تضاعف الحفظ الجديد لتلحق. أعد حساب الخطة من الموضع الذي وصلت إليه بمدة أطول قليلًا، واحرص على الاستمرار.'),
    ]
    return {'h1': h1, 'title': title, 'meta': meta[:160], 'intro': intro, 'tips': tips, 'faq': faq, 'faq_ld': _faq_ld(faq),
            'stats': st, 'years': y}


def hifz_en(years=None):
    y = years or 3
    st = P.hifz_stats(y)
    if years:
        h1 = f'Quran Memorization Plan in {P.HIFZ_PRESETS_EN[y]}'
        title = f'{h1}: {st["pages_per_day_txt"]} Pages a Day | Monthly Schedule'
        meta = (f'Memorize the whole Quran in {P.HIFZ_PRESETS_EN[y].lower()}: {st["pages_per_day_txt"]} pages ({st["lines_per_day"]} lines) a day, '
                f'5 days a week, with a monthly surah schedule and revision tips.')
    else:
        h1 = 'Quran Memorization Planner (Hifz Calculator)'
        title = 'Quran Memorization Planner: How Many Pages a Day? Free Hifz Calculator | Al-Agmi'
        meta = ('Free hifz calculator: choose your time frame, memorization days per week and starting point, and get your daily '
                'amount and a monthly schedule by surah and juz.')
    intro = []
    if years:
        intro.append(f'To memorize the whole Quran in {P.HIFZ_PRESETS_EN[y].lower()}, memorizing 5 days a week, you need about '
                     f'<strong>{st["pages_per_day_txt"]} pages a day</strong>, which is around <strong>{st["lines_per_day"]} lines</strong> '
                     f'of the Madinah Mushaf (15 lines per page), or {st["pages_per_week_txt"]} pages a week.')
        intro.append('The schedule below shows what you will memorize each month by surah and juz. By default it starts from Juz\' Amma, '
                     'then Tabarak and Qad Sami\'a, because shorter surahs give quick early wins; you can switch it to start from Al-Fatihah and Al-Baqarah.')
    else:
        intro.append('Choose how many years you want to take, how many days a week you will memorize, and where you want to start. '
                     'The planner calculates your daily amount in pages and lines, and builds a monthly schedule by surah and juz.')
        intro.append('The best plan is the one you can keep. Start with a little less than you think you can manage, and put revision first.')
    tips = [
        'Revision before new memorization: give revision more time than new material.',
        'Revise the last 5 pages you memorized every day, and rotate older portions through the week.',
        'Keep one day a week free of new memorization, to consolidate and recite the whole week\'s portion.',
        'Recite to a teacher every week; a teacher catches mistakes you cannot hear yourself.',
        'Memorize from one Mushaf so your visual memory of each page stays consistent.',
    ]
    faq = [
        (f'How many pages a day to memorize the Quran in {P.HIFZ_PRESETS_EN[y].lower()}?',
         f'About {st["pages_per_day_txt"]} pages ({st["lines_per_day"]} lines) a day if you memorize 5 days a week, which is '
         f'{st["pages_per_week_txt"]} pages a week of the 604-page Madinah Mushaf.'),
        ('How much time do I need each day?',
         f'Roughly {st["minutes"]} minutes for new memorization, and as much or more for revision. It varies with age and experience.'),
        ('Where should I start memorizing?',
         'Many people start with Juz\' Amma, then Tabarak and Qad Sami\'a, because the surahs are short. Others start with Al-Baqarah. The planner supports both; the key is to stick to one direction.'),
        ('How do I revise so I don\'t forget?',
         'Revise new memorization daily, rotate older portions weekly, and recite what you know in your prayers. The Prophet ﷺ said: "Keep refreshing your knowledge of the Quran, for it escapes more readily than camels from their tethers" (al-Bukhari and Muslim).'),
        ('What if I fall behind the plan?',
         'Don\'t double your new memorization to catch up. Recalculate from where you are with a slightly longer time frame, and keep going.'),
    ]
    return {'h1': h1, 'title': title, 'meta': meta[:160], 'intro': intro, 'tips': tips, 'faq': faq, 'faq_ld': _faq_ld(faq),
            'stats': st, 'years': y}
