# -*- coding: utf-8 -*-


from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Func, F, Count
from django.db.models.functions import Coalesce, Trunc
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden, HttpResponseRedirect
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied

import django_tables2 as tables
#from django_filters import FilterSet
#from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

#from two_factor.views import LoginView, PhoneSetupView, PhoneDeleteView, DisableView
#from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ims.models import User, Client, Shipment, Transaction, Product, Location, Receivable, ShipmentDoc, ClientUser, ActionLog, ReturnedProduct, AsyncTask
from ims import models
from ims.forms import AjaxableResponseMixin, UserLoginForm
from ims.views import LoginView
from mgmt import forms
from ims import utils
from ims import tasks

import math
import os
import csv
from datetime import datetime, timedelta

import logging
logger = logging.getLogger(__name__)


########################################################################
# Custom two-factor account setup views

class LoginView(LoginView):
    template_name = 'mgmt/login.html'
    home_url = reverse_lazy('mgmt:home')
#    form_list = (
#        ('auth', UserLoginForm),
#        ('token', AuthenticationTokenForm),
#        ('backup', BackupTokenForm),
#    )


#class PhoneSetupView(PhoneSetupView):
#    success_url = reverse_lazy('mgmt-two_factor:profile')


#class PhoneDeleteView(PhoneDeleteView):
#    success_url = reverse_lazy('mgmt-two_factor:profile')


#class DisableView(DisableView):
#    success_url = reverse_lazy('mgmt-two_factor:profile')


########################################################################
# IMS account management views

def home(request):

    logger.info(f'{request.user} viewed mgmt home page')

    context = {
    }
    return render(request, 'mgmt/home.html', context)


def redirect(request, client_id=None):
    return redirect('mgmt:inventory', client_id=client_id)


def notifications_delivery_requests(request):
    delivery_requests = Shipment.objects.exclude(status=Shipment.Status.SHIPPED).order_by('-date_created')

    context = {
        'delivery_requests': delivery_requests,
    }
    return render(request, 'mgmt/notifications_delivery_requests.html', context)


def notifications_ready_to_ship(request):
    ready_to_ship = Shipment.objects.filter(status=Shipment.Status.READY).order_by(F('date_shipped').asc(nulls_last=True))

    context = {
        'ready_to_ship': ready_to_ship,
    }
    return render(request, 'mgmt/notifications_ready_to_ship.html', context)


def notifications_inbound_receivables(request):
    inbound_receivables = []
    for receivable in Transaction.objects.filter(is_outbound=False, cases__isnull=True).order_by('-date_created'):
        split_receivables = Transaction.objects.filter(
            product=receivable.product,
            receivable__purchase_order=receivable.receivable.purchase_order,
            receivable__shipment_order=receivable.receivable.shipment_order,
            cases__isnull=False
        )
        inbound_receivables.append({
            'obj': receivable,
            'is_partial': split_receivables.count() > 0,
        })

    context = {
        'inbound_receivables': inbound_receivables,
    }
    return render(request, 'mgmt/notifications_inbound_receivables.html', context)


def notifications_invq(request):
    invq = Shipment.objects.filter(
        status=Shipment.Status.SHIPPED,
        transaction__product__accounting_prepay_type__in=Product.INVQ_TYPES,
        accounting_status__in=[Shipment.AccountingStatus.INVQ, Shipment.AccountingStatus.PENDING],
    ).order_by('-date_created')
    invq = invq.annotate(date=Func(F('date_created'), function='DATE'))
    invq = invq.values('date', 'id', 'client__company_name', 'location__name', 'client__id')
    invq = invq.annotate(count=Count('date'))

    context = {
        'invq': invq,
    }
    return render(request, 'mgmt/notifications_invq.html', context)


def notifications_low_stock(request):
    low_stock = []
    for product in Product.objects.filter(cases_inventory__lt=F('contracted_quantity') / 2, is_active=True, client__is_active=True).order_by('name'):
        try:
            last_shipment = Transaction.objects.filter(product=product).order_by('-date_created').first()
            low_stock.append({
                'obj': product,
                'last_shipment': last_shipment,
            })
        except Transaction.DoesNotExist:
            pass

    context = {
        'low_stock': low_stock,
    }
    return render(request, 'mgmt/notifications_low_stock.html', context)


def inventory(request, client_id=None, product_id=None, product_view='detail'):
    client = get_object_or_404(Client, pk=client_id)

    product = None
    if product_id:
        try:
            product = Product.objects.get(pk=product_id, client=client)
        except Product.DoesNotExist:
            pass

    if not product_view in ('detail', 'history'):
        product_view = 'detail'

    logger.info(f'{request.user} viewed inventory {product_view} page for {client}, product {product}')

    context = {
        'client': client,
        'product_view': product_view,
        'product': product,
    }
    return render(request, 'mgmt/inventory.html', context)


def inventory_list(request, client_id=None):
    client = get_object_or_404(Client, pk=client_id)
    try:
        active_filter = int(request.GET.get('active_filter', 0))
    except:
        active_filter = 0

    filter_clients = [c['obj'] for c in client.children]
    products = Product.objects.filter(client__in=filter_clients, is_deleted=False)
    products = products.order_by('client_tag', 'name', 'item_number')

    if active_filter:
        products = products.filter(is_active=True)
    else:
        products = products.filter(is_active=False)

    context = {
        'client': client,
        'products': products,
        'active_filter': active_filter,
        'distribution_center_choices': Product.DistributionCenter.choices,
    }
    return render(request, 'mgmt/inventory_list.html', context)


def shipments(request, client_id=None, shipment_id=None):
    client = get_object_or_404(Client, pk=client_id)
    filter_clients = [c['obj'] for c in client.children]

    shipment = None
    if shipment_id:
        try:
            shipment = Shipment.objects.get(pk=shipment_id, client__in=filter_clients)
        except Shipment.DoesNotExist:
            pass

    context = {
        'client': client,
        'shipment': shipment
    }
    return render(request, 'mgmt/shipments.html', context)


def shipments_list(request, client_id=None):
    client = get_object_or_404(Client, pk=client_id)

    try:
        shipped_filter = int(request.GET.get('shipped_filter', 0))
    except:
        shipped_filter = 0

    context = {
        'client': client,
        'shipped_filter': shipped_filter,
    }
    return render(request, 'mgmt/shipments_list.html', context)


def shipments_fetch(request, client_id=None):
    client = get_object_or_404(Client, pk=client_id)
    filter_clients = [c['obj'] for c in client.children]

    try:
        shipped_filter = int(request.GET.get('shipped_filter', 0))
    except:
        shipped_filter = 0

    page_size = settings.INFINITE_SCROLL_PAGE_SIZE
    start = int(request.GET.get('start', 0))
    end = start + page_size

    shipments = Shipment.objects.filter(client__in=filter_clients).order_by('status', '-date_created')

    shipment_id = request.GET.get('shipment_id')
    if shipment_id and shipment_id.isnumeric():
        shipments = shipments.filter(pk=int(shipment_id))

    if shipped_filter:
        shipments = shipments.exclude(status=Shipment.Status.SHIPPED)[start:end]
    else:
        shipments = shipments.filter(status=Shipment.Status.SHIPPED)[start:end]

    context = {
        'client': client,
        'shipments': shipments,
        'shipped_filter': shipped_filter,
    }
    return render(request, 'mgmt/shipments_list_shipments.html', context)


def shipment_docs(request, shipment_id=None):
    shipment = get_object_or_404(Shipment, pk=shipment_id)

    context = {
        'shipment': shipment,
    }
    return render(request, 'mgmt/shipment_docs.html', context)


def product_history(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

#    date_to = timezone.now()
#    date_from = date_to - timedelta(days=90)
    date_to = timezone.now() + timedelta(days=30)
    date_from = timezone.now() - timedelta(days=365)
    try:
        date_from = datetime.strptime(request.GET.get('fromdate', ''), '%m/%d/%Y')
        date_to = datetime.strptime(request.GET.get('todate', ''), '%m/%d/%Y')
    except:
        pass

    context = {
        'product': product,
        'history': product.get_history(date_from),
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'mgmt/product_history.html', context)


def customers_list(request):
    filter = request.GET.get('filter', None)

    clients = Client.objects.all()

    if filter == 'warehousing':
        clients = clients.filter(has_warehousing=True, is_active=True)
    elif filter == 'no-warehousing':
        clients = clients.filter(has_warehousing=False, is_active=True)
    elif filter == 'inactive':
        clients = clients.filter(is_active=False)
    else:
        clients = clients.filter(is_active=True)

    context = {
        'clients': utils.tree_to_list(clients, sort_by='company_name_lower'),
    }
    return render(request, 'mgmt/customers_list.html', context)


def contacts_list(request, client_id):
    client = get_object_or_404(Client, pk=client_id)

    context = {
        'client': client,
    }
    return render(request, 'mgmt/contacts_list.html', context)


def locations_list(request, client_id):
    client = get_object_or_404(Client, pk=client_id)

    context = {
        'client': client,
    }
    return render(request, 'mgmt/locations_list.html', context)


# def contact_form(request):
#     client_id = request.GET.get('client_id', None)
#     custcontact_id = request.GET.get('custcontact_id', None)
#
#     client = get_object_or_404(Client, pk=client_id)
#     custcontact = get_object_or_404(CustContact, client=client, pk=custcontact_id)
#
#     context = {
#         'client': client,
#         'custcontact': custcontact,
#     }
#     return render(request, 'mgmt/contact_form.html', context)


# def location_form(request):
#     client_id = request.GET.get('client_id', None)
#     location_id = request.GET.get('location_id', None)
#     logger.warning(location_id)
#
#     client = get_object_or_404(Client, pk=client_id)
#     location = get_object_or_404(Location, client=client, pk=location_id)
#
#     context = {
#         'location': location,
#     }
#     return render(request, 'mgmt/location_form.html', context)


class ClientCreate(AjaxableResponseMixin, CreateView):
    model = Client
    form_class = forms.ClientCreateForm
    template_name = 'mgmt/profile.html'

    def form_valid(self, form):
        logger.info(f'{self.request.user} created client {form.cleaned_data["company_name"]}')
        return super().form_valid(form)


class ClientUpdate(AjaxableResponseMixin, UpdateView):
    model = Client
    form_class = forms.ClientForm
    template_name = 'mgmt/profile.html'

    def get_object(self):
        return get_object_or_404(Client, pk=self.kwargs['client_id'])

    def form_valid(self, form):
        logger.info(form.cleaned_data)
        # self.object.custcontact_set.update(is_primary=False)
        self.object.clientuser_set.update(is_primary=False)
        if form.cleaned_data['primary_contact']:
            form.cleaned_data['primary_contact'].is_primary = True
            form.cleaned_data['primary_contact'].save()
        logger.info(f'{self.request.user} updated client {self.object}')
        return super(ClientUpdate, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        logger.info(f'{self.request.user} viewed profile page for {self.object}')
        context = super(ClientUpdate, self).get_context_data(*args, **kwargs)
        # context['primary_contact'] = self.object.custcontact_set.filter(is_primary=True).first()
        context['primary_contact'] = self.object.clientuser_set.filter(is_primary=True).first()
        return context


class LocationCreate(AjaxableResponseMixin, CreateView):
    model = Location
    form_class = forms.LocationForm
    template_name = 'mgmt/location_form.html'

    def form_valid(self, form):
        logger.info(form.cleaned_data)
        logger.info(f'{self.request.user} created location {form.cleaned_data["name"]} for client {form.cleaned_data["client"]}')
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super(LocationCreate, self).get_context_data(*args, **kwargs)
        context['client'] = get_object_or_404(Client, pk=self.kwargs['client_id'])
        return context


class LocationUpdate(AjaxableResponseMixin, UpdateView):
    model = Location
    form_class = forms.LocationForm
    template_name = 'mgmt/location_form.html'

    def form_valid(self, form):
        logger.info(form.cleaned_data)
        logger.info(f'{self.request.user} updated location {form.cleaned_data["name"]} for client {form.cleaned_data["client"]}')
        return super().form_valid(form)

    def get_object(self):
        return get_object_or_404(Location, pk=self.kwargs['location_id'])

    def get_context_data(self, *args, **kwargs):
        context = super(LocationUpdate, self).get_context_data(*args, **kwargs)
        context['client'] = self.object.client
        return context


class LocationDelete(AjaxableResponseMixin, UpdateView):
    model = Location
    fields = ['is_active']

    def form_valid(self, form):
        self.object = self.get_object()
        logger.info(f'{self.request.user} deleted location {self.object} for client {self.object.client}')
        ActionLog.objects.create(
            user=self.request.user,
            client=self.object.client,
            product=None,
            log_message=f'Deleted location {self.object}',
            app=self.request.resolver_match.app_name,
        )
        return super().form_valid(form)

    def get_object(self):
        return get_object_or_404(Location, pk=self.kwargs['location_id'])


class ClientUserMixin(AjaxableResponseMixin):
    """
    This mixin provides a common post() method for both the Create and Update methods for ClientUsers (mappings between
    Clients and Users). This eliminates redundancy and allows a consistent UI where the admin can either add a new
    user inline while creating the ClientUser, or select an existing user, and also change the password if desired;
    the same functionality is present when updating an existing ClientUser.
    """
    create_method = False

    def post(self, *args, **kwargs):
        logger.info(self.request.POST)
        self.object = self.get_object()

        user, user_created = User.objects.get_or_create(email=self.request.POST.get('email'))

        form = self.form_class(self.request.POST)
        user_form = self.user_form_class(self.request.POST, instance=user)

        if form.is_valid() and user_form.is_valid():
            logger.info(form.cleaned_data)
            logger.info(user_form.cleaned_data)

            if self.create_method and not user_created:
                try:
                    client_user = ClientUser.objects.get(user=user, client=form.cleaned_data['client'])
                    response = {
                        'email': [{'message': 'This user is already a contact for this client.'}],
                    }
                    return JsonResponse(response)
                except ClientUser.DoesNotExist:
                    pass

            existing_client_users = ClientUser.objects.filter(user=user, client=form.cleaned_data['client'])
            is_primary = existing_client_users.filter(is_primary=True).exists()
            existing_client_users.delete()

            client_user = form.save(commit=False)
            if is_primary:
                client_user.is_primary = True
            client_user.user = user_form.save(commit=False)
            client_user.save()

            if user_form.cleaned_data['password'] == '********':
                logger.info('Password unchanged')
                client_user.user.password = user_form.initial['password']
            else:
                logger.info('Password changed')
                client_user.user.set_password(user_form.cleaned_data['password'])
                client_user.user.set_password_to_expired()
                if self.request.user == client_user.user:
                    logger.info(f'{self.request.user} changed their own password; reauthenticating')
                    user = authenticate(self.request, username=self.request.user.email, password=user_form.cleaned_data['password'])
                    login(self.request, user)
            client_user.user.save()

            if self.create_method:
                logger.info(f'{self.request.user} created contact {client_user.user} for {form.cleaned_data["client"]}')
            else:
                logger.info(f'{self.request.user} updated contact {client_user.user} for {form.cleaned_data["client"]}')
            return super().form_valid(form)
        elif not form.is_valid():
            return super().form_invalid(form)
        elif not user_form.is_valid():
            if user_created:
                user.delete()
            return super().form_invalid(user_form)


class ClientUserCreate(ClientUserMixin, CreateView):
    model = ClientUser
    form_class = forms.ClientUserForm
    user_form_class = forms.UserForm
    template_name = 'mgmt/contact_form.html'
    create_method = True

    def get_object(self):
        return get_object_or_404(Client, pk=self.kwargs['client_id'])

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if 'client_id' in self.kwargs:
            context['client'] = get_object_or_404(Client, pk=self.kwargs['client_id'])
        try:
            context['user_form'] = self.user_form_class(instance=self.object.user)
        except AttributeError:
            context['user_form'] = self.user_form_class()
        return context


class ClientUserUpdate(ClientUserMixin, UpdateView):
    model = ClientUser
    form_class = forms.ClientUserForm
    user_form_class = forms.UserForm
    template_name = 'mgmt/contact_form.html'
    create_method = False

    def get_object(self):
        return get_object_or_404(ClientUser, pk=self.kwargs['clientuser_id'])

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['client'] = self.object.client
        context['user_form'] = self.user_form_class(instance=self.object.user)
        logger.info(f'{self.request.user} viewed contact {self.object.user} for {self.object.client}')
        return context


class ClientUserDelete(AjaxableResponseMixin, DeleteView):
    model = ClientUser

    def get_object(self):
        return get_object_or_404(ClientUser, pk=self.kwargs['clientuser_id'])

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        logger.info(f'{self.request.user} deleted contact {self.object.user} for {self.object.client}')
        self.object.delete()
        data = {
            'success': True,
            'pk': self.object.pk,
        }
        return JsonResponse(data)

    def get_success_url(self):
        return reverse_lazy('mgmt:profile', kwargs={'client_id': self.object.client.id})


class ProductCreate(AjaxableResponseMixin, CreateView):
    model = Product
    form_class = forms.ProductForm
    template_name = 'mgmt/product_form.html'
#    fields = ['client', 'first_name', 'last_name', 'password', 'title', 'email', 'phone_number', 'phone_extension', 'mobile_number', 'fax_number', 'notes']

    def form_valid(self, form):
        logger.info(form.data)
        response = super(ProductCreate, self).form_valid(form)
#        self.object.units_inventory = form.cleaned_data['cases_inventory'] * form.cleaned_data['packing']
        self.object.save()
        ActionLog.objects.create(
            user = self.request.user,
            client = self.object.client,
            product = self.object,
            log_message = 'Created',
            app = self.request.resolver_match.app_name,
        )
        logger.info(f'{self.request.user} created product {self.object} ({self.object.id}) for {self.object.client}')
        return response

#    def get_context_data(self, *args, **kwargs):
#        logger.warning(self.kwargs)
#        context = super(CustContactCreate, self).get_context_data(*args, **kwargs)
#        if 'client_id' in self.kwargs:
#            context['client'] = get_object_or_404(Client, pk=self.kwargs['client_id'])
#        return context


class ProductUpdate(AjaxableResponseMixin, UpdateView):
    model = Product
    form_class = forms.ProductForm
    template_name = 'mgmt/product_details.html'

    def get_object(self):
        return get_object_or_404(Product, pk=self.kwargs['product_id'])

    def form_valid(self, form):
        logger.info(form.data)
#        self.object.units_inventory = form.cleaned_data['cases_inventory'] * form.cleaned_data['packing']

        self.object.cases_inventory = form.cleaned_data['cases_inventory'] + self.object.cases_unshipped

        response = super(ProductUpdate, self).form_valid(form)
        if self.object.cases_inventory != form.initial['cases_inventory']:
            ActionLog.objects.create(
                user = self.request.user,
                client = self.object.client,
                product = self.object,
                log_message = 'Updated cases to {0}'.format(self.object.cases_inventory),
                app = self.request.resolver_match.app_name,
            )
        logger.info(f'{self.request.user} updated product {self.object} ({self.object.id}) for {self.object.client}')
        return response

#    def get_context_data(self, *args, **kwargs):
#        context = super(ProductUpdate, self).get_context_data(*args, **kwargs)
#        context['last_received'] = Receivable.objects.filter(transaction__product=self.object).order_by('-date_created').first()
#        context['last_shipped'] = Shipment.objects.filter(transaction__product=self.object).order_by('-date_created').first()
#        return context


class ProductDelete(AjaxableResponseMixin, UpdateView):
    model = Product
    fields = ['is_active', 'is_deleted']

    def form_valid(self, form):
        logger.info(form.data)
        response = super(ProductDelete, self).form_valid(form)
        if self.object.is_active:
            log_message = 'Undeleted'
            logger.info('Product {0} ({1}) undeleted.'.format(self.object, self.object.id))
        else:
            if self.object.is_deleted:
                log_message = 'Deleted permanently'
                logger.info('Product {0} ({1}) deleted permanently.'.format(self.object, self.object.id))
            else:
                log_message = 'Deleted'
                logger.info('Product {0} ({1}) deleted.'.format(self.object, self.object.id))
        ActionLog.objects.create(
            user = self.request.user,
            client = self.object.client,
            product = self.object,
            log_message = log_message,
            app = self.request.resolver_match.app_name,
        )
        return response

    def get_object(self):
        return get_object_or_404(Product, pk=self.kwargs['product_id'])


class ProductTransfer(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, product_id):
        logger.info(request.data)
        response = {'success': True}
        from_product = get_object_or_404(Product, pk=self.kwargs['product_id'])

        cases = int(request.data.get('cases', 0))

        to_product_id = request.data.get('to_productid', None)
        # If no destination product is supplied, create a new one
        if not to_product_id:
            to_client = get_object_or_404(Client, pk=request.data.get('to_customerid', None))
            new_product = Product(
                client = to_client,
                item_number = from_product.item_number,
                client_tag = from_product.client_tag,
                name = from_product.name,
                packing = from_product.packing,
                cases_inventory = 0,
#                units_inventory = 0,
                is_active = True,
                accounting_prepay_type = from_product.accounting_prepay_type,
                contracted_quantity = from_product.contracted_quantity,
                unit_price = from_product.unit_price,
                gross_weight = from_product.gross_weight,
                length = from_product.length,
                width = from_product.width,
                height = from_product.height,
                is_domestic = from_product.is_domestic,
            )
            new_product.save()
            to_product_id = new_product.id
            logger.info('Creating new product: {0}'.format(to_product_id))

        to_product = get_object_or_404(Product, pk=to_product_id)

        # Move inventory count from one product to the other
        from_product.cases_inventory -= cases
#        from_product.units_inventory = from_product.cases_inventory * from_product.packing
        to_product.cases_inventory += cases
#        to_product.units_inventory = to_product.cases_inventory * to_product.packing
        from_product.save()
        to_product.save()

        # Create outgoing transaction
        outgoing_transaction = Transaction(
            product = from_product,
            cases_remaining = from_product.cases_available - cases,
            is_outbound = True,
            client = from_product.client,
            cases = cases,
            transfer_client = to_product.client,
            transfer_product = to_product,
            date_completed = timezone.now(),
        )
        outgoing_transaction.save()

        ActionLog.objects.create(
            user = self.request.user,
            client = from_product.client,
            product = from_product,
            log_message = 'Transferred {0} to {1}'.format(cases, to_product.id),
            app = self.request.resolver_match.app_name,
        )

        # Create incoming transaction
        incoming_transaction = Transaction(
            product = to_product,
            cases_remaining = to_product.cases_available + cases,
            is_outbound = False,
            client = to_product.client,
            cases = cases,
            transfer_client = from_product.client,
            transfer_product = from_product,
            date_completed = timezone.now(),
        )
        incoming_transaction.save()

        ActionLog.objects.create(
            user = self.request.user,
            client = to_product.client,
            product = to_product,
            log_message = 'Transferred {0} from {1}'.format(cases, from_product.id),
            app = self.request.resolver_match.app_name,
        )

        logger.info(f'{self.request.user} transferred product {from_product} ({from_product.client}) to {to_product} ({to_product.client})')

        return Response(response)


class ProductReturn(AjaxableResponseMixin, CreateView):
    model = ReturnedProduct
    form_class = forms.ReturnedProductForm
    template_name = 'mgmt/product_detail.html'

    def form_valid(self, form):
        logger.info(form.data)
        product = get_object_or_404(Product, pk=self.kwargs['product_id'])
        returned_product = form.save(commit=False)
        returned_product.product = product
        returned_product.client = product.client
        returned_product.save()

        if form.cleaned_data['cases_undamaged']:
            return_receivable = Receivable(
                client = product.client,
                date_created = timezone.now(),
                date_received = form.cleaned_data['date_returned'],
                product = product,
                cases = form.cleaned_data['cases_undamaged'],
                returned_product = returned_product,
            )
            return_receivable.save()

            product.cases_inventory += form.cleaned_data['cases_undamaged']
            product.save()

            transaction = Transaction(
                date_created = timezone.now(),
                product = product,
                client = product.client,
                is_outbound = False,
                receivable = return_receivable,
                cases = form.cleaned_data['cases_undamaged'],
                cases_remaining = product.cases_inventory,
            )
            transaction.save()

        logger.info(f'{self.request.user} created return {returned_product} for {returned_product.client}')
        logger.info(f'{returned_product.cases_damaged} damaged / {returned_product.cases_undamaged} undamaged\t{returned_product.product}')

        response = super(ProductReturn, self).form_valid(form)
        return response

#    def get_success_url(self):
#        return reverse_lazy('mgmt:product-history', kwargs={'product_id': self.object.product.id})


class ReceivableCreate(AjaxableResponseMixin, CreateView):
    model = Receivable
    form_class = forms.ReceivableForm
    template_name = 'mgmt/receivable.html'

    def form_valid(self, form):
        logger.info(form.data)
        response = super(ReceivableCreate, self).form_valid(form)
        transaction = Transaction(
            date_created = self.object.date_received,
            product = self.object.product,
            client = self.object.client,
            is_outbound = False,
            shipment_order = self.object.shipment_order,
            receivable = self.object,
        )
        transaction.save()
        logger.info(f'{self.request.user} created receivable {self.object} for {self.object.client}')
        logger.info(f'{self.object.cases}\t{self.object.product}')
        return response

    def get_initial(self):
        cases = None
        product = get_object_or_404(Product, pk=self.kwargs['product_id'])
        if product.contracted_quantity and product.packing:
            cases = int(math.ceil(float(product.contracted_quantity) / float(product.packing)))
        return {
            'cases': cases,
        }

    def get_context_data(self, *args, **kwargs):
        context = super(ReceivableCreate, self).get_context_data(*args, **kwargs)
        product = get_object_or_404(Product, pk=self.kwargs['product_id'])
        context['product'] = product
        return context


class ReceivableConfirm(AjaxableResponseMixin, UpdateView):
    model = Receivable
    form_class = forms.ReceivableConfirmForm
    template_name = 'mgmt/receivable.html'

    def get_object(self):
        return get_object_or_404(Receivable, pk=self.kwargs['receivable_id'])

    def form_valid(self, form):
        data = {
            'success': True,
        }
        logger.info(f'Receivable {form.instance} processed by {self.request.user} via {self.request.resolver_match.app_name}')
        # logger.info(form.data)
        # logger.info(form.cleaned_data)
        # self.object.units_inventory = int(form.data['cases_inventory']) * int(form.data['packing'])
        # self.object.purchase_order = form.cleaned_data['purchase_order']
        # self.object.shipment_order = form.cleaned_data['shipment_order']
        self.object.cases = form.initial['cases']

        # If we received more cases than expected, return an error
        # if form.cleaned_data['cases'] > self.object.cases:
        #     data = {
        #         'success': False,
        #         'message': 'More cases entered than expected1.',
        #     }
        #     logger.warning(f"More cases ({form.cleaned_data['cases']}) entered than expected ({self.object.cases}).")
        #     return JsonResponse(data)

        action_log = ActionLog.objects.create(
            user = self.request.user,
            client = self.object.client,
            product = self.object.product,
            log_message = 'Receivable {0} updated. {1} cases added'.format(self.object.id, form.cleaned_data['cases']),
            app = self.request.resolver_match.app_name,
        )
        logger.info(action_log.log_message)

        # If we received fewer cases than expected, create a new receivable with the remainder
        if form.cleaned_data['cases'] < self.object.cases:
            split_receivable = Receivable(
                client = self.object.client,
                date_created = timezone.now(),
                date_received = self.object.date_received,
                purchase_order = form.cleaned_data['purchase_order'],
                shipment_order = form.cleaned_data['shipment_order'],
                product = self.object.product,
                cases = self.object.cases - form.cleaned_data['cases'],
            )
            split_receivable.save()

            transaction = Transaction(
                date_created = timezone.now(),
                product = self.object.product,
                client = self.object.client,
                is_outbound = False,
                shipment_order = self.object.shipment_order,
                receivable = split_receivable,
            )
            transaction.save()

            logger.info(f'Receivable {split_receivable} created with {split_receivable.cases} cases, split from {self.object} with {self.object.cases} expected.')

            data['warning'] = 'Fewer cases entered than expected.'


        # Update transaction with number of cases received
        transaction = self.object.transaction_set.first()
        transaction.cases = form.cleaned_data['cases']
        transaction.purchase_order = form.cleaned_data['purchase_order']
        transaction.shipment_order = form.cleaned_data['shipment_order']
        logger.info(transaction.product.packing)
        transaction.cases_remaining = transaction.product.cases_inventory + int(transaction.cases)
        transaction.date_completed = timezone.now()
        transaction.save()

        # Update product quantity
        self.object.product.cases_inventory += form.cleaned_data['cases']
#        self.object.product.units_inventory = self.object.product.cases_inventory * self.object.product.packing
        self.object.product.save()

        logger.info(self.object.purchase_order)
        logger.info(self.object.shipment_order)
        self.object.save()

#        response = super(ReceivableConfirm, self).form_valid(form)
        logger.info('Receivable {0} confirmed.'.format(self.object.id))
#        return response
        return JsonResponse(data)

#    def get_context_data(self, *args, **kwargs):
#        context = super(ReceivableCreate, self).get_context_data(*args, **kwargs)
#        product = get_object_or_404(Product, pk=self.kwargs['product_id'])
#        context['product'] = product
#        return context


class ReceivableDelete(AjaxableResponseMixin, DeleteView):
    model = Receivable

    def get_object(self):
        return get_object_or_404(Receivable, pk=self.kwargs['receivable_id'])

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        logger.info(f'{request.user} deleted receivable {self.object}, transaction {self.object.transaction}')
        ActionLog.objects.create(
            user=self.request.user,
            client=self.object.client,
            product=self.object.transaction.product,
            log_message=f'Deleted receivable {self.object}, transaction {self.object.transaction} with {self.object.cases} cases',
            app=self.request.resolver_match.app_name,
        )
        self.object.delete()
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse_lazy('mgmt:product-history', kwargs={'product_id': self.object.product.id})


class ShipmentDetail(DetailView):
    model = Shipment
    pk_url_kwarg = 'shipment_id'
    template_name = 'mgmt/shipment_detail.html'


class ShipmentDelete(AjaxableResponseMixin, DeleteView):
    model = Shipment

    def get_object(self):
        return get_object_or_404(Shipment, pk=self.kwargs['shipment_id'])

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        logger.info(f'{request.user} deleted shipment {self.object}')
        ActionLog.objects.create(
            user=self.request.user,
            client=self.object.client,
            product=None,
            log_message=f'Deleted shipment {self.object}',
            app=self.request.resolver_match.app_name,
        )
        self.object.delete()
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse_lazy('mgmt:shipments', kwargs={'client_id': self.object.client.id})


# Tools

class ActionLogTable(tables.Table):
    class Meta:
        model = ActionLog
        template_name = 'django_tables2/infotable.html'


#class ActionLogFilter(FilterSet):
#    class Meta:
#        model = ActionLog
#        fields = ['product',]


#class FilteredActionLogListView(SingleTableMixin, FilterView):
#    table_class = ActionLogTable
#    model = ActionLog
#    template_name = 'mgmt/action_log.html'

#    filterset_class = ActionLogFilter


def action_log(request):
    logs = ActionLog.objects.all()

    product_id = request.GET.get('product_id', None)
    if product_id:
        product = get_object_or_404(Product, pk=product_id)
        logs = logs.filter(product=product)

    client_id = request.GET.get('client_id', None)
    if client_id:
        client = get_object_or_404(Client, pk=client_id)
        logs = logs.filter(client=client)

    logs_table = ActionLogTable(logs)
    tables.RequestConfig(request).configure(logs_table)

    logger.info(f'{request.user} viewed action logs for product {product_id}, client {client_id}')
    context = {
        'logs_table': logs_table,
    }
    return render(request, 'mgmt/action_log.html', context)


def search(request):

    search_params = request.GET.dict()
    context = search_params

    transactions = Transaction.objects.filter(is_outbound=True).order_by('-shipment__date_created')
    if search_params.get('search_itemnum'):
        transactions = transactions.filter(product__item_number=search_params['search_itemnum'])
        context['search_itemnum'] = get_valid_filename(context['search_itemnum'])
    if search_params.get('search_shipmentid'):
        transactions = transactions.filter(shipment__id=search_params['search_shipmentid'])
    if search_params.get('search_shippedon'):
        date_filter = datetime.strptime(search_params['search_shippedon'], '%m/%d/%Y')
        transactions = transactions.annotate(date_shipped_day = Trunc('shipment__date_shipped', 'day')).filter(date_shipped_day=date_filter)
    if search_params.get('search_client'):
        transactions = transactions.filter(client__company_name__icontains=search_params['search_client'])
    if search_params.get('search_so'):
        transactions = transactions.filter(shipment_order=search_params['search_so'])
    if search_params.get('search_po'):
        transactions = transactions.filter(shipment__purchase_order=search_params['search_po'])
    if search_params.get('search_carrier'):
        transactions = transactions.filter(shipment__carrier__icontains=search_params['search_carrier'])
    if search_params.get('search_location'):
        transactions = transactions.filter(shipment__location__name__icontains=search_params['search_location'])

    logger.info(f'{request.user} performed search: {search_params}')
    context['transactions'] = transactions[0:50]

    return render(request, 'mgmt/search.html', context)


class AbstractReport(APIView):

    def launch_report_task(self):
        raise NotImplementedError

    def post(self, *args, **kwargs):
        async_task = self.launch_report_task()

        result = {
            'success': True,
            'task_id': async_task.id,
        }
        return JsonResponse(result)


class ItemLookupReport(AbstractReport):

    def launch_report_task(self):
        item_number = self.request.data['itemnum']
        report_task_name = f'ItemLookup-{item_number}'
        async_task = AsyncTask.objects.create(name=report_task_name, user=self.request.user)
        tasks.generate_item_lookup.delay(async_task.id, item_number)
        logger.info(f'{self.request.user} generated item lookup report for {item_number}, async task {async_task.id}')
        return async_task


class InventoryListReport(AbstractReport):

    def launch_report_task(self):
        client = get_object_or_404(Client, pk=self.request.data['client'])
        report_task_name = f'InventoryList-{client.company_name}'
        async_task = AsyncTask.objects.create(name=report_task_name, user=self.request.user)
        tasks.generate_inventory_list.delay(async_task.id, client.id, self.request.data['fromdate'], self.request.data['todate'])
        logger.info(f'{self.request.user} generated inventory list report for {client}, async task {async_task.id}')
        return async_task


class ClientInventoryListReport(AbstractReport):

    def launch_report_task(self):
        client = get_object_or_404(Client, pk=self.request.data['client'])
        report_task_name = f'ClientInventoryList-{client.company_name}'
        async_task = AsyncTask.objects.create(name=report_task_name, user=self.request.user)
        tasks.generate_client_inventory_list.delay(async_task.id, client.id, self.request.data['ondate'])
        logger.info(f'{self.request.user} generated client inventory list report for {client}, async task {async_task.id}')
        return async_task


class DeliveryListReport(AbstractReport):

    def launch_report_task(self):
        client = get_object_or_404(Client, pk=self.request.data['client'])
        report_task_name = f'ClientDeliveryList-{client.company_name}'
        async_task = AsyncTask.objects.create(name=report_task_name, user=self.request.user)
        tasks.generate_delivery_list.delay(async_task.id, client.id, self.request.data['fromdate'], self.request.data['todate'])
        logger.info(f'{self.request.user} generated delivery list report for {client}, async task {async_task.id}')
        return async_task


class IncomingListReport(AbstractReport):

    def launch_report_task(self):
        client = get_object_or_404(Client, pk=self.request.data['client'])
        report_task_name = f'ClientIncomingList-{client.company_name}'
        async_task = AsyncTask.objects.create(name=report_task_name, user=self.request.user)
        tasks.generate_incoming_list.delay(async_task.id, client.id, self.request.data['fromdate'], self.request.data['todate'])
        logger.info(f'{self.request.user} generated incoming list report for {client}, async task {async_task.id}')
        return async_task


class ProductListReport(AbstractReport):

    def launch_report_task(self):
        client_id = self.request.data.get('client')
        client_name = 'All Clients'
        if client_id:
            client = get_object_or_404(Client, pk=client_id)
            client_name = client.company_name

        report_task_name = f'ProductList-{client_name}'
        async_task = AsyncTask.objects.create(name=report_task_name, user=self.request.user)
        tasks.generate_product_list.delay(async_task.id, client_id)
        logger.info(f'{self.request.user} generated product list report for {client_name}, async task {async_task.id}')
        return async_task


class LocationListReport(AbstractReport):

    def launch_report_task(self):
        client = get_object_or_404(Client, pk=self.request.data['client'])
        report_task_name = f'LocationList-{client.company_name}'
        async_task = AsyncTask.objects.create(name=report_task_name, user=self.request.user)
        tasks.generate_location_list.delay(async_task.id, client.id)
        logger.info(f'{self.request.user} generated location list report for {client}, async task {async_task.id}')
        return async_task


class ContactListReport(AbstractReport):

    def launch_report_task(self):
        client = get_object_or_404(Client, pk=self.request.data['client'])
        report_task_name = f'ContactList-{client.company_name}'
        async_task = AsyncTask.objects.create(name=report_task_name, user=self.request.user)
        tasks.generate_contact_list.delay(async_task.id, client.id)
        logger.info(f'{self.request.user} generated contact list report for {client}, async task {async_task.id}')
        return async_task
