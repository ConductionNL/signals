
# TODO: replace Q2 with Question
from signals.apps.signals.models import Q2
from tests.test import SignalsBaseApiTestCase

PLAIN_TEXT_TEMPLATE = {
    'label': 'Dit is een vraag?', 'shortLabel': 'vraag',
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
