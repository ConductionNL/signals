# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from django.urls import include, path

from signals.apps.api.routers import SignalsRouterVersion1
from signals.apps.questionnaire.views import QuestionnaireViewSet, ResponseViewSet

router = SignalsRouterVersion1()

(
    router.register(r'questionnaires', QuestionnaireViewSet, basename='questionnaire')
          .register(r'responses', ResponseViewSet, basename='questionnaire-response',
                    parents_query_lookups=['questionnaire__uuid', ])
)

urlpatterns = [
    path('', include(router.urls)),
]
