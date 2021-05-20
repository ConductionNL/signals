# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
import uuid
from datetime import timedelta

from django.utils import timezone
from freezegun import freeze_time

# TODO: replace Q2 with Question
from signals.apps.services.domain.qa import QASessionService
from signals.apps.signals.models import Q2, Answer, QASession
from tests.test import SignalsBaseApiTestCase

PLAIN_TEXT_TEMPLATE = {
    'label': 'Dit is een vraag?',
    'shortLabel': 'Vraag',
    'key': 'blah',
}


class TestQuestionnaire(SignalsBaseApiTestCase):
    private_q2_list_endpoint = '/signals/v1/private/q2s/'
    private_q2_detail_endpoint = '/signals/v1/private/q2s/{pk}/'

    def setUp(self):
        self.client.force_authenticate(user=self.superuser)

    def test_create_question_plain_text(self):
        self.assertEqual(Q2.objects.count(), 0)

        data = {
            'field_type': 'plain_text',
            'path': 'extra_properties',
        }
        url = self.private_q2_list_endpoint

        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Q2.objects.count(), 1)

        response_json = response.json()
        self.assertIn('uuid', response_json)
        self.assertIn('field_type', response_json)
        self.assertIn('payload', response_json)
        self.assertIn('required', response_json)

    def test_update_question_plain_text(self):
        q2 = Q2.objects.create(
            key='test_question',
            field_type='plain_text',
            path='extra_properties',
            payload=None,
        )

        # now update it as well
        data = {
            'path': 'extra_properties',
            'payload': {
                'shortLabel': 'kort label',
                'label': 'lang label',
            },
        }
        url = self.private_q2_detail_endpoint.format(pk=q2.id)

        response = self.client.patch(url, data=data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Q2.objects.count(), 1)

        response_json = response.json()
        self.assertIsInstance(response_json['payload'], dict)

        q2.refresh_from_db()
        self.assertEqual(q2.payload, data['payload'])

    def test_next_field(self):
        next_none = {}
        next_unconditional = {
                'shortLabel': 'kort label',
                'label': 'lang label',
                'next': [{'key': 'next_question'}, ]
        }
        next_conditional = {
                'shortLabel': 'kort label',
                'label': 'lang label',
                'next': [{'key': 'next_question_a', 'answer': 'A'}]
        }

        Q2.objects.create(
            key='test_question_1',
            field_type='plain_text',
            payload=next_none,
            required=False,
            path='PLACEHOLDER',
        )

        Q2.objects.create(
            key='test_question_2',
            field_type='plain_text',
            payload=next_unconditional,
            required=False,
            path='PLACEHOLDER',
        )

        Q2.objects.create(
            key='test_question_3',
            field_type='plain_text',
            payload=next_conditional,
            required=False,
            path='PLACEHOLDER',
        )


class TestQuestionAnswerFlow(SignalsBaseApiTestCase):
    QUESTIONS_ENDPOINT = '/signals/v1/public/q2s/'
    ANSWERS_ENDPOINT = '/signals/v1/public/answers/'
    QA_SESSIONS_ENDPOINT = '/signals/v1/public/qa-sessions/{uuid}/'
    QA_SESSION_ANSWERS_ENDPOINT = '/signals/v1/public/qa-sessions/{uuid}/answers/'
    QA_SESSION_QUESTIONS_ENDPOINT = '/signals/v1/public/qa-sessions/{uuid}/questions/'

    def setUp(self):
        self.q_start = Q2.objects.create(
            field_type='plain_text',
            path='extra_properties.a',
            key='q_yesno',
            payload={
                'shortLabel': 'Yes or no?',
                'label': 'Yes or no, what do you choose?',
                'next': [
                    {'key': 'q_yes', 'answer': 'yes'},
                    {'key': 'q_no', 'answer': 'no'},
                ]
            }
        )

        self.q_yes = Q2.objects.create(
            field_type='plain_text',
            path='extra_properties.b',
            key='q_yes',
            payload={
                'shortLabel': 'yes',
                'label': 'The yes question. Happy now?'
            }
        )

        self.q_no = Q2.objects.create(
            field_type='plain_text',
            path='extra_properties.c',
            key='q_no',
            payload={
                'shortLabel': 'no',
                'label': 'The no question. Still unhappy?'
            }
        )

    def test_answer_session_with_conditional_questions(self):
        """
        Test conditional question-answer flow (only happy flow).
        """
        self.assertEqual(QASession.objects.count(), 0)

        # Retrieve the first question
        response = self.client.get(f'{self.QUESTIONS_ENDPOINT}?key=q_yesno')
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['count'], 1)  # we expect one question (key is unique and exists)
        question_json = response_json['results'][0]

        # answer it
        answer = {
            'key': question_json['key'],
            'answer': 'yes',
            'session': None,
        }
        response = self.client.post(self.ANSWERS_ENDPOINT, data=answer, format='json')
        self.assertEqual(response.status_code, 201)

        response_json = response.json()
        self.assertEqual(response_json['key'], 'q_yesno')
        self.assertEqual(response_json['answer'], 'yes')
        self.assertEqual(response_json['next_key'], 'q_yes')
        self.assertIn('session_token', response_json)
        session_token = response_json['session_token']

        # retrieve second question:
        next_key = response_json['next_key']
        response = self.client.get(f'{self.QUESTIONS_ENDPOINT}?key={next_key}')
        self.assertEqual(response.status_code, 200)

        # answer it
        answer_2 = {
            'key': next_key,
            'answer': 'Yes happy now!',
            'session_token': session_token
        }
        response = self.client.post(self.ANSWERS_ENDPOINT, data=answer_2, format='json')
        self.assertEqual(response.status_code, 201)

        response_json = response.json()
        self.assertEqual(response_json['key'], 'q_yes')
        self.assertEqual(response_json['answer'], answer_2['answer'])
        self.assertEqual(response_json['session_token'], answer_2['session_token'])
        self.assertEqual(response_json['next_key'], None)  # means we reached the end of questionnaire
        self.assertEqual(response_json['label'], self.q_yes.payload['shortLabel'])

        # some database level checks
        self.assertEqual(Answer.objects.count(), 2)
        self.assertEqual(QASession.objects.count(), 1)

    def test_answer_session_does_not_exist(self):
        """
        Questions cannot be submitted to SIA API if non-existant QASession is referenced
        """
        # Retrieve the first question
        response = self.client.get(f'{self.QUESTIONS_ENDPOINT}?key=q_yesno')
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['count'], 1)  # we expect one question (key is unique and exists)
        question_json = response_json['results'][0]

        # answer it, observe that using a non-existing QASession yields a HTTP 400
        random_token = uuid.uuid4()
        with self.assertRaises(QASession.DoesNotExist):
            QASession.objects.get(token=random_token)

        answer = {
            'key': question_json['key'],
            'answer': 'yes',
            'session_token': random_token,
        }
        response = self.client.post(self.ANSWERS_ENDPOINT, data=answer, format='json')
        with self.assertRaises(QASession.DoesNotExist):
            QASession.objects.get(token=random_token)
        self.assertEqual(response.status_code, 400)

        # some database level checks
        self.assertEqual(Answer.objects.count(), 0)
        self.assertEqual(QASession.objects.count(), 0)

    def test_kto_prototype(self):
        """
        Pretend our questions are requested feedback.
        """
        # Idea is that instead of a Feedback object we prepare an QASession
        # and request the reporter to fill it out some time later. For
        # expediency we assume that the link to the questionnaire was shared
        # somehow (likely by email as with KTO).
        now = timezone.now()
        prepared_session = QASession.objects.create(
            submit_before=now + timedelta(days=14),
            first_question=self.q_start,
        )

        # Retrieve prepared QASession
        url = self.QA_SESSIONS_ENDPOINT.format(uuid=prepared_session.token)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        key = response_json['key']
        session_token = response_json['token']
        self.assertEqual(key, self.q_start.key)
        self.assertEqual(uuid.UUID(session_token), prepared_session.token)

        # Retrieve first question referenced by prepared QASession
        url = self.QUESTIONS_ENDPOINT + f'?key={key}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['results'][0]['key'], key)

        # Answer the first question
        answer = {
            'key': key,
            'answer': 'yes',
            'session_token': session_token
        }

        response = self.client.post(self.ANSWERS_ENDPOINT, data=answer, format='json')
        self.assertEqual(response.status_code, 201)

        response_json = response.json()
        next_key = response_json['next_key']
        self.assertEqual(next_key, 'q_yes')  # see setUp method

        # Retrieve and answer the second question
        url = self.QUESTIONS_ENDPOINT + f'?key={next_key}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()

        # answer
        answer = {
            'key': response_json['results'][0]['key'],
            'answer': 'WHATEVER',
            'session_token': session_token
        }
        response = self.client.post(self.ANSWERS_ENDPOINT, data=answer, format='json')
        self.assertEqual(response.status_code, 201)

        response_json = response.json()
        self.assertEqual(response_json['next_key'], None)  # questionnaire fully filled out

        self.assertEqual(QASession.objects.count(), 1)  # no new session should have been created

    def test_kto_prototype_too_slow(self):
        with freeze_time('2021-05-12 12:00:00'):
            prepared_session = QASession.objects.create(
                first_question=self.q_start,
            )

            answer = {
                'key': prepared_session.first_question.key,
                'answer': 'yes',
                'session_token': prepared_session.token
            }
            response = self.client.post(self.ANSWERS_ENDPOINT, data=answer, format='json')
            self.assertEqual(response.status_code, 201)

        with freeze_time('2021-05-12 18:00:00'):
            # Try to continue session after more than 2 hours (standard QASession time to live is 2 hours)
            # That should not be allowed, because it was after the time to live had passed.
            answer = {
                'key': prepared_session.first_question.key,
                'answer': 'yes',
                'session_token': prepared_session.token
            }
            response = self.client.post(self.ANSWERS_ENDPOINT, data=answer, format='json')
            self.assertEqual(response.status_code, 400)

    def test_kto_prototype_in_time(self):
        # Set deadline in the future
        with freeze_time('2021-05-12 12:00:00'):
            now = timezone.now()
            prepared_session = QASession.objects.create(
                submit_before=now + timedelta(days=14),
                first_question=self.q_start,
            )

        # QASessions are hidden when they expire
        url = self.QA_SESSIONS_ENDPOINT.format(uuid=prepared_session.token)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Referencing a non-expired session should yield HTTP 201
        answer = {
            'key': prepared_session.first_question.key,
            'answer': 'yes',
            'session_token': prepared_session.token
        }
        response = self.client.post(self.ANSWERS_ENDPOINT, data=answer, format='json')
        self.assertEqual(response.status_code, 201)

    def test_kto_prototype_too_late(self):
        # Set deadline in the past
        with freeze_time('2021-05-12 12:00:00'):
            now = timezone.now()
            prepared_session = QASession.objects.create(
                submit_before=now - timedelta(days=14),
                first_question=self.q_start,
            )

        # QASessions are hidden when they expire
        url = self.QA_SESSIONS_ENDPOINT.format(uuid=prepared_session.token)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Referencing a expired session should yield HTTP 400
        answer = {
            'key': prepared_session.first_question.key,
            'answer': 'yes',
            'session_token': prepared_session.token
        }
        response = self.client.post(self.ANSWERS_ENDPOINT, data=answer, format='json')
        self.assertEqual(response.status_code, 400)

    def test_answers_query(self):
        session = None
        qs = Answer.objects.filter(session=session).order_by('question_id').distinct('question_id')  # noqa

    def test_get_answers(self):
        # Make sure we get only the most recent answers when we repeat answers.
        # TBD: do we only return "reachable" questions (i.e. those that are in
        # the chain of questions and answers starting at
        # QASession.first_question).

        # ----------------------
        # ------ REFACTOR ME ---
        self.assertEqual(QASession.objects.count(), 0)

        # Retrieve the first question
        response = self.client.get(f'{self.QUESTIONS_ENDPOINT}?key=q_yesno')
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['count'], 1)  # we expect one question (key is unique and exists)
        question_json = response_json['results'][0]

        # answer it
        answer = {
            'key': question_json['key'],
            'answer': 'yes',
            'session': None,
        }
        response = self.client.post(self.ANSWERS_ENDPOINT, data=answer, format='json')
        self.assertEqual(response.status_code, 201)

        response_json = response.json()
        self.assertEqual(response_json['key'], 'q_yesno')
        self.assertEqual(response_json['answer'], 'yes')
        self.assertEqual(response_json['next_key'], 'q_yes')
        self.assertIn('session_token', response_json)
        session_token = response_json['session_token']

        # retrieve second question:
        next_key = response_json['next_key']
        response = self.client.get(f'{self.QUESTIONS_ENDPOINT}?key={next_key}')
        self.assertEqual(response.status_code, 200)

        # answer it
        answer_2 = {
            'key': next_key,
            'answer': 'Yes happy now!',
            'session_token': session_token
        }
        response = self.client.post(self.ANSWERS_ENDPOINT, data=answer_2, format='json')
        self.assertEqual(response.status_code, 201)

        response_json = response.json()
        self.assertEqual(response_json['key'], 'q_yes')
        self.assertEqual(response_json['answer'], answer_2['answer'])
        self.assertEqual(response_json['session_token'], answer_2['session_token'])
        self.assertEqual(response_json['next_key'], None)  # means we reached the end of questionnaire
        self.assertEqual(response_json['label'], self.q_yes.payload['shortLabel'])

        # some database level checks
        self.assertEqual(Answer.objects.count(), 2)
        self.assertEqual(QASession.objects.count(), 1)
        # ----------------------
        # ----------------------

        answers = QASessionService.get_answers(session_token)
        self.assertEqual(len(answers), 2)

    def test_get_answers_api(self):
        # ----------------------
        # ------ REFACTOR ME ---
        self.assertEqual(QASession.objects.count(), 0)

        # Retrieve the first question
        response = self.client.get(f'{self.QUESTIONS_ENDPOINT}?key=q_yesno')
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['count'], 1)  # we expect one question (key is unique and exists)
        question_json = response_json['results'][0]

        # answer it
        answer = {
            'key': question_json['key'],
            'answer': 'yes',
            'session': None,
        }
        response = self.client.post(self.ANSWERS_ENDPOINT, data=answer, format='json')
        self.assertEqual(response.status_code, 201)

        response_json = response.json()
        self.assertEqual(response_json['key'], 'q_yesno')
        self.assertEqual(response_json['answer'], 'yes')
        self.assertEqual(response_json['next_key'], 'q_yes')
        self.assertIn('session_token', response_json)
        session_token = response_json['session_token']

        # retrieve second question:
        next_key = response_json['next_key']
        response = self.client.get(f'{self.QUESTIONS_ENDPOINT}?key={next_key}')
        self.assertEqual(response.status_code, 200)

        # answer it
        answer_2 = {
            'key': next_key,
            'answer': 'Yes happy now!',
            'session_token': session_token
        }
        response = self.client.post(self.ANSWERS_ENDPOINT, data=answer_2, format='json')
        self.assertEqual(response.status_code, 201)

        response_json = response.json()
        self.assertEqual(response_json['key'], 'q_yes')
        self.assertEqual(response_json['answer'], answer_2['answer'])
        self.assertEqual(response_json['session_token'], answer_2['session_token'])
        self.assertEqual(response_json['next_key'], None)  # means we reached the end of questionnaire
        self.assertEqual(response_json['label'], self.q_yes.payload['shortLabel'])

        # some database level checks
        self.assertEqual(Answer.objects.count(), 2)
        self.assertEqual(QASession.objects.count(), 1)
        # ----------------------
        # ----------------------

        response = self.client.get(self.QA_SESSION_ANSWERS_ENDPOINT.format(uuid=session_token))
        self.assertEqual(response.status_code, 200)

    def test_get_questions(self):
        session = QASession.objects.create(first_question=self.q_start)
        questions = QASessionService.get_questions(session.token)
        self.assertEqual(len(questions), 3)

    def test_get_questions_cyclical(self):
        # create cyclical references
        q_a = Q2.objects.create(
            field_type='plain_text',
            path='extra_properties.a',
            key='a',
            payload={
                'shortLabel': 'Question A?',
                'label': 'Question A?',
                'next': [{'key': 'b'}],
            }
        )

        Q2.objects.create(
            field_type='plain_text',
            path='extra_properties.',
            key='b',
            payload={
                'shortLabel': 'Question B?',
                'label': 'Question B?',
                'next': [{'key': 'a'}],
            }
        )

        # check that we only get two questions back
        session = QASession.objects.create(first_question=q_a)
        questions = QASessionService.get_questions(session.token)
        self.assertEqual(len(questions), 2)

    def test_get_questions_api(self):
        # ----------------------
        # ------ REFACTOR ME ---
        self.assertEqual(QASession.objects.count(), 0)

        # Retrieve the first question
        response = self.client.get(f'{self.QUESTIONS_ENDPOINT}?key=q_yesno')
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(response_json['count'], 1)  # we expect one question (key is unique and exists)
        question_json = response_json['results'][0]

        # answer it
        answer = {
            'key': question_json['key'],
            'answer': 'yes',
            'session': None,
        }
        response = self.client.post(self.ANSWERS_ENDPOINT, data=answer, format='json')
        self.assertEqual(response.status_code, 201)

        response_json = response.json()
        self.assertEqual(response_json['key'], 'q_yesno')
        self.assertEqual(response_json['answer'], 'yes')
        self.assertEqual(response_json['next_key'], 'q_yes')
        self.assertIn('session_token', response_json)
        session_token = response_json['session_token']

        # ----------------------
        # ----------------------

        # get the questions
        response = self.client.get(self.QA_SESSION_QUESTIONS_ENDPOINT.format(uuid=session_token))
        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertEqual(len(response_json), 3)
