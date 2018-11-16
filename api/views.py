# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, get_object_or_404

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins

from ims.models import User, Client, Product, AsyncTask
from ims import utils
from api.serializers import UserSerializer, ClientSerializer, ProductSerializer, AsyncTaskSerializer

import logging
logger = logging.getLogger(__name__)


class GetClients(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        clients = Client.objects.filter(is_active=True).order_by('company_name')

        clients_sorted = []
        for client in utils.tree_to_list(clients, sort_by='company_name'):
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
        queryset = Product.objects.filter(client=client, is_active=True)
        source_product_id = self.request.query_params.get('source_productid', None)
        if source_product_id:
            source_product = get_object_or_404(Product, pk=source_product_id)
            queryset = queryset.filter(item_number=source_product.item_number, packing=source_product.packing)
        return queryset


class AsyncTaskStatus(APIView):

    def get(self, request, task_id):
        async_task = get_object_or_404(AsyncTask, pk=task_id)
        serializer = AsyncTaskSerializer(async_task)
        return Response(serializer.data)


class AutocompleteUsers(APIView):

    def get(self, request, term):
        response = {'users': []}

        for user in User.objects.filter(email__icontains=term).order_by('email')[0:20]:
            response['users'].append({
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.full_name,
                'email': user.email,
            })

        return Response(response)


class UserAPIView(APIView):
#    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data)


class UserListAPIView(ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = (IsAuthenticated,)

