# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, get_object_or_404

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ims.models import Client, Product
from ims import utils
from api.serializers import ClientSerializer, ProductSerializer

import logging
logger = logging.getLogger(__name__)


class GetClients(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        clients = Client.objects.filter(is_active=True).order_by('company_name')

        clients_sorted = []
        for client in utils.tree_to_list(clients, sort_by='company_name'):
            logger.warning(client)
            clients_sorted.append({
                'id': client['obj'].id,
                'company_name': client['obj'].company_name,
                'depth': client['depth'],
            })

        return Response(clients_sorted)


class GetClientProducts(ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        client = get_object_or_404(Client, pk=self.kwargs['client_id'])
        return Product.objects.filter(client=client, is_active=True)
