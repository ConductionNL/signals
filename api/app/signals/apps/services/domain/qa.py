# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.core.exceptions import ValidationError as django_validation_error
from rest_framework.exceptions import ValidationError

from signals.apps.signals.models import Q2, Answer, AnswerSession


class QuestionAnswerService:
    @staticmethod
    def create_answer(key, answer, session_token):
        """
        Check references, check answer validity, create Answer instance.
        """
        try:
            q2 = Q2.objects.get(key=key)
        except Q2.DoesNotExist:
            msg = f'No question with key={key} exists.'
            raise ValidationError(msg)

        if session_token:
            try:
                session = AnswerSession.objects.get(token=session_token)
            except AnswerSession.DoesNotExist:
                msg = f'AnswerSession referenced by token={session_token} does not exist!'
                raise ValidationError(msg)
        else:
            session = QuestionAnswerService.create_answer_session()

        try:
            q2.validate_submission(answer)
        except django_validation_error:
            msg = 'Answer is not valid.'
            raise ValidationError(msg)

        answer = Answer.objects.create(
            question=q2,
            answer=answer,
            session=session,
            label=q2.payload['shortLabel'],
        )

        return answer

    @staticmethod
    def create_answer_session():
        return AnswerSession.objects.create()
