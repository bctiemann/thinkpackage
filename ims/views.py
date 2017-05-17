# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Func, F, Count
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse

from ims.models import User, Client, Shipment, Transaction, Product, CustContact, Location
from ims.forms import LocationForm, CustContactForm
from ims import utils

import logging
logger = logging.getLogger(__name__)


def home(request):
    context = {
    }
    return render(request, 'ims/home.html', context)


def mgmt(request):

    delivery_requests = Shipment.objects.exclude(status=2).order_by('-date_created')

    ready_to_ship = Shipment.objects.filter(status=1).order_by('-date_created')

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

    invq = Shipment.objects.filter(status=2, transaction__product__account_prepay_type=1, accounting_status__in=[0, 1]) \
        .order_by('-date_created') \
        .annotate(date=Func(F('date_created'), function='DATE')) \
        .values('date', 'id', 'client__company_name', 'location__name', 'client__id') \
        .annotate(count=Count('date'))

    low_stock = []
    for product in Product.objects.filter(cases_inventory__lt=F('contracted_quantity') / 2, is_active=True).order_by('name'):
        try:
            last_shipment = Transaction.objects.filter(product=product).order_by('-date_created').first()
            low_stock.append({
                'obj': product,
                'last_shipment': last_shipment,
            })
        except Transaction.DoesNotExist:
            pass

    context = {
        'delivery_requests': delivery_requests,
        'ready_to_ship': ready_to_ship,
        'inbound_receivables': inbound_receivables,
        'invq': invq,
        'low_stock': low_stock,
    }
    return render(request, 'ims/mgmt.html', context)


def mgmt_redirect(request, client_id=None):
    return redirect('mgmt-inventory', client_id=client_id)


def mgmt_profile(request, client_id=None):
    client = get_object_or_404(Client, pk=client_id)
    all_clients = []
    for parent_client in utils.tree_to_list(Client.objects.filter(is_active=True).order_by('company_name'), sort_by='company_name'):
        indent = '&nbsp;&nbsp;&nbsp;&nbsp;'.join(['' for i in xrange(parent_client['depth'])])
        parent_client['indent'] = indent
        all_clients.append(parent_client)

    context = {
        'client': client,
        'primary_contact': CustContact.objects.filter(client=client, is_primary=True).first(),
        'all_clients': all_clients,
    }
    return render(request, 'ims/mgmt_profile.html', context)


def mgmt_inventory(request, client_id=None, product_id=None):
    client = get_object_or_404(Client, pk=client_id)

    context = {
        'client': client,
    }
    return render(request, 'ims/mgmt_inventory.html', context)


def mgmt_shipments(request, client_id=None, shipment_id=None):
    client = get_object_or_404(Client, pk=client_id)

    context = {
        'client': client,
        'shipment_id': shipment_id,
    }
    return render(request, 'ims/mgmt_shipments.html', context)


def mgmt_customers_list(request):
    filter = request.GET.get('filter', None)

    clients = Client.objects.all().order_by('company_name')

    if filter == 'warehousing':
        clients = clients.filter(has_warehousing=True, is_active=True)
    elif filter == 'no-warehousing':
        clients = clients.filter(has_warehousing=False, is_active=True)
    elif filter == 'inactive':
        clients = clients.filter(is_active=False)
    else:
        clients = clients.filter(is_active=True)

    context = {
        'clients': utils.tree_to_list(clients, sort_by='company_name'),
    }
    return render(request, 'ims/mgmt_customers_list.html', context)


def mgmt_contacts_list(request, client_id):
    client = get_object_or_404(Client, pk=client_id)

    context = {
        'client': client,
    }
    return render(request, 'ims/mgmt_contacts_list.html', context)


def mgmt_locations_list(request, client_id):
    client = get_object_or_404(Client, pk=client_id)

    context = {
        'client': client,
    }
    return render(request, 'ims/mgmt_locations_list.html', context)


def mgmt_contact_form(request):
    client_id = request.GET.get('client_id', None)
    custcontact_id = request.GET.get('custcontact_id', None)

    client = get_object_or_404(Client, pk=client_id)
    custcontact = get_object_or_404(CustContact, client=client, pk=custcontact_id)

    context = {
        'custcontact': custcontact,
    }
    return render(request, 'ims/mgmt_contact_form.html', context)


def mgmt_location_form(request):
    client_id = request.GET.get('client_id', None)
    location_id = request.GET.get('location_id', None)
    logger.warning(location_id)

    client = get_object_or_404(Client, pk=client_id)
    location = get_object_or_404(Location, client=client, pk=location_id)

    context = {
        'location': location,
    }
    return render(request, 'ims/mgmt_location_form.html', context)


class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def form_invalid(self, form):
        logger.warning(form.errors)
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return HttpResponse(form.errors.as_json())
#            return HttpResponse(form.errors.as_json(), content_type='application/json')
        else:
            return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            data = {
                'success': True,
                'pk': self.object.pk,
            }
            return JsonResponse(data)
        else:
            return response


class ClientUpdate(AjaxableResponseMixin, UpdateView):
    model = Client
    template_name = 'ims/mgmt_profile.html'
    fields = ['company_name', 'is_active', 'has_warehousing', 'parent', 'notes']

    def get_object(self):
        return get_object_or_404(Client, pk=self.kwargs['client_id'])


class LocationCreate(AjaxableResponseMixin, CreateView):
    model = Location
    template_name = 'ims/mgmt_location_form.html'
    fields = ['client', 'name', 'customer_contact', 'address', 'address_2', 'city', 'state', 'zip', 'receiving_hours', 'notes']

    def get_context_data(self, *args, **kwargs):
        context = super(LocationCreate, self).get_context_data(*args, **kwargs)
        context['client'] = get_object_or_404(Client, pk=self.kwargs['client_id'])
        return context


class LocationUpdate(AjaxableResponseMixin, UpdateView):
    model = Location
    form_class = LocationForm
    template_name = 'ims/mgmt_location_form.html'
#    fields = ['name', 'customer_contact', 'address', 'address_2', 'city', 'state', 'zip', 'receiving_hours', 'notes']

    def get_object(self):
        return get_object_or_404(Location, pk=self.kwargs['location_id'])

    def get_context_data(self, *args, **kwargs):
        context = super(LocationUpdate, self).get_context_data(*args, **kwargs)
        context['client'] = self.object.client
        return context


class LocationDelete(AjaxableResponseMixin, UpdateView):
    model = Location
    fields = ['is_active']

    def get_object(self):
        return get_object_or_404(Location, pk=self.kwargs['location_id'])


class CustContactCreate(AjaxableResponseMixin, CreateView):
    model = CustContact
    template_name = 'ims/mgmt_contact_form.html'
    fields = ['client', 'first_name', 'last_name', 'password', 'title', 'email', 'phone_number', 'phone_extension', 'mobile_number', 'fax_number', 'notes']

    def get_context_data(self, *args, **kwargs):
        context = super(CustContactCreate, self).get_context_data(*args, **kwargs)
        context['client'] = get_object_or_404(Client, pk=self.kwargs['client_id'])
        return context


class CustContactUpdate(AjaxableResponseMixin, UpdateView):
    model = CustContact
    form_class = CustContactForm
    template_name = 'ims/mgmt_contact_form.html'

    def get_object(self):
        return get_object_or_404(CustContact, pk=self.kwargs['custcontact_id'])

    def form_valid(self, form):
        logger.info('Cust contact {0} ({1}) updated.'.format(self.object, self.object.id))
        response = super(CustContactUpdate, self).form_valid(form)

        if self.object.user == None and self.object.email:
            try:
                self.object.user = User.objects.get(email=self.object.email)
            except User.DoesNotExist:
                self.object.user = User.objects.create_user(
                    email = self.object.email,
                    password = self.object.password,
                )

        if form.data['password'] == '********':
            logger.info('Password unchanged')
            self.object.password = form.initial['password']
            self.object.user.set_password(self.object.password)
        else:
            logger.info('Password changed')
            self.object.user.set_password(form.data['password'])
            self.object.password = self.object.user.password
        self.object.user.save()
        self.object.save()
        return response

    def get_context_data(self, *args, **kwargs):
        context = super(CustContactUpdate, self).get_context_data(*args, **kwargs)
        context['client'] = self.object.client
        return context


class CustContactDelete(AjaxableResponseMixin, UpdateView):
    model = CustContact
    fields = ['is_active']

    def get_object(self):
        return get_object_or_404(CustContact, pk=self.kwargs['custcontact_id'])

