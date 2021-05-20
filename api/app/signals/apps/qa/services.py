# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datetime import timedelta

from django.core.exceptions import ValidationError as django_validation_error
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from signals.apps.qa.models import Answer, QASession, Question

N_MAX_QUESTIONS_PER_QUESTIONNAIRE = 100


class QASessionService:
    @staticmethod
    def process_answer(key, answer, session_token):  # noqa: C901
        """
        Check references, check answer validity, create Answer instance.
        """
        try:
            question = Question.objects.get(key=key)
        except Question.DoesNotExist:
            msg = f'No question with key={key} exists.'
            raise ValidationError(msg)

        # Make sure we can tie our answer to an QASession:
        if session_token:
            session = QASessionService.get_qa_session(session_token)
        else:
            # We are receiving answers, so mark our QASession as started
            # right away and add a pointer to the first question in the
            # questionnaire.
            session = QASession(started_at=timezone.now(), first_question=question)
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

        # Check that the answer we received matches the referenced Question object.
        try:
            question.validate_submission(answer)
        except django_validation_error:
            msg = 'Answer is not valid.'
            raise ValidationError(msg)

        # Finally create an answer in the DB
        answer = Answer.objects.create(
            question=question,
            answer=answer,
            session=session,
            label=question.payload['shortLabel'],
        )

        return answer

    @staticmethod
    def get_qa_session(session_token):
        try:
            session = QASession.objects.get(token=session_token)
        except QASession.DoesNotExist:
            msg = f'QASession referenced by token={session_token} does not exist!'
            raise ValidationError(msg)
        return session

    @staticmethod
    def get_answers(session_token):
        """
        Retrieve all answers associated with a QASession, return list.
        """
        session = QASessionService.get_qa_session(session_token)

        # Postgres only: https://docs.djangoproject.com/en/3.2/ref/models/querysets/#distinct
        # We want the most recent answer per unique question (in effect letting
        # clients overwrite questions).
        all_answers = list(
            Answer.objects.filter(session=session)
            .order_by('question_id')
            .distinct('question_id')
            .select_related('question')
        )
        all_question_ids = [answer.question_id for answer in all_answers]

        # We do not want to repeatedly hit the database, hence we cache the answers.
        answer_cache = {a.question.key: a for a in all_answers}
        assert session.first_question.id in all_question_ids  # protects prepared QASeesions against random answers

        answers = []
        current_answer = answer_cache.get(session.first_question.key, None)

        while current_answer:
            answers.append(current_answer)
            next_key = current_answer.question.get_next_key(current_answer.answer)

            current_answer = answer_cache.get(next_key, None)

        return answers

    @staticmethod
    def get_questions(session_token):
        """
        Retrieve all questions associated with a QASession, return list.
        """
        # NOTE: this does not check whether the graph formed by the questions
        # is actually a valid graph (in this context whether it is a-cyclical).
        # This only returns the connected component reachable from the first
        # question. If there are cycles they are not detected.
        session = QASessionService.get_qa_session(session_token)

        all_questions = {
            session.first_question.key: session.first_question
        }
        to_visit = set(session.first_question.get_all_next_keys())

        while to_visit:
            key = to_visit.pop()
            question = Question.objects.get(key=key)  # can raise ...
            all_questions[key] = question

            next_keys = question.get_all_next_keys()
            for next_key in next_keys:
                if next_key not in all_questions:
                    to_visit.add(next_key)

        return all_questions.values()

    @staticmethod
    def get_extra_properties(session_token):
        """
        Create old-style extra_properties from the answers associated with a QASession.

        Note:
        The category_url is not known in general, so it is not added here. Caller is
        has the responsibility to overwrite the category_url property.
        """
        answers = QASessionService.get_answers(session_token)

        extra_properties = []
        for answer in answers:
            props = {
                'id': answer.question.key,
                'label': answer.label,
                'answer': answer.answer,
                'category_url': 'PLACEHOLDER',
            }
            extra_properties.append(props)

        return extra_properties
