"""محتوى خاص بكل صفحة من صفحات الخطط الجاهزة (الختمة والحفظ).

كانت الصفحات الجاهزة متطابقة تقريبًا مع الصفحة الرئيسية للحاسبة، ولا يختلف فيها إلا الأرقام والجدول،
وده بيخليها «محتوى مكرر» في نظر جوجل وأدسنس. هنا لكل خطة قسم مكتوب لها وحدها: لمن تناسب، وكيف تُنفذ،
وأخطاؤها الخاصة. كل عنصر: (عنوان القسم، [فقرات HTML]).
"""

KHATMA_AR = {
    'ramadan': ('ختمة رمضان: كيف تجعلها تمشي مع يوم الصائم', [
        'يوم الصائم غير أي يوم آخر: سحور قبل الفجر، ونهار بلا طعام، وإفطار يأخذ جزءًا من المساء، ثم تراويح. ولذلك فإن أنجح طريقة لختمة رمضان أن توزع الجزء على <strong>أوقات تعرفها في يوم الصائم</strong>، لا على ساعة فارغة قد لا تأتي: صفحات بعد السحور والفجر وهي أهدأ أوقات اليوم، وصفحات في الظهيرة، وصفحات قبل المغرب حين يكون الطعام جاهزًا والدعاء مرجوًا، وصفحات بعد التراويح.',
        'واعلم أن الشهر قد يكون 29 يومًا، فاقرأ في الأسبوع الأول صفحة أو صفحتين زيادة كل يوم، حتى لا يبقى عليك جزء كامل في الليلة الأخيرة. وإذا أردت أن تفهم ما تقرأ، فاقرأ قبل جزء كل يوم ملخصه في سلسلة <a href="/ramadan/#juz-daily">ملخص جزء كل يوم في رمضان</a>، وفيها لكل جزء خطة قراءته على الصلوات وأسئلة تدبر للعائلة.',
        'ومن جعل ختمته في العشرين الأولى، وترك العشر الأواخر للقيام والدعاء والتدبر، فقد أحسن. ولمن يحتاج الاستعداد قبل الشهر، فهذه <a href="/blog/prepare-for-ramadan-with-quran-shaban/">خطة أربعة أسابيع في شعبان</a>.',
    ]),
    'ramadan-2-khatmas': ('ختمتان في رمضان: لمن تناسب وكيف تنظمها', [
        'ختمتان في الشهر تعني جزأين في اليوم، أي نحو ساعة ونصف من القراءة المتأنية. وهذا يناسب من عنده وقت: المتقاعد، والطالب في إجازته، ومن خفف عمله في رمضان، ومن اعتاد القراءة طوال العام فلن يكون الجزءان عليه صدمة.',
        'وأفضل تنظيم جربه كثيرون أن تكون إحدى الختمتين <strong>ختمة تدبر</strong> تقرؤها ببطء مع تفسير مختصر لآية أو آيتين كل يوم، والأخرى <strong>ختمة تلاوة</strong> بقراءة أسرع مع الحفاظ على الأحكام. فتجمع بين كثرة التلاوة وفهم المعنى، ولا تتحول الختمتان إلى سباق صفحات.',
        'ونصيحة مهمة: إذا كنت تقرأ لأول مرة بهذا المقدار، فابدأ في شعبان بجزء يوميًا لمدة أسبوعين على الأقل، وإلا فستتعب في الأسبوع الأول ويثقل عليك الورد. وإن تأخرت، فلا تتردد في أن تحول خطتك إلى ختمة ونصف، فالمداومة أحب إلى الله من الكثرة المنقطعة.',
    ]),
    'ramadan-3-khatmas': ('ثلاث ختمات في رمضان: خطة لأصحاب الوقت والهمة', [
        'ثلاث ختمات تعني ثلاثة أجزاء يوميًا، أي ختمة كل عشرة أيام، ونحو ساعتين إلى ثلاث من القراءة. وهذا يناسب الحفاظ الذين يقرؤون بسرعة متقنة، ومن تفرغ لرمضان، ومن اعتكف العشر الأواخر. أما من يقرأ ببطء أو ما زال يتعلم التلاوة، فختمة واحدة بتأنٍ خير له من ثلاث يسرع فيها حتى يُسقط الأحكام.',
        'وتقسيم مريح: جزء بعد الفجر، وجزء موزع على الظهر والعصر، وجزء بين المغرب والعشاء أو في قيام الليل. ومن كان يحفظ فليجعل جزءًا من الثلاثة في صلاته بالليل، فيجمع بين الختمة والمراجعة والقيام.',
        'واحذر أن يتحول الهدف إلى رقم. كان السلف يكثرون الختم في رمضان، لكنهم كانوا يقرؤون بالترتيل والخشوع. فإن وجدت قلبك غائبًا من السرعة، فخفف المقدار ولو صارت ختمتين، فالمقصود من القرآن أن يحيا به القلب.',
    ]),
    '3-days': ('الختم في ثلاثة أيام: أقل مدة ولمن تصلح', [
        'ثلاثة أيام هي أقل مدة للختم ذكرها النبي ﷺ لعبد الله بن عمرو رضي الله عنهما، ولذلك كرِه كثير من العلماء الختم في أقل منها في الأحوال العادية. وهي تعني نحو عشرة أجزاء في اليوم، أي ما يقارب سبع ساعات من القراءة، فلا تصلح إلا لحافظ متقن يقرأ بالحدر، أو لمعتكف تفرغ تمامًا.',
        'ومن أشهر استعمالاتها: المعتكف في العشر الأواخر من رمضان، والحافظ الذي يريد مراجعة شاملة قبل اختبار أو تسميع، وأيام الإجازات الطويلة لمن اعتاد كثرة القراءة. فإن لم تكن من هؤلاء، فاختر <a href="/quran/khatma/7-days/">الختم في أسبوع</a> أو <a href="/quran/khatma/10-days/">الختم في عشرة أيام</a>.',
        'وطريقة التقسيم المقترحة لثلاثة أيام: من الفاتحة إلى آخر التوبة في اليوم الأول، ومن يونس إلى آخر العنكبوت في الثاني، ومن الروم إلى الناس في الثالث، وهي قريبة من ثلث المصحف لكل يوم.',
    ]),
    '7-days': ('الختم في أسبوع: سنة الصحابة وتحزيب «فمي بشوق»', [
        'الختم في سبعة أيام هو ما أرشد إليه النبي ﷺ عبد الله بن عمرو حين قال: «فاقرأه في سبع ولا تزد على ذلك» (متفق عليه)، وكان كثير من الصحابة يختمون كل أسبوع. وكانوا يقسمون القرآن على سبعة أحزاب بالسور لا بالصفحات، ويجمعها قول العلماء: <strong>«فمي بشوق»</strong>، وكل حرف يدل على السورة التي يبدأ بها يوم:',
        '<strong>ف</strong>: الفاتحة (اليوم الأول من الفاتحة إلى آخر النساء)، <strong>م</strong>: المائدة (إلى آخر التوبة)، <strong>ي</strong>: يونس (إلى آخر النحل)، <strong>ب</strong>: بني إسرائيل أي الإسراء (إلى آخر الفرقان)، <strong>ش</strong>: الشعراء (إلى آخر يس)، <strong>و</strong>: والصافات (إلى آخر الحجرات)، <strong>ق</strong>: سورة ق (إلى آخر المصحف).',
        'ومزية هذا التحزيب أنك لا تقف في وسط سورة أبدًا، فتقرأ كل سورة كاملة بسياقها. أما الجدول بالأسفل فيقسم بالصفحات بالتساوي، فاختر ما يناسبك: التحزيب بالسور أقرب للسنة وأجمل للتدبر، والتقسيم بالصفحات أعدل في الوقت.',
    ]),
    '10-days': ('الختم في عشرة أيام: العشر الأواخر وعشر ذي الحجة', [
        'عشرة أيام مدة لها مواسم معروفة: <strong>العشر الأواخر من رمضان</strong> لمن أراد ختمة خاصة بليالي القدر، و<strong>العشر الأولى من ذي الحجة</strong> التي هي أفضل أيام الدنيا، ومن أعظم الأعمال فيها تلاوة القرآن. وتحتاج إلى ثلاثة أجزاء يوميًا تقريبًا.',
        'وفي العشر الأواخر يحسن أن تجعل جزءًا من الورد في قيام الليل إن كنت تحفظ، وأن تختم في ليلة وترية وتدعو عند الختم. وفي عشر ذي الحجة يمكنك أن تختم يوم عرفة أو قبله، فتجمع بين ختمة القرآن وصيام عرفة والدعاء فيه.',
        'وإن كانت ثلاثة أجزاء كثيرة عليك، فاجعل هدفك في هذه العشر ختمة الجزء الذي تحبه أو تحفظه مرات، أو اقرأ نصف القرآن، فالعبرة بإحياء الأيام الفاضلة لا بالرقم.',
    ]),
    '15-days': ('الختم في نصف شهر: ختمتان كل شهر طوال العام', [
        'الختم في خمسة عشر يومًا يعني جزأين يوميًا، وهو ورد كثير من الحفاظ والمعلمين طوال العام، لأنه يجعل المصحف كله يمر عليهم مرتين في الشهر، فيبقى محفوظهم حاضرًا. ولغير الحافظ هو ورد عالي الهمة يحتاج قرابة ساعة ونصف يوميًا.',
        'وأسهل تقسيم: جزء في الصباح وجزء في المساء، فيكون لك «ختمة نهار» و«ختمة ليل» تسيران معًا. ومن أراد أن يستعمله في رمضان، فهو نفسه خطة <a href="/quran/khatma/ramadan-2-khatmas/">ختمتين في رمضان</a>.',
        'وإن كنت تحفظ، فاقرأ الجزأين من حفظك قدر استطاعتك، وارجع إلى المصحف عند كل تردد، وعلّم على مواضع الخطأ لتراجعها. فبهذا يصير وردك تلاوة ومراجعة معًا.',
    ]),
    '20-days': ('الختم في عشرين يومًا: لتفرغ العشر الأواخر للقيام', [
        'عشرون يومًا تعني جزءًا ونصفًا يوميًا. وأجمل استعمال لها في رمضان: أن تختم في العشرين الأولى، ثم تجعل العشر الأواخر لختمة ثانية أبطأ بالتدبر، أو للقيام والدعاء والاعتكاف دون ضغط ورد كبير.',
        'وتناسب أيضًا الإجازات القصيرة، كإجازة منتصف العام الدراسي، أو أيام الحج والعمرة لمن يريد أن يختم في سفره. ويسهل تقسيمها على الصلوات: ست صفحات بعد كل صلاة.',
        'ونصيحة لمن يبدأ هذه الخطة: إذا كنت تقرأ جزءًا واحدًا عادة، فارفع المقدار تدريجيًا خلال الأيام الثلاثة الأولى، ولا تبدأ بالجزء والنصف من أول يوم حتى لا تتعب.',
    ]),
    '40-days': ('الختم في أربعين يومًا: خطوة بين المبتدئ والمنتظم', [
        'أربعون يومًا تعني نصف جزء ونصف ربع تقريبًا يوميًا، أي ثلاث صفحات بعد كل صلاة. وهي مناسبة لمن يريد أن يتدرج: كان لا يختم، ويريد أن يصل يومًا إلى ختمة شهرية، فيبدأ بأربعين يومًا ثم ينقص المدة بعد ذلك.',
        'وننبه إلى أنه لا يثبت فضل خاص لختم القرآن في أربعين يومًا بعينها، وإنما هي مدة مناسبة في الوقت والجهد، فلا تعتقد فيها فضيلة مخصوصة. والمهم الاستمرار.',
        'ومن الأفكار الجميلة مع هذه الخطة أن تقرأ مع كل ورد تفسير صفحة واحدة، فتنتهي بعد أربعين يومًا وقد قرأت القرآن كاملًا وفهمت جزءًا كبيرًا منه.',
    ]),
    '60-days': ('الختم في شهرين: ختمة المتعلم ومن يقرأ ببطء', [
        'شهران يعنيان نصف جزء يوميًا، أي صفحتين بعد كل صلاة. وهي خطة مثالية لمن ما زال يتعلم القراءة الصحيحة، أو من يقرأ ببطء لأن العربية ليست لغته الأولى، فيقرأ بتأنٍ ويصحح أخطاءه دون أن يشعر بضغط.',
        'ويمكن أن تجعلها <strong>ختمة تعلم</strong>: تستمع إلى ورد اليوم من قارئ متقن قبل أن تقرأه، ثم تقرؤه، ثم تراجع تفسير آية منه. وبعد شهرين تكون قد ختمت وتحسنت قراءتك ملحوظًا.',
        'وتناسب كذلك الأم المشغولة والعامل بساعات طويلة، فصفحتان بعد كل صلاة لا تأخذ أكثر من خمس دقائق. ومن أراد ختمة في رمضان بهذا المقدار، فليقرأ نصف القرآن في رمضان ونصفه في شوال.',
    ]),
    '90-days': ('الختم في ثلاثة شهور: ختمة الفهم والتفسير', [
        'ثلاثة شهور تعني نحو سبع صفحات يوميًا، أي ربع ساعة. وهي مدة مثالية لمن يريد أن يجمع الختمة مع <strong>قراءة تفسير مختصر</strong> للقرآن كاملًا: تقرأ الصفحات ثم تفسيرها في نصف ساعة يوميًا، فتختم القرآن وتفسيره معًا في فصل واحد من السنة.',
        'وتناسب أيضًا الختمة العائلية: تقرأ الأسرة كل يوم ورد الخطة معًا بعد المغرب، كل فرد يقرأ صفحة، والأب أو الأم يشرح آية. وفي نهاية الثلاثة شهور تحتفل الأسرة بختمة جماعية.',
        'ومن يريد أن يجعلها ورده الدائم، فثلاثة شهور تعني أربع ختمات في السنة، وهذا خير كثير مع قلة الوقت اليومي.',
    ]),
    '1-year': ('الختم في سنة: صفحتان يوميًا تغيران حياتك', [
        'ختم القرآن في سنة يحتاج أقل من صفحتين في اليوم، أي أربع دقائق تقريبًا. وهذه أسهل خطة على الإطلاق، وتناسب من لم يختم القرآن في حياته، ومن أسلم حديثًا، ومن ابتعد عن القرآن ويريد أن يعود بخطوة صغيرة لا يتركها.',
        'وسر هذه الخطة أنها <strong>صغيرة بما يكفي ألا تتركها أبدًا</strong>. قال النبي ﷺ: «أحب الأعمال إلى الله أدومها وإن قل» (متفق عليه). صفحتان بعد الفجر كل يوم، ولو في السفر والمرض والانشغال، تصنع عادة تبقى معك العمر كله.',
        'وكثيرون يبدؤون بها ثم يجدون أنفسهم يقرؤون أكثر دون تخطيط. فإن وجدت الرغبة، فانتقل إلى <a href="/quran/khatma/90-days/">الختم في ثلاثة شهور</a>، ثم شهرين، حتى تصل إلى ختمة شهرية.',
    ]),
}

KHATMA_EN = {
    'ramadan': ('A Ramadan khatam that fits a fasting day', [
        'A fasting day is unlike any other: suhoor before dawn, a day without food, an iftar that takes part of the evening, then Tarawih. The most successful Ramadan khatam is split across <strong>moments you already know in a fasting day</strong>, not a free hour that may never come: pages after suhoor and Fajr, the calmest time; pages at midday; pages just before Maghrib, when the food is ready and du\'a is hoped to be answered; and pages after Tarawih.',
        'Remember the month may be 29 days, so read a page or two extra each day in the first week, so you are not left with a whole juz on the last night. To understand what you read, spend five minutes on each day\'s <a href="/en/ramadan/#juz-daily">juz summary</a> before reading it.',
        'If you finish your khatam in the first twenty days and keep the last ten nights for night prayer, du\'a and reflection, you have done well. To get ready beforehand, see our <a href="/blog/prepare-for-ramadan-shaban-english/">four-week plan for Sha\'ban</a>.',
    ]),
    'ramadan-2-khatmas': ('Two khatams in Ramadan: who it suits and how to organise it', [
        'Two khatams in a month means two juz a day, about an hour and a half of careful reading. It suits people with time: retirees, students on holiday, those who reduce their work in Ramadan, and anyone who reads all year so two juz will not be a shock.',
        'A pattern many people find works well is to make one khatam a <strong>reflection khatam</strong>, read slowly with a short tafsir of one or two verses each day, and the other a <strong>recitation khatam</strong>, read faster while keeping the rules of tajweed. You combine abundant recitation with understanding, and the two khatams never become a race.',
        'If you have never read this much before, start in Sha\'ban with one juz a day for at least two weeks; otherwise the first week will exhaust you. And if you fall behind, do not hesitate to make it one and a half khatams: consistency is more beloved to Allah than quantity that stops.',
    ]),
    'ramadan-3-khatmas': ('Three khatams in Ramadan: for those with time and energy', [
        'Three khatams means three juz a day, a khatam every ten days, and two to three hours of reading. It suits hafiz who read quickly and accurately, people who have freed their time for Ramadan, and those in i\'tikaf in the last ten nights. If you still read slowly or are learning, one careful khatam is better for you than three rushed ones that drop the rules.',
        'A comfortable split: one juz after Fajr, one spread across Dhuhr and Asr, and one between Maghrib and Isha or in night prayer. If you have memorized, recite one of the three in your night prayer, combining the khatam with revision and qiyam.',
        'Beware of turning the goal into a number. The early Muslims read a great deal in Ramadan, but with tartil and humility. If speed is pulling your heart away, reduce the amount, even to two khatams; the purpose of the Quran is to bring the heart to life.',
    ]),
    '3-days': ('Finishing in three days: the shortest period, and who it is for', [
        'Three days is the shortest period for a khatam that the Prophet ﷺ mentioned to \'Abdullah ibn \'Amr, which is why many scholars disliked finishing in less in normal circumstances. It means about ten juz a day, close to seven hours of reading, so it only suits a hafiz reading at a quick but correct pace, or someone in i\'tikaf who has freed all their time.',
        'Its best-known uses are i\'tikaf in the last ten nights of Ramadan, a hafiz doing a complete review before an exam or recitation, and long holidays for those used to reading a lot. If none of these is you, choose <a href="/en/quran/khatam-planner/7-days/">finishing in a week</a> or <a href="/en/quran/khatam-planner/10-days/">in ten days</a> instead.',
        'A suggested split by surahs: Al-Fatiha to the end of At-Tawbah on day one, Yunus to the end of Al-\'Ankabut on day two, and Ar-Rum to An-Nas on day three, roughly a third of the mushaf each day.',
    ]),
    '7-days': ('Finishing in a week: the practice of the Companions', [
        'Seven days is what the Prophet ﷺ advised \'Abdullah ibn \'Amr: "Recite it in seven and do not do more than that" (al-Bukhari and Muslim), and many Companions finished the Quran weekly. They divided it into seven portions by surah rather than by page, remembered by the Arabic mnemonic <strong>"fami bi-shawq"</strong>, each letter marking the surah that begins a day:',
        '<strong>F</strong>: Al-Fatiha (day one, to the end of An-Nisa\'); <strong>M</strong>: Al-Ma\'idah (to the end of At-Tawbah); <strong>Y</strong>: Yunus (to the end of An-Nahl); <strong>B</strong>: Bani Isra\'il, i.e. Al-Isra\' (to the end of Al-Furqan); <strong>Sh</strong>: Ash-Shu\'ara\' (to the end of Ya-Sin); <strong>W</strong>: Was-Saffat (to the end of Al-Hujurat); <strong>Q</strong>: Surah Qaf (to the end of the mushaf).',
        'The beauty of this division is that you never stop in the middle of a surah, so you read every surah whole, in context. The table below divides by pages equally instead. Choose what suits you: dividing by surahs is closer to the early practice and better for reflection; dividing by pages is fairer on time.',
    ]),
    '10-days': ('Finishing in ten days: the last ten of Ramadan and the first ten of Dhul-Hijjah', [
        'Ten days has well-known seasons: <strong>the last ten nights of Ramadan</strong>, for a khatam dedicated to the nights of Laylat al-Qadr, and <strong>the first ten days of Dhul-Hijjah</strong>, the best days of the year, in which reciting the Quran is among the greatest deeds. It needs about three juz a day.',
        'In the last ten nights, recite part of your portion in night prayer if you have memorized, and aim to complete the khatam on an odd night with du\'a. In Dhul-Hijjah, you can finish on or before the Day of \'Arafah, combining the khatam with fasting \'Arafah and making du\'a.',
        'If three juz a day is too much, make your goal for these ten days half the Quran, or repeated readings of a juz you love or have memorized. What matters is filling the blessed days, not the number.',
    ]),
    '15-days': ('Finishing in fifteen days: two khatams a month, all year', [
        'Finishing in fifteen days means two juz a day, the regular portion of many hafiz and teachers throughout the year, because the whole mushaf passes through their recitation twice a month and their memorization stays fresh. For non-hafiz, it is an ambitious portion of about an hour and a half a day.',
        'The easiest split is one juz in the morning and one in the evening, giving you a "day khatam" and a "night khatam" running together. Used in Ramadan, it is the same as the <a href="/en/quran/khatam-planner/ramadan-2-khatmas/">two-khatam Ramadan plan</a>.',
        'If you have memorized, recite as much of the two juz from memory as you can, check the mushaf whenever you hesitate, and mark your mistakes for review. Your portion then becomes recitation and revision at once.',
    ]),
    '20-days': ('Finishing in twenty days: freeing the last ten nights', [
        'Twenty days means a juz and a half a day. Its most beautiful use in Ramadan is to finish in the first twenty days and keep the last ten for a slower second reading with reflection, or for night prayer, du\'a and i\'tikaf without the pressure of a large daily portion.',
        'It also suits short holidays, such as a mid-year school break, or Hajj and \'Umrah trips for those who want to finish while travelling. It splits easily across the prayers: six pages after each.',
        'If you normally read one juz a day, raise the amount gradually over the first three days rather than starting with a juz and a half on day one.',
    ]),
    '40-days': ('Finishing in forty days: a step between beginner and regular', [
        'Forty days means fifteen pages a day, three pages after each prayer. It suits anyone building up gradually: someone who has not been finishing the Quran and wants to reach a monthly khatam one day can start with forty days and shorten the period later.',
        'Note that no special virtue is established for finishing the Quran in exactly forty days; it is simply a manageable period in time and effort, so do not attach a particular merit to it. What matters is consistency.',
        'A lovely idea with this plan is to read the tafsir of one page with each portion, so that after forty days you have read the whole Quran and understood a large part of it.',
    ]),
    '60-days': ('Finishing in two months: a learner\'s khatam', [
        'Two months means half a juz a day, two pages after each prayer. It is ideal for those still learning to read correctly, or who read slowly because Arabic is not their first language: you can read carefully and fix mistakes without pressure.',
        'Make it a <strong>learning khatam</strong>: listen to the day\'s portion from a skilled reciter before reading it, then read it, then look up the tafsir of one verse. After two months you will have finished and your reading will have improved noticeably.',
        'It also suits busy parents and people working long hours, since two pages after each prayer takes no more than five minutes. In Ramadan, it means reading half the Quran in Ramadan and the other half in Shawwal.',
    ]),
    '90-days': ('Finishing in three months: a khatam with understanding', [
        'Three months means about seven pages a day, roughly fifteen minutes. It is ideal for combining your khatam with <strong>a short tafsir of the whole Quran</strong>: read the pages, then their explanation, in half an hour a day, and finish the Quran and its meaning together in one season of the year.',
        'It also works well as a family khatam: the family reads the day\'s portion together after Maghrib, each person reading a page while a parent explains a verse, and celebrates together at the end of three months.',
        'As a permanent routine, three months means four khatams a year, which is a great deal of good for very little daily time.',
    ]),
    '1-year': ('Finishing in a year: two pages a day that can change your life', [
        'Finishing the Quran in a year takes less than two pages a day, about four minutes. It is the easiest plan of all, and suits anyone who has never finished the Quran, new Muslims, and anyone who has drifted away and wants to return with a step small enough never to drop.',
        'The secret of this plan is that it is <strong>small enough that you never stop</strong>. The Prophet ﷺ said: "The most beloved deeds to Allah are the most consistent, even if small" (al-Bukhari and Muslim). Two pages after Fajr every day, while travelling, ill or busy, builds a habit that stays for life.',
        'Many people start here and find themselves reading more without planning to. When that happens, move up to <a href="/en/quran/khatam-planner/90-days/">three months</a>, then two, until you reach a monthly khatam.',
    ]),
}

HIFZ_AR = {
    1: ('حفظ القرآن في سنة: خطة التفرغ الكامل', [
        'حفظ القرآن في سنة واحدة يعني أكثر من صفحتين جديدتين يوميًا خمسة أيام في الأسبوع، ومعها مراجعة تكبر كل شهر حتى تصل في آخر السنة إلى أجزاء يوميًا. وهذا لا يناسب إلا <strong>المتفرغ</strong>: طالب في سنة تفرغ أو إجازة طويلة، أو من ترك عمله لهذا الهدف، بمعدل أربع إلى ست ساعات يوميًا.',
        'ولا ننصح بها أبدًا دون معلم يسمع لك كل يوم، لأن السرعة تُخفي الأخطاء، والخطأ الذي يُحفظ مرة يصعب تصحيحه. وأهم ما فيها نظام المراجعة: من يحفظ صفحتين يوميًا دون مراجعة قوية سينسى نصف ما حفظ قبل أن يكمل.',
        'وإن بدأت بها ووجدتها ثقيلة، فلا تعتبر ذلك فشلًا، بل حوّل خطتك إلى <a href="/quran/hifz-plan/2-years/">سنتين</a>، فالحافظ المتقن في سنتين أفضل من حافظ متعجل في سنة.',
    ]),
    2: ('حفظ القرآن في سنتين: خطة الطالب الجاد', [
        'سنتان تعنيان أكثر من صفحة يوميًا، أي نحو سبعة عشر سطرًا. وهي خطة مناسبة للطالب في المرحلة الثانوية أو الجامعة الذي يخصص للقرآن ساعتين يوميًا، أو للمتقاعد، أو لمن يعمل عملًا مرنًا.',
        'والسنة الأولى أسهل غالبًا لأن المراجعة قليلة، والسنة الثانية أصعب لأن المحفوظ صار كبيرًا. ولذلك اجعل من البداية نظامًا ثابتًا: ورد جديد، وورد قريب من آخر عشرين صفحة، وورد بعيد يدور على كل ما حفظت. وتجد تفصيل ذلك في <a href="/blog/how-to-memorize-quran-plan/">خطة حفظ القرآن وتثبيته</a>.',
        'ومن أفضل ما يعين على هذه الخطة أن تصلي بما تحفظ في السنن وقيام الليل، فالصلاة أقوى تثبيت، وتكشف لك مواضع الضعف قبل أن تتسع.',
    ]),
    4: ('حفظ القرآن في أربع سنوات: خطة الموظف والأم', [
        'أربع سنوات تعني تسعة أسطر يوميًا تقريبًا، أي أقل من صفحة. وهذه خطة واقعية لمن يعمل بدوام كامل أو للأم التي عندها أطفال، لأن الحفظ الجديد لا يأخذ أكثر من عشرين دقيقة، والمراجعة يمكن توزيعها على الصلوات والطريق.',
        'وأهم سر فيها <strong>الثبات</strong>: تسعة أسطر كل يوم عمل لمدة أربع سنوات أنفع من صفحتين يومًا وانقطاع أسبوعًا. واجعل يومي العطلة للمراجعة فقط، فلا تضيف جديدًا قبل أن تثبت القديم.',
        'ومع طول المدة، احتفل بكل جزء تنهيه، وسمّعه على معلم أو صديق، فالأهداف الصغيرة تحفظ لك الحماس. وتجد أفكارًا كثيرة لمثل ظروفك في <a href="/blog/hifz-for-busy-mothers/">حفظ القرآن للأم المشغولة</a>.',
    ]),
    5: ('حفظ القرآن في خمس سنوات: الطريق الهادئ للأطفال والكبار', [
        'خمس سنوات تعني سبعة أسطر يوميًا، وهي أهدأ الخطط وأسهلها. وتناسب <strong>الأطفال من سن سبع سنوات</strong> مع حلقة يومية قصيرة، و<strong>كبار السن</strong> ومن يجد صعوبة في الحفظ، ومن يريد أن يحفظ مع فهم المعاني وقراءة التفسير.',
        'وللطفل خاصة، فإن سبعة أسطر في اليوم مع مراجعة لطيفة تجعله يختم الحفظ قبل أن يصل إلى المرحلة الثانوية، دون أن يكره القرآن من الضغط. وابدأ معه من جزء عمّ لأن سوره قصيرة ويرى إنجازه سريعًا، ويمكنه أن يبدأ بـ<a href="/quran/juz-amma-challenge/">تحدي جزء عمّ في 30 يوم</a>.',
        'ولا تستهن بهذه المدة. فمن حفظ سبعة أسطر يوميًا خمس سنوات حتى ختم، أفضل بكثير ممن بدأ بخطة سريعة وتوقف بعد أشهر. والمهم أن تبدأ اليوم.',
    ]),
}

HIFZ_EN = {
    1: ('Memorizing the Quran in one year: a full-time plan', [
        'Memorizing the whole Quran in a year means more than two new pages a day, five days a week, plus revision that grows every month until it reaches several juz a day by the end. It only suits someone <strong>studying full time</strong>: a gap year, a long break, or someone who has stepped away from work for this goal, at four to six hours a day.',
        'We never recommend it without a teacher who listens to you daily, because speed hides mistakes, and a mistake memorized once is hard to undo. The heart of this plan is revision: anyone memorizing two pages a day without strong review will forget half before finishing.',
        'If you start and find it too heavy, that is not failure. Switch to <a href="/en/quran/memorization-planner/2-years/">two years</a>; a solid hafiz in two years is better than a rushed one in one.',
    ]),
    2: ('Memorizing the Quran in two years: a plan for the committed student', [
        'Two years means a little more than a page a day, about seventeen lines. It suits a secondary-school or university student who gives the Quran two hours a day, a retiree, or someone with flexible work.',
        'The first year is usually easier because there is little to review; the second is harder because your memorization has grown. So set up a fixed system from the start: new memorization, recent review of your last twenty pages, and distant review cycling through everything you know. Our <a href="/blog/quran-revision-system-english/">Quran revision system</a> explains how.',
        'One of the best supports for this plan is praying with what you memorize in your sunnah prayers and night prayer. Prayer is the strongest way to fix memorization, and it shows your weak spots before they grow.',
    ]),
    4: ('Memorizing the Quran in four years: a plan for workers and parents', [
        'Four years means about nine lines a day, less than a page. It is realistic for full-time workers and parents of young children, because new memorization takes no more than twenty minutes and revision can be spread across the prayers and the commute.',
        'Its secret is <strong>consistency</strong>: nine lines every working day for four years achieves more than two pages one day and nothing for a week. Keep your days off for revision only, and never add new material until the old is secure.',
        'Over a long journey, celebrate every juz you finish by reciting it to a teacher or friend; small milestones keep your motivation alive.',
    ]),
    5: ('Memorizing the Quran in five years: the gentle path for children and adults', [
        'Five years means about seven lines a day, the calmest and easiest plan. It suits <strong>children from about age seven</strong> with a short daily lesson, <strong>older adults</strong> and anyone who finds memorizing hard, and those who want to memorize while studying the meanings.',
        'For children especially, seven lines a day with gentle revision lets them finish before secondary school without coming to dislike the Quran through pressure. Start with Juz Amma, whose short surahs give quick wins, perhaps with our <a href="/en/quran/juz-amma-challenge/">30-day Juz Amma challenge</a>.',
        'Do not underestimate this pace. Someone who memorizes seven lines a day for five years and finishes is far better off than someone who starts a fast plan and stops after a few months. What matters is starting today.',
    ]),
}


def for_khatma(slug, en=False):
    return (KHATMA_EN if en else KHATMA_AR).get(slug)


def for_hifz(years, en=False):
    return (HIFZ_EN if en else HIFZ_AR).get(years)
