"""الدفعة الثانية عشرة من الأسئلة (عربي). آمنة: الأسئلة الموجودة مبتتكررش."""
from django.db import migrations


def seed(apps, schema_editor):
    from content_seed.seeding import seed_questions
    seed_questions(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [('qna', '0015_seed_questions_wave11'), ('accounts', '0004_fcmtoken_user')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
