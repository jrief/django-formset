from django.db import migrations, models

def initialize_opinions(apps, schema_editor):
    OpinionModel = apps.get_model('testapp', 'OpinionModel')
    for counter in range(999):
        label = f"Opinion {counter + 100}"
        OpinionModel.objects.create(tenant=1, label=label)


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PayloadModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='OpinionModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant', models.PositiveSmallIntegerField()),
                ('label', models.CharField(max_length=50, verbose_name='Opinion')),
            ],
            options={
                'unique_together': {('tenant', 'label')},
            },
        ),
        migrations.RunPython(initialize_opinions, reverse_code=migrations.RunPython.noop),
    ]
