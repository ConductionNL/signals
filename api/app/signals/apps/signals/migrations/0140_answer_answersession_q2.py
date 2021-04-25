# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
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
                ('key', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('field_type', models.CharField(choices=[('plain_text', 'PlainText')], max_length=255)),
                ('payload', models.JSONField(blank=True, null=True)),
                ('required', models.BooleanField(default=False)),
                ('path', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='AnswerSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('submit_before', models.DateTimeField(blank=True, null=True)),
                ('started_at', models.DateTimeField(null=True)),
                ('ttl_seconds', models.IntegerField(default=7200)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                (
                    'first_question',
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='signals.q2')
                ),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('answer', models.JSONField()),
                ('label', models.CharField(max_length=255)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='signals.q2')),
                (
                    'session',
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to='signals.answersession'
                    )
                ),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
    ]
