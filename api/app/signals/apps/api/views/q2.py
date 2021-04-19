# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from datapunt_api.rest import HALPagination
from rest_framework import viewsets

from signals.apps.api.generics import mixins
from signals.apps.api.serializers import PrivateQ2SerializerDetail
from signals.apps.signals.models import Q2


class PrivateQ2ViewSet(mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                       mixins.UpdateModelMixin, viewsets.GenericViewSet,):
    queryset = Q2.objects.all()

    serializer_class = PrivateQ2SerializerDetail
    serializer_detail_class = PrivateQ2SerializerDetail
    pagination_class = HALPagination
