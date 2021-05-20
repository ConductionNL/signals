# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.serializers import HALSerializer
from django.utils.text import slugify
from rest_framework import serializers

from signals.apps.questionnaire.fields import (
    QuestionnaireLinksField,
    QuestionnaireResponseLinksField,
    QuestionnaireResponsePageQuestionLinksField,
)
from signals.apps.questionnaire.models import (
    Answer,
    Page,
    PageQuestion,
    Question,
    Questionnaire,
    Response,
)


class EmptySerializer(serializers.Serializer):
    pass


class QuestionSerializer(serializers.ModelSerializer):
    choices = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ('uuid', 'text', 'help_text', 'type', 'choices', 'slug', )
        read_only_fields = fields

    def get_choices(self, obj):
        return {slugify(value.strip()): value.strip() for value in obj.choices.split(',')} if obj.choices else None


class PageQuestionSerializer(HALSerializer):
    serializer_url_field = QuestionnaireResponsePageQuestionLinksField
    question = QuestionSerializer()
    answer = serializers.SerializerMethodField()

    class Meta:
        model = PageQuestion
        fields = ('_links', 'question', 'required', 'order', 'answer', )
        read_only_fields = fields

    def get_answer(self, obj):
        response = self.context['response']
        if response.answers.filter(question_id=obj.question.pk).exists():
            answer = response.answers.filter(question_id=obj.question.pk).order_by('created_at').last()
            serializer = SimpleAnswerSerializer(answer)
            return serializer.data


class PageSerializer(serializers.ModelSerializer):
    questions = PageQuestionSerializer(source='pagequestion_set', many=True)

    class Meta:
        model = Page
        fields = ('uuid', 'description', 'order', 'questions', )
        read_only_fields = fields


class QuestionnaireSerializer(HALSerializer):
    serializer_url_field = QuestionnaireLinksField

    class Meta:
        model = Questionnaire
        fields = ('_links', 'uuid', 'name', )
        read_only_fields = fields


class ResponseSerializer(HALSerializer):
    serializer_url_field = QuestionnaireResponseLinksField
    questionnaire = serializers.UUIDField(source='questionnaire.uuid')
    pages = PageSerializer(source='questionnaire.pages', many=True)

    class Meta:
        model = Response
        fields = ('_links', 'uuid', 'questionnaire', 'pages', )
        read_only_fields = fields


class SimpleAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ('text', 'created_at', )


class AnswerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ('text', )
