# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.rest import DatapuntViewSet
from django.http import HttpResponseRedirect
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.response import Response as DRFResponse
from rest_framework.reverse import reverse
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

from signals.apps.api.generics.exceptions import Gone
from signals.apps.api.generics.mixins import RetrieveModelMixin
from signals.apps.questionnaire.models import Questionnaire, Response, Answer, Question
from signals.apps.questionnaire.serializers import (
    QuestionnaireSerializer,
    ResponseSerializer, AnswerCreateSerializer, EmptySerializer,
)


class QuestionnaireViewSet(DatapuntViewSet):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Questionnaire.objects.filter(is_active=True)
    pagination_class = None

    serializer_detail_class = QuestionnaireSerializer
    serializer_class = QuestionnaireSerializer

    # def list(self, request, *args, **kwargs):
    #     raise NotFound()

    @action(detail=True, url_path=r'start/?$', methods=['POST', ], serializer_class=EmptySerializer)
    def start(self, request, *args, **kwargs):
        response = Response.objects.create(questionnaire=self.get_object())

        context = self.get_serializer_context()
        context.update({'response': response})
        serializer = ResponseSerializer(response, context=context)
        return DRFResponse(serializer.data, status=201)


class ResponseViewSet(NestedViewSetMixin, RetrieveModelMixin, GenericViewSet):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    queryset = Response.objects.all()
    pagination_class = None

    serializer_class = ResponseSerializer

    def get_object(self):
        response = super().get_object()
        if response.is_expired:
            raise Gone(detail='Response expired!')
        if response.finished:
            raise Gone(detail='Response filled out!')
        return response

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'response': self.get_object()})
        return context

    @action(detail=True, url_path=r'finish/?$', methods=['POST', ], serializer_class=EmptySerializer)
    def finish(self, request, *args, **kwargs):
        response = self.get_object()

        if not response.finished:
            response.finished = True
            response.save()

        return DRFResponse({'thank': 'you'})

    @action(detail=True, url_path=r'answer/(?P<question_uuid>[-\w]+)/?$', methods=['POST', ],
            serializer_class=AnswerCreateSerializer)
    def answer_question(self, request, question_uuid=None, *args, **kwargs):
        response = self.get_object()
        question = Question.objects.get(uuid=question_uuid)

        try:
            question.validate_answer(request.data['text'], raise_exceptions=True)
        except Exception as e:
            raise ValidationError({'text': str(e)})

        Answer.objects.create(text=request.data['text'], response=response, question=question)

        context = self.get_serializer_context()
        context.update({'response': response})
        response_serializer = ResponseSerializer(response, context=context)
        return DRFResponse(response_serializer.data)
