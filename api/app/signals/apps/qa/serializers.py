# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from rest_framework import serializers

from signals.apps.qa.models import Question


class PrivateQuestionSerializerDetail2(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'
        read_only_fields = ('uuid',)


class AnswerSerializer(serializers.Serializer):
    """
    Serialize outgoing answer.
    """
    key = serializers.CharField(source='question.key', max_length=255)  # should be method uuid/key
    answer = serializers.JSONField()
    session_token = serializers.UUIDField(source='session.token', required=False)

    label = serializers.CharField(max_length=255)
    next_key = serializers.SerializerMethodField()

    def get_next_key(self, obj):
        return obj.question.get_next_key(obj.answer)


class AnswerDeserializer(serializers.Serializer):
    """
    Deserialize incoming Answer from JSON representations.
    """
    key = serializers.CharField(max_length=255)
    answer = serializers.JSONField()
    session_token = serializers.UUIDField(required=False)


class QASessionSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    key = serializers.CharField(source='first_question.key')
