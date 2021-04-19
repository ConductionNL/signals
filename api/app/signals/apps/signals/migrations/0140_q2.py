import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0139_json_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='Q2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('field_type', models.CharField(
                    choices=[
                        ('checkbox_input', 'CheckboxInput'),
                        ('text_input', 'MultiTextInput'),
                        ('plain_text', 'PlainText'),
                        ('text_input', 'TextInput')
                    ],
                    max_length=255)),
                ('payload', models.JSONField(blank=True, null=True)),
                ('required', models.BooleanField(default=False)),
                ('path', models.CharField(max_length=255)),
                ('next', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='previous',
                    to='signals.Q2'
                )),
            ],
        ),
    ]
