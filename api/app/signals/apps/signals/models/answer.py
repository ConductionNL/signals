# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import uuid

from django.contrib.gis.db import models

ANSWER_SESSION_TTL = 2 * 60 * 60  # Two hours default


class QASession(models.Model):
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    submit_before = models.DateTimeField(blank=True, null=True)
    first_question = models.ForeignKey('Q2', on_delete=models.CASCADE, null=True)

    started_at = models.DateTimeField(null=True)
    ttl_seconds = models.IntegerField(default=ANSWER_SESSION_TTL)
    # TODO: add a created_by ...

    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        ordering = ('-created_at',)


class Answer(models.Model):
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    session = models.ForeignKey(QASession, on_delete=models.CASCADE, null=True)
    question = models.ForeignKey('Q2', on_delete=models.CASCADE)
    answer = models.JSONField()

    label = models.CharField(max_length=255)

    class Meta:
        ordering = ('-created_at',)
