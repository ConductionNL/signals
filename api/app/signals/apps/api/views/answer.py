# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND

from signals.apps.api.serializers import AnswerDeserializer, AnswerSerializer, QASessionSerializer
from signals.apps.services.domain.qa import QASessionService
from signals.apps.signals.models import QASession


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
