# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from collections import OrderedDict

from rest_framework import serializers

from signals.apps.questionnaire.models import Questionnaire, Response, PageQuestion


class QuestionnaireLinksField(serializers.HyperlinkedIdentityField):
    def to_representation(self, value: Questionnaire) -> OrderedDict:
        request = self.context.get('request')

        return OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request))),
            ('self', dict(href=self.reverse('questionnaire-detail', kwargs={'uuid': value.uuid}, request=request))),
            ('sia:start', dict(href=self.reverse('questionnaire-start', kwargs={'uuid': value.uuid}, request=request))),
        ])


class QuestionnaireResponseLinksField(serializers.HyperlinkedIdentityField):
    def to_representation(self, value: Response) -> OrderedDict:
        request = self.context.get('request')

        return OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request))),
            ('self', dict(href=self.reverse('questionnaire-response-detail',
                                            kwargs={'parent_lookup_questionnaire__uuid': value.questionnaire.uuid,
                                                    'uuid': value.uuid},
                                            request=request))),
            ('sia:finish', dict(href=self.reverse('questionnaire-response-finish',
                                                  kwargs={'parent_lookup_questionnaire__uuid': value.questionnaire.uuid,
                                                          'uuid': value.uuid},
                                                  request=request))),
        ])


class QuestionnaireResponsePageQuestionLinksField(serializers.HyperlinkedIdentityField):
    def to_representation(self, value: PageQuestion) -> OrderedDict:
        request = self.context.get('request')

        return OrderedDict([
            ('curies', dict(name='sia', href=self.reverse('signal-namespace', request=request))),
            ('sia:answer', dict(href=self.reverse('questionnaire-response-answer-question',
                                                  kwargs={'parent_lookup_questionnaire__uuid': value.page.questionnaire.uuid,  # noqa
                                                          'uuid': self.context['response'].uuid,
                                                          'question_uuid': value.question.uuid},
                                                  request=request))),
        ])
