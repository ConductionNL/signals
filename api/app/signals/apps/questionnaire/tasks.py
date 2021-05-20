# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import logging

from django.utils import timezone

from signals.apps.questionnaire.models import Response
from signals.celery import app

log = logging.getLogger(__name__)


@app.task
def deactivate_expired_responses():
    """
    Deactivate all Response objects in the database that are active, not finished and past their TTL
    """
    response_qs = Response.objects.filter(expired=False, finished=False, ttl__lt=timezone.now())
    response_qs.update(expired=True)
