from django.test import TestCase

from signals.apps.signals.models import Q2


class TestQ2(TestCase):
    def test_create(self):
        Q2.objects.create(
            field_type='plain_text',
            payload={'label': 'Dit is een test', 'shortLabel': 'blah'},
            required=False,
            path='PLACEHOLDER',
            next=None,
        )
