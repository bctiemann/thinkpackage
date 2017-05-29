# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Func, F, Count
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ims.models import User, Client, Shipment, Transaction, Product, CustContact, Location, Receivable
from ims.forms import ClientForm, LocationForm, CustContactForm, ProductForm, ReceivableForm, ReceivableConfirmForm
from ims import utils

import math
from datetime import datetime, timedelta

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
    return render(request, 'ims/mgmt/home.html', context)


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
    return render(request, 'ims/mgmt/profile.html', context)


def mgmt_inventory(request, client_id=None, product_id=None):
    client = get_object_or_404(Client, pk=client_id)

    context = {
        'client': client,
        'history': request.GET.get('history', 'null'),
        'productid': request.GET.get('productid', 'null'),
    }
    return render(request, 'ims/mgmt/inventory.html', context)


def mgmt_inventory_list(request, client_id=None):
    client = get_object_or_404(Client, pk=client_id)
    try:
        active_filter = int(request.GET.get('active_filter', 0))
    except:
        active_filter = 0

    products = client.product_set.filter(is_deleted=False)

    if active_filter:
        products = products.filter(is_active=True)
    else:
        products = products.filter(is_active=False)

    context = {
        'client': client,
        'products': products,
        'active_filter': active_filter,
    }
    return render(request, 'ims/mgmt/inventory_list.html', context)


def mgmt_shipments(request, client_id=None, shipment_id=None):
    client = get_object_or_404(Client, pk=client_id)

    context = {
        'client': client,
        'shipment_id': shipment_id,
    }
    return render(request, 'ims/mgmt/shipments.html', context)


def mgmt_shipments_list(request, client_id=None):
    client = get_object_or_404(Client, pk=client_id)

    context = {
        'client': client,
    }
    return render(request, 'ims/mgmt/shipments_list.html', context)


def mgmt_product_history(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    date_to = timezone.now()
    date_from = date_to - timedelta(days=90)
    try:
        date_from = datetime.strptime(request.GET.get('fromdate', ''), '%m/%d/%Y')
        date_to = datetime.strptime(request.GET.get('todate', ''), '%m/%d/%Y')
    except:
        pass

#<CFQUERY NAME="Transactions" DATASOURCE="#DSN#">
#SELECT Transactions.*,Receivables.createdon,Receivables.PO,Receivables.cases as cases_expected,
#    Shipments.shippedon,Shipments.status as shipment_status,(Shipments.status IN (0,1) AND Shipments.shipmentid IS NOT NULL) AS shipment_pending,
#    Locations.name as location_name,Customers.coname as transfercustomer_name,count(ShipmentDocs.shipmentid) AS document_count FROM Transactions
#LEFT JOIN Shipments ON Shipments.shipmentid=Transactions.shipmentid
#LEFT JOIN Locations ON Shipments.locationid=Locations.locationid
#LEFT JOIN Receivables ON Receivables.receivableid=Transactions.receivableid
#LEFT JOIN Customers ON transfercustomerid=Customers.customerid
#LEFT JOIN ShipmentDocs ON ShipmentDocs.shipmentid=Shipments.shipmentid
#WHERE Transactions.productid=<CFQUERYPARAM value="#URL.productid#" CFSQLType="CF_SQL_NUMERIC">
#<CFIF IsDefined("URL.fromdate") AND REFind("\d{2}/\d{2}/\d{4}",URL.fromdate) GT 0>
#<CFSET fromdate = URL.fromdate>
#AND stamp > STR_TO_DATE("#URL.fromdate#","%m/%d/%Y")
#</CFIF>
#<CFIF IsDefined("URL.todate") AND REFind("\d{2}/\d{2}/\d{4}",URL.todate) GT 0>
#<CFSET todate = URL.todate>
#AND stamp < DATE_ADD(STR_TO_DATE("#URL.todate#","%m/%d/%Y"),INTERVAL 1 DAY)
#</CFIF>
#GROUP BY Transactions.transactionid
#ORDER BY shipment_pending DESC,stamp DESC
#</CFQUERY>

    history = Transaction.objects.filter(product=product, date_created__gt=date_from, date_created__lte=date_to).order_by('shipment__status', '-date_created')

    context = {
        'product': product,
        'history': history,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'ims/mgmt/product_history.html', context)


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
    return render(request, 'ims/mgmt/customers_list.html', context)


def mgmt_contacts_list(request, client_id):
    client = get_object_or_404(Client, pk=client_id)

    context = {
        'client': client,
    }
    return render(request, 'ims/mgmt/contacts_list.html', context)


def mgmt_locations_list(request, client_id):
    client = get_object_or_404(Client, pk=client_id)

    context = {
        'client': client,
    }
    return render(request, 'ims/mgmt/locations_list.html', context)


def mgmt_contact_form(request):
    client_id = request.GET.get('client_id', None)
    custcontact_id = request.GET.get('custcontact_id', None)

    client = get_object_or_404(Client, pk=client_id)
    custcontact = get_object_or_404(CustContact, client=client, pk=custcontact_id)

    context = {
        'client': client,
        'custcontact': custcontact,
    }
    return render(request, 'ims/mgmt/contact_form.html', context)


def mgmt_location_form(request):
    client_id = request.GET.get('client_id', None)
    location_id = request.GET.get('location_id', None)
    logger.warning(location_id)

    client = get_object_or_404(Client, pk=client_id)
    location = get_object_or_404(Location, client=client, pk=location_id)

    context = {
        'location': location,
    }
    return render(request, 'ims/mgmt/location_form.html', context)


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
    form_class = ClientForm
    template_name = 'ims/mgmt/profile.html'

    def get_object(self):
        return get_object_or_404(Client, pk=self.kwargs['client_id'])

    def form_valid(self, form):
        self.object.custcontact_set.update(is_primary=False)
        if form.cleaned_data['primary_contact']:
            CustContact.objects.filter(pk=form.cleaned_data['primary_contact']).update(is_primary=True)
        return super(ClientUpdate, self).form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super(ClientUpdate, self).get_context_data(*args, **kwargs)
        context['primary_contact'] = self.object.custcontact_set.filter(is_primary=True).first()
        return context


class LocationCreate(AjaxableResponseMixin, CreateView):
    model = Location
    form_class = LocationForm
    template_name = 'ims/mgmt/location_form.html'

#    def get_context_data(self, *args, **kwargs):
#        context = super(LocationCreate, self).get_context_data(*args, **kwargs)
#        context['client'] = get_object_or_404(Client, pk=self.kwargs['client_id'])
#        return context


class LocationUpdate(AjaxableResponseMixin, UpdateView):
    model = Location
    form_class = LocationForm
    template_name = 'ims/mgmt/location_form.html'

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
    form_class = CustContactForm
    template_name = 'ims/mgmt/contact_form.html'
#    fields = ['client', 'first_name', 'last_name', 'password', 'title', 'email', 'phone_number', 'phone_extension', 'mobile_number', 'fax_number', 'notes']

    def form_valid(self, form):
        response = super(CustContactCreate, self).form_valid(form)
        logger.info('Cust contact {0} ({1}) created.'.format(self.object, self.object.id))
        return response

    def get_context_data(self, *args, **kwargs):
        logger.warning(self.kwargs)
        context = super(CustContactCreate, self).get_context_data(*args, **kwargs)
        if 'client_id' in self.kwargs:
            context['client'] = get_object_or_404(Client, pk=self.kwargs['client_id'])
        return context


class CustContactUpdate(AjaxableResponseMixin, UpdateView):
    model = CustContact
    form_class = CustContactForm
    template_name = 'ims/mgmt/contact_form.html'

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


class ProductCreate(AjaxableResponseMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'ims/mgmt/product_form.html'
#    fields = ['client', 'first_name', 'last_name', 'password', 'title', 'email', 'phone_number', 'phone_extension', 'mobile_number', 'fax_number', 'notes']

    def form_valid(self, form):
        logger.warning(form.data)
        response = super(ProductCreate, self).form_valid(form)
        self.object.units_inventory = form.cleaned_data['cases_inventory'] * form.cleaned_data['packing']
        self.object.save()
        logger.info('Product {0} ({1}) created.'.format(self.object, self.object.id))
        return response

#    def get_context_data(self, *args, **kwargs):
#        logger.warning(self.kwargs)
#        context = super(CustContactCreate, self).get_context_data(*args, **kwargs)
#        if 'client_id' in self.kwargs:
#            context['client'] = get_object_or_404(Client, pk=self.kwargs['client_id'])
#        return context


class ProductUpdate(AjaxableResponseMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'ims/mgmt/product_details.html'

    def get_object(self):
        return get_object_or_404(Product, pk=self.kwargs['product_id'])

    def form_valid(self, form):
        logger.warning(form.data)
        self.object.units_inventory = form.cleaned_data['cases_inventory'] * form.cleaned_data['packing']
        response = super(ProductUpdate, self).form_valid(form)
        logger.info('Product {0} ({1}) updated.'.format(self.object, self.object.id))
        return response

    def get_context_data(self, *args, **kwargs):
        context = super(ProductUpdate, self).get_context_data(*args, **kwargs)
        context['last_received'] = Receivable.objects.filter(transaction__product=self.object).order_by('-date_created').first()
        context['last_shipped'] = Shipment.objects.filter(transaction__product=self.object).order_by('-date_created').first()
        return context


class ProductDelete(AjaxableResponseMixin, UpdateView):
    model = Product
    fields = ['is_active', 'is_deleted']

    def form_valid(self, form):
        logger.warning(form.data)
        response = super(ProductDelete, self).form_valid(form)
        if self.object.is_active:
            logger.info('Product {0} ({1}) undeleted.'.format(self.object, self.object.id))
        else:
            if self.object.is_deleted:
                logger.info('Product {0} ({1}) deleted permanently.'.format(self.object, self.object.id))
            else:
                logger.info('Product {0} ({1}) deleted.'.format(self.object, self.object.id))
        return response

    def get_object(self):
        return get_object_or_404(Product, pk=self.kwargs['product_id'])


class ProductTransfer(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, product_id):
        logger.warning(request.data)
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
                client_product_id = from_product.client_product_id,
                name = from_product.name,
                packing = from_product.packing,
                cases_inventory = 0,
                units_inventory = 0,
                is_active = True,
                account_prepay_type = from_product.account_prepay_type,
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
        from_product.units_inventory = from_product.cases_inventory * from_product.packing
        to_product.cases_inventory += cases
        to_product.units_inventory = to_product.cases_inventory * to_product.packing
        from_product.save()
        to_product.save()

        # Create outgoing transaction
        outgoing_transaction = Transaction(
            product = from_product,
            quantity = cases * from_product.packing,
            quantity_remaining = (from_product.cases_available - cases) * from_product.packing,
            is_outbound = True,
            client = from_product.client,
            cases = cases,
            transfer_client = to_product.client,
            transfer_product = to_product,
            date_completed = timezone.now(),
        )
        outgoing_transaction.save()

        # Create incoming transaction
        incoming_transaction = Transaction(
            product = to_product,
            quantity = cases * to_product.packing,
            quantity_remaining = (to_product.cases_available + cases) * to_product.packing,
            is_outbound = False,
            client = to_product.client,
            cases = cases,
            transfer_client = from_product.client,
            transfer_product = from_product,
            date_completed = timezone.now(),
        )
        incoming_transaction.save()

        logger.info('Product {0} ({1}) transferred from {2} ({3}) to {4} ({5})'.format(from_product, from_product.id, from_product.client, from_product.client.id, to_product.client, to_product.client.id))

        return Response(response)


class ReceivableCreate(AjaxableResponseMixin, CreateView):
    model = Receivable
    form_class = ReceivableForm
    template_name = 'ims/mgmt/receivable.html'

    def form_valid(self, form):
        logger.warning(form.data)
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
        logger.info('Receivable {0} created.'.format(self.object))
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
    form_class = ReceivableConfirmForm
    template_name = 'ims/mgmt/receivable.html'

    def get_object(self):
        return get_object_or_404(Receivable, pk=self.kwargs['receivable_id'])

    def form_valid(self, form):
        data = {
            'success': True,
        }
        logger.warning(form.data)
        logger.warning(form.cleaned_data)
#        self.object.units_inventory = int(form.data['cases_inventory']) * int(form.data['packing'])
#        self.object.purchase_order = form.cleaned_data['purchase_order']
#        self.object.shipment_order = form.cleaned_data['shipment_order']
        self.object.cases = form.initial['cases']

        # If we received more cases than expected, return an error
        if form.cleaned_data['cases'] > self.object.cases:
            data = {
                'success': False,
                'message': 'More cases entered than expected.',
            }
            return JsonResponse(data)

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

            logger.info('Receivable {0} created, split from {1}.'.format(split_receivable, self.object))

            data['warning'] = 'Fewer cases entered than expected.'


        # Update transaction with number of cases received
        transaction = self.object.transaction_set.first()
        transaction.cases = form.cleaned_data['cases']
        transaction.purchase_order = form.cleaned_data['purchase_order']
        transaction.shipment_order = form.cleaned_data['shipment_order']
        logger.warning(transaction.product.packing)
        transaction.quantity = int(transaction.cases) * transaction.product.packing
        transaction.quantity_remaining = (transaction.product.cases_inventory + int(transaction.cases)) * transaction.product.packing
        transaction.date_completed = timezone.now()
        transaction.save()

        # Update product quantity
        self.object.product.cases_inventory += form.cleaned_data['cases']
        self.object.product.units_inventory = self.object.product.cases_inventory * self.object.product.packing
        self.object.product.save()

        logger.warning(self.object.purchase_order)
        logger.warning(self.object.shipment_order)
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

    def get_success_url(self):
        return reverse_lazy('mgmt-product-history', kwargs={'product_id': self.object.product.id})



