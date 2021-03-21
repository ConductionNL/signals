# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
import inspect
import sys
import uuid

import jsonschema
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError

# questionnaire-less solution

# Note that adding FieldType subclasses means having to migrate


class FieldType:
    def clean(self, payload):
        return payload  # implement cleaning rules in subclass --- probably using JSONSchema


class PlainText(FieldType):
    choice = ('plain_text', 'PlainText')
    payload_schema = {
        'type': 'object',
        'properties': {
            'label': {
                'type': 'string'
            },
            'shortLabel': {
                'type': 'string'
            },
        }
    }
    # submission_schema =

    def clean(self, payload):
        print('About to validate:\n', repr(payload), '\n\n')
        jsonschema.validate(payload, self.payload_schema)  # !! what is the output? probably
        return payload

    def process_submission(self, data):
        pass


def field_type_choices():
    current_module = sys.modules[__name__]
    seen = set()

    choices = []
    for _, item in inspect.getmembers(current_module):
        if inspect.isclass(item) and issubclass(item, FieldType) and item != FieldType:
            if item.choice[0] in seen:
                raise Exception(f'Class{item.__name__} is bad, repeated choice[0] of {item.choice[0]} !')
            seen.add(item)
            choices.append(item.choice)

    return choices


class Q2(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    field_type = models.CharField(choices=field_type_choices(), max_length=255)
    payload = JSONField(null=True, blank=True)
    required = models.BooleanField(default=False)

    path = models.CharField(max_length=255)
    next = models.ForeignKey('self', null=True, blank=True, related_name='previous', on_delete=models.CASCADE)

    def _get_field_type_class(self):
        '''Grab FieldType subclass that defines this question's behavior.'''
        current_module = sys.modules[__name__]
        to_find = self.field_type
        seen = set()

        # This scan through the module should be cached, move this code at a later point.
        for _, item in inspect.getmembers(current_module):
            if inspect.isclass(item) and issubclass(item, FieldType) and item != FieldType:
                if item.choice[0] in seen:
                    raise Exception(f'Class{item.__name__} is bad, repeated choice[0] of {item.choice[0]} !')
                seen.add(item)

                if item.choice[0] == to_find:
                    return item
        return None  # <- we want some relevant exception here

    def _clean_path(self, value):  # later !!!
        # should only allow valid JSON identifiers, implementation TBD (also consider models.Field subclass for this)
        return value

    def _clean_payload(self, value):
        field_type_class = self._get_field_type_class()
        if field_type_class is None:
            raise ValidationError('field_type')
        return field_type_class().clean(self.payload)

    def clean(self):
        if self.payload:
            self.payload = self._clean_payload(self.payload)
        self.path = self._clean_path(self.path)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def process_submission(self, data):
        # To be called from the Submission .clean method, candidate for
        # refactor to service.
        field_type_class = self._get_field_type_class()
        return field_type_class().process_submission(data)


# class Submission(models.Model):
#    question_uuid = models.UUIDField()
