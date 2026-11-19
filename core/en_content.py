"""English content for the /en/ version of the public pages.
Same programmes and facts as core/site_content.py (the Arabic source of truth), translated.
If you change a programme in site_content.py, update its English twin here too."""

STANDARD_SCHEDULE = [('8 classes', '30 minutes'), ('12 classes', '30 minutes'), ('8 classes', '60 minutes')]

PROGRAMS = [
    {
        'slug': 'nourania', 'kind': 'Package', 'name': 'Noorani Beginnings',
        'audience': 'For children aged 6 and up',
        'summary': 'Choose the number of classes that suits your child, with full flexibility.',
        'sections': [
            ('What is included', [
                'Simple explanations of the meanings of the verses, suited to a child',
                'Fun, interactive learning games',
                'Basics of Islamic belief and the life of the Prophet ﷺ',
                'Daily homework to lock in memorisation',
                'Memorisation with Tajweed and correct oral transmission (talqeen)',
            ]),
        ],
        'tip': 'We suggest 40-minute classes for young children',
        'schedule': STANDARD_SCHEDULE,
    },
    {
        'slug': 'ghiras', 'kind': 'Package', 'name': 'Good Seedlings (Recitation Correction)',
        'audience': 'For improving recitation and fixing Tajweed mistakes',
        'summary': 'Helps the student recite the Quran correctly, free of mistakes.',
        'sections': [
            ('What is included', [
                'Recitation correction directly from the Mushaf',
                'Hands-on practice of letter articulation points and qualities',
                'Review of each student\'s own mistakes and pronunciation analysis',
                'Regular assessment and a completion certificate',
            ]),
            ('Who it is for', [
                'Anyone who reads the Quran and wants to correct their recitation',
                'Anyone who struggles with pronunciation or the lengths of madd',
            ]),
        ],
        'schedule': STANDARD_SCHEDULE,
    },
    {
        'slug': 'himma', 'kind': 'Package', 'name': 'High Ambition',
        'audience': 'For students aged 10 to 15',
        'summary': 'Memorise the Quran step by step, comfortably, with close follow-up.',
        'sections': [
            ('What is included', [
                'Sessions for new memorisation and revision',
                'The teacher checks the daily portion (wird)',
                'Islamic belief, Seerah and authentic hadith',
                'Weekly performance follow-up and progress reports',
                'Highly experienced memorisation teachers',
                'Flexible study times',
            ]),
        ],
        'schedule': STANDARD_SCHEDULE,
    },
    {
        'slug': 'sufaraa', 'kind': 'Package', 'name': 'Ambassadors of the Quran',
        'audience': 'A programme designed for adults',
        'summary': 'Memorise the Quran at a steady pace with an organised plan that fits your time.',
        'sections': [
            ('What is included', [
                'Recite your new memorisation and revise the old',
                'Polish your reading, letter articulation and Tajweed rules',
                'A flexible memorisation plan that fits your daily schedule',
                'Comfortable one-to-one online sessions',
                'Close follow-up and regular assessment',
            ]),
            ('Who it is for', [
                'Adults who want to start memorising from the beginning',
                'Those who want to complete what they started',
            ]),
        ],
        'schedule': STANDARD_SCHEDULE,
    },
    {
        'slug': 'nour-albayan', 'kind': 'Course', 'name': 'Noor Al-Bayan',
        'audience': 'Learn to read Arabic and the Quran correctly and clearly',
        'summary': ('A complete foundation course in reading Arabic correctly, following a clear step-by-step '
                    'method that takes the learner from recognising letters to reading words and sentences fluently.'),
        'sections': [
            ('Course goals', [
                'Read the Arabic letters correctly',
                'Master the short and long vowels',
                'Join letters together to form words',
                'Improve pronunciation and articulation points',
                'Build a strong foundation for reading Arabic and the Quran',
            ]),
            ('Course content', [
                'The Arabic letters and their shapes',
                'Short vowels: fatha, damma and kasra',
                'Long vowels (alif, waw and ya)',
                'Tanween, sukoon and shadda',
                'Joining letters into words',
                'Practical reading exercises',
            ]),
            ('Why this course', [
                'A clear, easy, gradual method',
                'Continuous practical application',
                'Focus on understanding, not memorising alone',
                'Noticeable results in a short time, God willing',
            ]),
        ],
        'schedule': [('Class', '40 minutes')],
    },
    {
        'slug': 'arbaeen', 'kind': 'Course', 'name': 'An-Nawawi\'s Forty Hadith',
        'audience': 'A structured study of the foundations of the Sunnah',
        'summary': ('A foundational study of the hadith collected by Imam Yahya ibn Sharaf An-Nawawi (may Allah have mercy on him), '
                    'which set out major principles of the religion.'),
        'sections': [
            ('Course goals', [
                'Understand the forty hadith correctly and soundly',
                'Explain the general principles and objectives drawn from them',
                'Practise deriving lessons and linking the texts together',
                'A balanced, moderate approach to understanding the Sunnah',
                'A solid base for beginner students of knowledge',
                'Written and practical exercises after every lesson',
            ]),
            ('Why this course', [
                'Built on the texts of the hadith themselves',
                'Combines memorisation, understanding and analysis',
                'A gradual path suited to beginners',
                'Simple explanation without losing accuracy',
                'Links each hadith to daily life and conduct',
                'Suitable for students of knowledge and non-specialists alike',
            ]),
        ],
        'schedule': [('Class', '40 minutes')],
    },
]

STEPS = [
    ('Book your free class', 'Fill in a short form or message us on WhatsApp, and tell us the student\'s age and level.'),
    ('Try it with the teacher', 'A free online trial class where we assess the level and get to know the student.'),
    ('Start your plan', 'Choose the package and times that suit your time zone, and start memorising with ongoing follow-up.'),
]

FEATURES = [
    ('One-to-one classes', 'The student learns alone with the teacher, for full focus and discipline.'),
    ('Certified teachers', 'Teachers hold ijazah certificates in the Quran and have experience teaching children and adults.'),
    ('From any country', 'Book from anywhere in the world and pick a time that suits your time zone.'),
    ('Flexible timing', 'Choose the time that suits you and change it in coordination with our team.'),
    ('Monthly reports', 'A written report every month on the student\'s level, strengths and next steps.'),
    ('All ages', 'Programmes for children from age 6, for teenagers and for adults.'),
    ('Help with memorisation', 'We help the student overcome any difficulty with memorising or revising.'),
    ('Completion certificates', 'A certificate at the end of every level and memorisation stage.'),
]

FAQ = [
    ('Can I book from outside Egypt?',
     'Yes. All classes are fully online, so students from any country can book a free trial class and choose a time that fits their own time zone, in coordination with our team.'),
    ('Is the first class free?',
     'Yes. Every new student gets a completely free trial class to try the service before subscribing.'),
    ('How do I book?',
     'Click "Book a free class", or contact us through the contact page or WhatsApp, and we will agree on the right package and time with you.'),
    ('Who are the packages for?',
     'We have packages for children from age 6, for students aged 10 to 15 and for adults, plus specialised courses such as Noor Al-Bayan and An-Nawawi\'s Forty Hadith.'),
    ('Are the teachers qualified?',
     'All of our teachers hold ijazah certificates in the Holy Quran and have wide experience teaching the Quran to children and adults.'),
    ('Do I need to speak Arabic?',
     'No. Tell us your language and level when you book, and we will match you with a suitable teacher and start from where you are, including learning to read Arabic letters from scratch with Noor Al-Bayan.'),
    ('How do I follow my child\'s progress?',
     'Every student has an account in the student portal showing class times and monthly reports, and can message the teacher in the in-platform chat, supervised by our team.'),
]


def faq_schema():
    return {
        '@context': 'https://schema.org', '@type': 'FAQPage', 'inLanguage': 'en',
        'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQ],
    }


def courses_schema(site_url):
    items = []
    for i, p in enumerate(PROGRAMS, start=1):
        items.append({
            '@type': 'ListItem', 'position': i,
            'item': {
                '@type': 'Course',
                'name': p['name'],
                'description': f"{p['audience']}. {p['summary']}",
                'url': f"{site_url}/en/pricing/#{p['slug']}",
                'inLanguage': 'en',
                'provider': {'@type': 'EducationalOrganization', 'name': 'Al-Agmi Quran Academy', 'sameAs': site_url + '/'},
                'hasCourseInstance': {'@type': 'CourseInstance', 'courseMode': 'online',
                                      'courseWorkload': 'PT' + ('40M' if p['kind'] == 'Course' else '30M')},
                'offers': {'@type': 'Offer', 'category': 'Paid', 'availability': 'https://schema.org/InStock'},
            },
        })
    return {'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'Online Quran memorisation packages and courses', 'itemListElement': items}


# أسماء السور بالإنجليزي (نقل حرفي + المعنى) لصفحة /en/quran/
SURAH_EN = [
    ('Al-Fatihah', 'The Opening'), ('Al-Baqarah', 'The Cow'), ('Aal-Imran', 'The Family of Imran'),
    ('An-Nisa', 'The Women'), ('Al-Ma\'idah', 'The Table Spread'), ('Al-An\'am', 'The Cattle'),
    ('Al-A\'raf', 'The Heights'), ('Al-Anfal', 'The Spoils of War'), ('At-Tawbah', 'The Repentance'),
    ('Yunus', 'Jonah'), ('Hud', 'Hud'), ('Yusuf', 'Joseph'), ('Ar-Ra\'d', 'The Thunder'),
    ('Ibrahim', 'Abraham'), ('Al-Hijr', 'The Rocky Tract'), ('An-Nahl', 'The Bee'),
    ('Al-Isra', 'The Night Journey'), ('Al-Kahf', 'The Cave'), ('Maryam', 'Mary'), ('Ta-Ha', 'Ta-Ha'),
    ('Al-Anbiya', 'The Prophets'), ('Al-Hajj', 'The Pilgrimage'), ('Al-Mu\'minun', 'The Believers'),
    ('An-Nur', 'The Light'), ('Al-Furqan', 'The Criterion'), ('Ash-Shu\'ara', 'The Poets'),
    ('An-Naml', 'The Ant'), ('Al-Qasas', 'The Stories'), ('Al-Ankabut', 'The Spider'),
    ('Ar-Rum', 'The Romans'), ('Luqman', 'Luqman'), ('As-Sajdah', 'The Prostration'),
    ('Al-Ahzab', 'The Confederates'), ('Saba', 'Sheba'), ('Fatir', 'The Originator'), ('Ya-Sin', 'Ya-Sin'),
    ('As-Saffat', 'Those Ranged in Ranks'), ('Sad', 'Sad'), ('Az-Zumar', 'The Groups'),
    ('Ghafir', 'The Forgiver'), ('Fussilat', 'Explained in Detail'), ('Ash-Shura', 'The Consultation'),
    ('Az-Zukhruf', 'The Ornaments of Gold'), ('Ad-Dukhan', 'The Smoke'), ('Al-Jathiyah', 'The Kneeling'),
    ('Al-Ahqaf', 'The Sand Dunes'), ('Muhammad', 'Muhammad'), ('Al-Fath', 'The Victory'),
    ('Al-Hujurat', 'The Rooms'), ('Qaf', 'Qaf'), ('Adh-Dhariyat', 'The Winnowing Winds'),
    ('At-Tur', 'The Mount'), ('An-Najm', 'The Star'), ('Al-Qamar', 'The Moon'),
    ('Ar-Rahman', 'The Most Merciful'), ('Al-Waqi\'ah', 'The Inevitable Event'), ('Al-Hadid', 'The Iron'),
    ('Al-Mujadilah', 'The Pleading Woman'), ('Al-Hashr', 'The Gathering'),
    ('Al-Mumtahanah', 'The Woman Examined'), ('As-Saff', 'The Ranks'), ('Al-Jumu\'ah', 'Friday'),
    ('Al-Munafiqun', 'The Hypocrites'), ('At-Taghabun', 'Mutual Loss and Gain'), ('At-Talaq', 'Divorce'),
    ('At-Tahrim', 'The Prohibition'), ('Al-Mulk', 'The Dominion'), ('Al-Qalam', 'The Pen'),
    ('Al-Haqqah', 'The Reality'), ('Al-Ma\'arij', 'The Ascending Stairways'), ('Nuh', 'Noah'),
    ('Al-Jinn', 'The Jinn'), ('Al-Muzzammil', 'The Enwrapped One'), ('Al-Muddaththir', 'The Cloaked One'),
    ('Al-Qiyamah', 'The Resurrection'), ('Al-Insan', 'Man'), ('Al-Mursalat', 'Those Sent Forth'),
    ('An-Naba', 'The Great News'), ('An-Nazi\'at', 'Those Who Pull Out'), ('Abasa', 'He Frowned'),
    ('At-Takwir', 'The Folding Up'), ('Al-Infitar', 'The Cleaving'), ('Al-Mutaffifin', 'The Defrauders'),
    ('Al-Inshiqaq', 'The Splitting Open'), ('Al-Buruj', 'The Constellations'), ('At-Tariq', 'The Night Comer'),
    ('Al-A\'la', 'The Most High'), ('Al-Ghashiyah', 'The Overwhelming Event'), ('Al-Fajr', 'The Dawn'),
    ('Al-Balad', 'The City'), ('Ash-Shams', 'The Sun'), ('Al-Layl', 'The Night'),
    ('Ad-Duha', 'The Morning Brightness'), ('Ash-Sharh', 'The Relief'), ('At-Tin', 'The Fig'),
    ('Al-Alaq', 'The Clinging Clot'), ('Al-Qadr', 'The Night of Decree'), ('Al-Bayyinah', 'The Clear Proof'),
    ('Az-Zalzalah', 'The Earthquake'), ('Al-Adiyat', 'The Chargers'), ('Al-Qari\'ah', 'The Striking Calamity'),
    ('At-Takathur', 'Rivalry in Increase'), ('Al-Asr', 'Time'), ('Al-Humazah', 'The Slanderer'),
    ('Al-Fil', 'The Elephant'), ('Quraysh', 'Quraysh'), ('Al-Ma\'un', 'Small Kindnesses'),
    ('Al-Kawthar', 'Abundance'), ('Al-Kafirun', 'The Disbelievers'), ('An-Nasr', 'The Help'),
    ('Al-Masad', 'The Palm Fibre'), ('Al-Ikhlas', 'Sincerity'), ('Al-Falaq', 'The Daybreak'),
    ('An-Nas', 'Mankind'),
]
assert len(SURAH_EN) == 114

# صفحة عربي ⇄ صفحتها الإنجليزي (اسم الـ url) - بيستخدمها زرار تبديل اللغة و hreflang
PAIRS = {
    'home': 'en_home', 'about': 'en_about', 'pricing': 'en_pricing', 'contact': 'en_contact',
    'quality_standards': 'en_quality_standards', 'privacy': 'en_privacy', 'terms': 'en_terms',
    'editorial_policy': 'en_editorial_policy', 'quran_index': 'en_quran_index', 'blog_list': 'en_blog_list',
    'thank_you': 'en_thank_you',
}
PAIRS.update({v: k for k, v in list(PAIRS.items())})
