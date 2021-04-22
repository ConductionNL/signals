# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2020 - 2021 Vereniging van Nederlandse Gemeenten, Gemeente Amsterdam
from datapunt_api.rest import HALPagination
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters
from rest_framework import viewsets

from signals.apps.api.generics import mixins
from signals.apps.api.serializers import PrivateQ2SerializerDetail
from signals.apps.signals.models import Q2


class Q2FilterSet(FilterSet):
    uuid = filters.UUIDFilter(field_name='uuid')
    key = filters.CharFilter(field_name='key')


class PrivateQ2ViewSet(mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.ListModelMixin,
                       mixins.UpdateModelMixin, viewsets.GenericViewSet,):
    queryset = Q2.objects.order_by('-id')

    serializer_class = PrivateQ2SerializerDetail
    serializer_detail_class = PrivateQ2SerializerDetail
    pagination_class = HALPagination

    filter_backends = (DjangoFilterBackend,)
    filterset_class = Q2FilterSet
