# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from rest_framework import serializers

from signals.apps.signals.models import Q2


class PrivateQ2SerializerDetail(serializers.ModelSerializer):
    class Meta:
        model = Q2
        fields = '__all__'
        read_only_fields = ('uuid',)
