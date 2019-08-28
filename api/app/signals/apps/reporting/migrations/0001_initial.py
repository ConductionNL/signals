import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ReportDefinition',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(max_length=1000)),
                ('interval', models.CharField(choices=[('WEEK', 'Week')], max_length=255)),
                ('category', models.CharField(
                    choices=[('CATEGORY_SUB', 'Subcategorie')],
                    max_length=255
                )),
                ('area', models.CharField(choices=[('AREA_ALL', 'Overal')], max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='ReportIndicator',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('code', models.CharField(max_length=16)),
                ('report', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='reporting.ReportDefinition'
                )),
            ],
        ),
    ]
