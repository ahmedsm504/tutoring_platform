"""الدفعتان 21 و22 من الأسئلة (133 سؤالًا): بدايات الأجزاء الثلاثين بالعربي والإنجليزي، وسبب تسمية السور،
وأسئلة تجويد وحفظ وأطفال جديدة. آمنة: الأسئلة الموجودة مبتتكررش."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_questions
    seed_questions(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('qna', '0021_seed_questions_wave20'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
