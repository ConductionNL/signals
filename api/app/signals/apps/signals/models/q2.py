# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Gemeente Amsterdam
import uuid

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError

from signals.apps.signals.models.q2_fieldtypes import field_type_choices, get_field_type_class


class Q2(models.Model):
    key = models.CharField(unique=True, max_length=255, null=True, blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    field_type = models.CharField(choices=field_type_choices(), max_length=255)
    payload = models.JSONField(null=True, blank=True)
    required = models.BooleanField(default=False)

    path = models.CharField(max_length=255)

    def _clean_path(self, value):  # later !!!
        # should only allow valid JSON identifiers, implementation TBD (also consider models.Field subclass for this)
        return value

    def _clean_payload(self, value):
        field_type_class = get_field_type_class(self)
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

    def validate_submission(self, data):
        # To be called from the Submission .clean method, candidate for
        # refactor to service.
        field_type_class = get_field_type_class(self)
        return field_type_class().validate_submission(data)

    def get_next_key(self, answer_data):
        """
        Find the next question based on this question's payload and sumbitted answer.
        """
        payload_next = self.payload.get('next', None)
        if not payload_next:
            return None

        # check our conditions
        for item in payload_next:
            if answer_data == item['answer']:
                return item['key']
        return None
