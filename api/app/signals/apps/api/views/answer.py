# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from signals.apps.api.serializers import AnswerDeserializer, AnswerSerializer
from signals.apps.services.domain.qa import QuestionAnswerService


class PublicAnswerViewSet(viewsets.ViewSet):
    def create(self, request, *args, **kwargs):
        deserializer = AnswerDeserializer(data=request.data)
        deserializer.is_valid()

        token = deserializer.data.get('session_token', None)
        answer = QuestionAnswerService.create_answer(
            deserializer.data['key'],
            deserializer.data['answer'],
            token
        )

        out = AnswerSerializer(answer).data
        # Don't need the success headers with a Location entry, because answers
        # have no API endpoint.
        return Response(out, status=HTTP_201_CREATED)
