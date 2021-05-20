# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.test import TestCase

from signals.apps.qa.models import Question


class TestQ2(TestCase):
    def test_create(self):
        Question.objects.create(
            key='test_question_plain_text',
            field_type='plain_text',
            payload={'label': 'Dit is een test', 'shortLabel': 'blah'},
            required=False,
            path='PLACEHOLDER',
        )
