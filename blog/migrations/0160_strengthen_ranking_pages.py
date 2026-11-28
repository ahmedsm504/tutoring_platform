from django.db import migrations

RESTORED = ['madd-farq-and-tamkin', 'tafsir-ayah-rabbi-inni-lima-anzalta-ilayya-faqir',
            'ha-al-kinaya-rules', 'idgham-mutajanisayn']
BUNDLES = ['idgham-mutaqaribayn', 'alifs-dropped-in-wasl', 'tafsir-surat-ash-shuara',
           # روابط داخلية للمقالات الجديدة من أقرب المقالات ليها
           'noon-sakinah-tanween-rules', 'makharij-al-huruf', 'tafsir-surat-al-falaq-kamila', 'tafsir-surat-an-nas-kamila',
           'tafsir-surat-al-anbiya-kamila', 'tafsir-surat-al-qasas-kamila', 'madd-types-tajweed',
           'tafsir-ayat-index-by-surah']
# عناوين تبدأ بكلمة البحث نفسها («مكتوبة»، «متى تفخم الألف») وإجابات مباشرة لأسئلة جوجل
RETITLED = ['tafsir-surat-abasa-kamila', 'tafsir-surat-al-jinn-kamila', 'tafsir-surat-ad-dukhan-kamila',
            'alif-tafkhim-and-tarqiq', 'surah-al-qamar-full-tafsir-english', 'surah-ash-shura-full-tafsir-english',
            'tafsir-surat-al-bayyina-kamila']

# روابط داخلية كانت بتشاور على الأقسام المختصرة -> المقال الكامل
RELINKED = [
    'alifs-dropped-in-wasl',
    'ayat-al-kursi-tajweed',
    'from-qaida-to-mushaf-transition',
    'idgham-mutaqaribayn',
    'imam-hamza-az-zayyat-biography',
    'juz-20-themes-and-summary',
    'learn-tajweed-roadmap',
    'lips-jawf-khayshum-makharij',
    'madd-types-tajweed',
    'mushaf-symbols-explained',
    'qalqalah-rules',
    'small-letters-in-mushaf',
    'tajweed-applied-ahqaf-ending',
    'tajweed-applied-araf-ending',
    'tajweed-applied-baqara-177',
    'tajweed-applied-fajr-balad',
    'tajweed-applied-hijr-ending',
    'tajweed-applied-kahf-first-ten',
    'tajweed-applied-mujadila-ending',
    'tajweed-applied-naml-ending',
    'tajweed-applied-nisa-36',
    'tajweed-applied-nur-ending',
    'tajweed-applied-rum-ending',
    'tajweed-applied-surat-al-jinn',
    'tajweed-applied-surat-an-naziat',
    'tajweed-applied-surat-as-saff',
    'tajweed-applied-surat-at-tahrim',
    'tajweed-applied-yasin-ending',
    'tajweed-applied-yunus-62-64',
    'teaching-kids-lam-shamsiyya-qamariyya-simply',
]


def run(apps, schema_editor):
    """صفحات كانت بتظهر كتير في جوجل في الترتيب 7-15:
    - 4 مقالات قديمة كانت اندمجت كأقسام صغيرة في صفحات مجمعة رجعت مقالات كاملة على روابطها الأصلية.
    - 4 مقالات جديدة لأسئلة عليها بحث كبير (الاستعلاء والاستفال، ذو النون، الإدغام بغنة وبغير غنة، المعوذات).
    - الأقسام المكررة في الصفحات المجمعة بقت ملخص ورابط للمقال الكامل."""
    from content_seed.seeding import apply_merges, seed_articles
    seed_articles(apps, schema_editor)
    apply_merges(apps, RESTORED + RETITLED, refresh=sorted(set(BUNDLES + RELINKED)))


class Migration(migrations.Migration):
    dependencies = [('blog', '0159_draft_legacy_duplicates')]
    operations = [migrations.RunPython(run, migrations.RunPython.noop)]
