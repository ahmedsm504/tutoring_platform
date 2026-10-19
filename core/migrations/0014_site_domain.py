"""يتأكد إن دومين الموقع في django.contrib.sites هو alagme.com (السايت ماب والـ RSS بيعتمدوا عليه)."""
from django.db import migrations


def set_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    site, _ = Site.objects.get_or_create(pk=1, defaults={'domain': 'alagme.com', 'name': 'مؤسسة العجمي'})
    if site.domain in ('example.com', '', 'localhost', '127.0.0.1'):
        site.domain = 'alagme.com'
        site.name = 'مؤسسة العجمي'
        site.save()


class Migration(migrations.Migration):
    dependencies = [('core', '0013_indexnow_ping'), ('sites', '0002_alter_domain_unique')]
    operations = [migrations.RunPython(set_domain, migrations.RunPython.noop)]
