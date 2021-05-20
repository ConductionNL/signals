# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.rest import HALPagination
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND

from signals.apps.api.generics import mixins
from signals.apps.qa.models import QASession, Question
from signals.apps.qa.serializers import (
    AnswerDeserializer,
    AnswerSerializer,
    PrivateQuestionSerializerDetail2,
    QASessionSerializer
)
from signals.apps.qa.services import QASessionService


class QuestionFilterSet(FilterSet):
    uuid = filters.UUIDFilter(field_name='uuid')
    key = filters.CharFilter(field_name='key')


class PrivateQuestionViewSet2(mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.ListModelMixin,
                              mixins.UpdateModelMixin, viewsets.GenericViewSet,):
    queryset = Question.objects.order_by('-id')

    serializer_class = PrivateQuestionSerializerDetail2
    serializer_detail_class = PrivateQuestionSerializerDetail2
    pagination_class = HALPagination

    filter_backends = (DjangoFilterBackend,)
    filterset_class = QuestionFilterSet


class PublicQuestionViewSet2(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Question.objects.order_by('-id')

    serializer_class = PrivateQuestionSerializerDetail2  # TODO: replace with public version?
    serializer_detail_class = PrivateQuestionSerializerDetail2
    pagination_class = HALPagination

    filter_backends = (DjangoFilterBackend,)
    filterset_class = QuestionFilterSet


class PublicAnswerViewSet(viewsets.ViewSet):
    def create(self, request, *args, **kwargs):
        deserializer = AnswerDeserializer(data=request.data)
        deserializer.is_valid()

        token = deserializer.data.get('session_token', None)
        answer = QASessionService.process_answer(
            deserializer.data['key'],
            deserializer.data['answer'],
            token
        )

        out = AnswerSerializer(answer).data
        # Don't need the success headers with a Location entry, because answers
        # have no API endpoint.
        return Response(out, status=HTTP_201_CREATED)


class PublicQASessionViewSet(viewsets.ViewSet):
    def retrieve(self, requests, pk=None):
        # TODO: clean-up the lookup arg handling here
        answer_session = QASession.objects.get(token=pk)
        if answer_session.submit_before is not None:
            if answer_session.submit_before <= timezone.now():
                return Response(status=HTTP_404_NOT_FOUND)  # TODO: add proper body

        return Response(QASessionSerializer(answer_session).data, status=HTTP_200_OK)

    @action(detail=True, url_path=r'answers/?$')
    def answers(self, request, pk=None):
        answer_session = QASession.objects.get(token=pk)
        if answer_session.submit_before is not None:
            if answer_session.submit_before <= timezone.now():
                return Response(status=HTTP_404_NOT_FOUND)  # TODO: add proper body

        answers = QASessionService.get_answers(answer_session.token)
        out = AnswerSerializer(answers, many=True).data

        return Response(out, status=HTTP_200_OK)

    @action(detail=True, url_path=r'questions/?$')
    def questions(self, request, pk=None):
        # TODO: consider wether we want this exposed (or should we only )
        answer_session = QASession.objects.get(token=pk)
        if answer_session.submit_before is not None:
            if answer_session.submit_before <= timezone.now():
                return Response(status=HTTP_404_NOT_FOUND)  # TODO: add proper body

        questions = QASessionService.get_questions(answer_session.token)
        out = PrivateQuestionSerializerDetail2(questions, many=True).data

        return Response(out, status=HTTP_200_OK)
