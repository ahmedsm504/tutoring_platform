from django.db import migrations

OLD = 'يُحدد في المقابلة حسب عدد الحلقات والخبرة.'
NEW = 'من 50 إلى 80 جنيهًا في الساعة، حسب عدد الحلقات والخبرة.'


def run(apps, schema_editor):
    Job = apps.get_model('careers', 'JobOpening')
    for job in Job.objects.filter(slug='quran-supervisor'):
        if not job.salary_value:
            job.salary_value, job.salary_max, job.salary_unit = 50, 80, 'HOUR'
        job.important_note = job.important_note.replace('الراتب ' + OLD, 'الراتب ' + NEW)
        job.faq = job.faq.replace(OLD, NEW)
        job.save()


class Migration(migrations.Migration):
    dependencies = [('careers', '0003_salary_max')]
    operations = [migrations.RunPython(run, migrations.RunPython.noop)]
