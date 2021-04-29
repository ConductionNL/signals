# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
"""
Validation for the various question types (Q2 objects in this proof of concept)

Note: when a fieldtype is added here, the Q2 model should be migrated (because
of the choices for the field types).
"""

import inspect
import sys

import jsonschema
from django.core.exceptions import ValidationError as django_validation_error
from jsonschema.exceptions import SchemaError as js_schema_error
from jsonschema.exceptions import ValidationError as js_validation_error


class FieldType:
    """All field types should subclass this, so that they become visible as a choice"""

    def clean(self, payload):
        jsonschema.validate(payload, self.payload_schema)  # !! what is the output? probably
        return payload

    def validate_submission(self, data):
        try:
            jsonschema.validate(data, self.submission_schema)
        except js_schema_error:
            msg = f'JSONSchema for {self.__name__} is not valid.'
            raise django_validation_error(msg)
        except js_validation_error:
            msg = 'Submitted answer does not validate.'
            raise django_validation_error(msg)
        return data


class PlainText(FieldType):
    choice = ('plain_text', 'PlainText')  # TODO: derive from class name
    submission_schema = {'type': 'string'}

    payload_schema = {
        'type': 'object',
        'properties': {
            'label': {'type': 'string'},
            'shortLabel': {'type': 'string'},
            'next': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'key': {'type': 'string'},
                        'answer': submission_schema  # leave out "answer" if next is unconditional
                    },
                    'required': ['key'],
                    'additionalProperties': False
                }
            }
        },
        'required': ['label', 'shortLabel'],
        'additionalProperties': False,
    }


class Integer(FieldType):
    choice = ('integer', 'Integer')
    submission_schema = {'type': 'integer'}

    payload_schema = {
        'type': 'object',
        'properties': {
            'label': {'type': 'string'},
            'shortLabel': {'type': 'string'},
            'next': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'key': {'type': 'string'},
                        'answer': submission_schema  # leave out "answer" if next is unconditional
                    },
                    'required': ['key'],
                    'additionalProperties': False
                }
            }
        },
        'required': ['label', 'shortLabel'],
        'additionalProperties': False,
    }


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


def get_field_type_class(question):
    '''Grab FieldType subclass that defines this question's behavior.'''
    current_module = sys.modules[__name__]
    to_find = question.field_type
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
