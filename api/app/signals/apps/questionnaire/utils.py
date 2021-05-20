# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.utils import timezone

from signals.apps.questionnaire import app_settings


def response_ttl(seconds=app_settings.DEFAULT_RESPONSE_TTL):
    """
    By default a response is valid for 3600 seconds

    Can be changed by setting the `DEFAULT_RESPONSE_TTL` of the `QUESTIONNAIRE` settings
    """
    return timezone.now() + timezone.timedelta(seconds=seconds)
