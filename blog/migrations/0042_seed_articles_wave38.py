"""الدفعة الثامنة والثلاثون: ثمانية فهارس كبرى (تفسير الآيات، تفسير السور، تطبيقات التجويد، خطط الحفظ،
موسوعة موضوعات القرآن، أسماء الله الحسنى، قصص القرآن للأطفال، وفهرس إنجليزي لمعاني الآيات)،
المقالات 2219-2226، لربط مئات المقالات ببعضها ورفع قوة الربط الداخلي."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_articles
    seed_articles(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('blog', '0041_bump_modified_expanded'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
