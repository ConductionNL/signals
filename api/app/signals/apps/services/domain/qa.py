# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import timedelta

from django.core.exceptions import ValidationError as django_validation_error
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from signals.apps.signals.models import Q2, Answer, QASession


class QASessionService:
    @staticmethod
    def process_answer(key, answer, session_token):  # noqa: C901
        """
        Check references, check answer validity, create Answer instance.
        """
        try:
            q2 = Q2.objects.get(key=key)
        except Q2.DoesNotExist:
            msg = f'No question with key={key} exists.'
            raise ValidationError(msg)

        # Make sure we can tie our answer to an QASession:
        if session_token:
            try:
                session = QASession.objects.get(token=session_token)
            except QASession.DoesNotExist:
                msg = f'QASession referenced by token={session_token} does not exist!'
                raise ValidationError(msg)
        else:
            # We are receiving answers, so mark our QASession as started
            # right away and add a pointer to the first question in the
            # questionnaire.
            session = QASession(started_at=timezone.now(), first_question=q2)
            session.save()

        # Mark our QASession as started (in case it was prepared before)
        if not session.started_at:
            session.started_at = timezone.now()
            session.save()

        # Check that not too much time elapsed since answering started
        if session.started_at + timedelta(seconds=session.ttl_seconds) < timezone.now():
            msg = f'QASession referenced by token={session_token} does not exist!'
            raise ValidationError(msg)

        # Check that we are receiving before the QASession expired (in case
        # it was prepared before).
        if session.submit_before and session.submit_before <= timezone.now():
            msg = f'QASession referenced by token={session_token} does not exist!'
            raise ValidationError(msg)

        # Check that the answer we received matches the referenced Q2 object.
        try:
            q2.validate_submission(answer)
        except django_validation_error:
            msg = 'Answer is not valid.'
            raise ValidationError(msg)

        # Finally create an answer in the DB
        answer = Answer.objects.create(
            question=q2,
            answer=answer,
            session=session,
            label=q2.payload['shortLabel'],
        )

        return answer
