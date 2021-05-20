# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import logging
import uuid

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db.models.deletion import CASCADE
from django.utils import timezone
from django_extensions.db.fields import AutoSlugField
from jsonschema import validate

from signals.apps.questionnaire import app_settings
from signals.apps.questionnaire.utils import response_ttl

logger = logging.getLogger(__name__)
CHOICES_SEPARATOR = app_settings.CHOICES_SEPARATOR


class Questionnaire(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True, editable=False)
    name = models.CharField(max_length=1000)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(editable=False, auto_now=True)

    def __str__(self):
        return f'Questionnaire #{self.pk} "{self.name}" ({"" if self.is_active else "not"} active)'


class Page(models.Model):
    questionnaire = models.ForeignKey(to='questionnaire.Questionnaire', on_delete=CASCADE, related_name='pages')
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True, editable=False)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)
    questions = models.ManyToManyField(to='questionnaire.Question', through='PageQuestion', related_name='questions')

    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        ordering = ('questionnaire', 'order', )

    def __str__(self):
        return f'Page #{self.order} for questionnaire "{self.questionnaire.name}"'


class PageQuestion(models.Model):
    page = models.ForeignKey(to='questionnaire.Page', on_delete=CASCADE)
    question = models.ForeignKey(to='questionnaire.Question', on_delete=CASCADE)
    required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        ordering = ('page', 'order', )


class Question(models.Model):
    TYPE_TEXT = 'text'
    TYPE_RADIO = 'radio'
    TYPE_SELECT = 'select'
    TYPE_SELECT_MULTIPLE = 'select-multiple'
    TYPE_INTEGER = 'integer'
    TYPE_DATE = 'date'
    TYPE_TIME = 'time'
    TYPE_DATE_TIME = 'date-time'

    TYPES = (
        (TYPE_TEXT, 'Text field (multiple lines)'),
        (TYPE_RADIO, 'Radio (single selection)'),
        (TYPE_SELECT, 'Select (single selection)'),
        (TYPE_SELECT_MULTIPLE, 'Select (multiple selections)'),
        (TYPE_INTEGER, 'Integer'),
        (TYPE_DATE, 'Date'),
        (TYPE_TIME, 'Time'),
        (TYPE_DATE_TIME, 'Date + time'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, db_index=True, editable=False)
    text = models.TextField()
    help_text = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=128, choices=TYPES, default=TYPE_TEXT)
    choices = models.TextField(blank=True, null=True, help_text='The choices field will only be used if one of the '
                                                                'question is one of the following types: select, select'
                                                                ' multiple choice or radio. Provide a '
                                                                f'"{app_settings.CHOICES_SEPARATOR}"-separated list of '
                                                                'possible options')
    slug = AutoSlugField(populate_from=['text', ], blank=False, overwrite=False, editable=False)
    json_schema = JSONField(blank=True, null=True)

    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(editable=False, auto_now=True)

    def __str__(self):
        return f'{self.text} ({self.type})'

    def validate_answer(self, answer, raise_exceptions=False):
        errors = []

        if self.json_schema:
            try:
                validate(instance=answer, schema=self.json_schema)
            except Exception as e:
                errors.append(getattr(e, 'message', 'An error occurred!'))

        if raise_exceptions and errors:
            raise ValidationError(errors)

        return bool(errors)


class Response(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True, editable=False)
    questionnaire = models.ForeignKey(to='questionnaire.Questionnaire', on_delete=CASCADE, related_name='responses')

    ttl = models.DateTimeField(default=response_ttl, editable=False)
    expired = models.BooleanField(default=False)

    finished = models.BooleanField(default=False)

    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(editable=False, auto_now=True)

    @property
    def is_expired(self):
        if not self.expired and self.ttl <= timezone.now():
            self.expired = True
            self.save()
        return self.expired


class Answer(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True, editable=False)
    response = models.ForeignKey(to='questionnaire.Response', on_delete=CASCADE, related_name='answers')
    question = models.ForeignKey(to='questionnaire.Question', on_delete=CASCADE, related_name='+')
    text = models.TextField()

    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(editable=False, auto_now=True)
