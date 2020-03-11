from django.conf import settings
from django.core import mail
from django.template import Context
from django.template.loader import get_template
from django.utils import timezone
from django.urls import reverse
from django.test import override_settings

from celery import shared_task
from celery.utils.log import get_task_logger

from django_pdfkit import PDFView

from datetime import datetime, timedelta
from dateutil import rrule
import csv
import math
import os
import pdfkit

from ims.models import AsyncTask, Client, Product, Shipment, Transaction
# from warehouse.views import PurchaseOrderView
from ims import utils

import logging
logger = logging.getLogger(__name__)


@shared_task
def generate_item_lookup(async_task_id, item_number):

    async_task = AsyncTask.objects.get(pk=async_task_id)
    products = Product.objects.filter(item_number=item_number)

    now = timezone.now()

    filename = 'ItemLookup - {0} - {1}.csv'.format(item_number, timezone.now().strftime('%m-%d-%Y %H%M%S'))
    with open('{0}/reports/{1}'.format(settings.MEDIA_ROOT, filename), mode='w') as csvfile:

        writer = csv.writer(csvfile)

#    response = HttpResponse(content_type='text/csv')
#    response['Content-Disposition'] = 'attachment; filename="ItemLookup-{0}.csv"'.format(item_number)

#    writer = csv.writer(response)
        writer.writerow([
            'CURRENT Date',
            'Item Number',
            'Client Name',
            'Item Description',
            'Packing per Case',
            'Current Case Count',
            'Current Quantity',
            'Status',
        ])
        for product in products:
            writer.writerow([
                now.strftime('%m/%d/%Y'),
                product.item_number_force_string,
                product.client.company_name,
                product.name,
                product.packing,
                product.cases_inventory,
                product.units_inventory,
                'Active' if product.is_active else 'Inactive',
            ])

    logger.info('Done writing CSV')
    async_task.is_complete = True
    async_task.percent_complete = 100
    async_task.result_file = 'reports/{0}'.format(filename)
    async_task.result_content_type = 'text/csv'
    async_task.save()

    return 'done'


@shared_task
def generate_inventory_list(async_task_id, client_id, fromdate, todate):

    async_task = AsyncTask.objects.get(pk=async_task_id)
    client = Client.objects.get(pk=client_id)
    client_tree = [c['obj'] for c in client.children]

    date_to = timezone.now() + timedelta(days=30)
    date_from = timezone.now() - timedelta(days=365)
    try:
        date_from = datetime.strptime(fromdate, '%m/%d/%Y')
        date_to = datetime.strptime(todate, '%m/%d/%Y')
    except:
        pass

    products = Product.objects.filter(client__in=client_tree, is_deleted=False).order_by('item_number')
#    shipments = Shipment.objects.filter(client=client, date_shipped__gt=date_from, date_shipped__lte=date_to)
#    non_shipment_transactions = Transaction.objects.filter(client=client, shipment__isnull=True, date_created__gt=date_from, date_created__lte=date_to)
#    transactions = Transaction.objects.filter(client=client, date_created__gt=date_from, date_created__lte=date_to)
    transactions = Transaction.objects.filter(client__in=client_tree, date_created__gt=date_from)

#    transactions = Transaction.objects.filter(date_created__gt=date_from, date_created__lte=date_to)
#    transactions = transactions.annotate(date_requested=Trunc(Coalesce('receivable__date_created', 'date_created'), 'day'))
#    transactions = transactions.annotate(date_in_out=Trunc(Coalesce('shipment__date_shipped', 'date_created'), 'day'))
#    transactions = transactions.order_by('-date_in_out', '-shipment__id')

    product_counts = {}
    columns = []
    status_update_interval = transactions.count() / 20
    for i, transaction in enumerate(transactions):
        if transactions.count() > 1000 and i % status_update_interval == 0:
            async_task.percent_complete = math.ceil(i / float(transactions.count()) * 100)
            async_task.save()
            logger.info(i)
            logger.info(async_task.percent_complete)

        if transaction.shipment:
            if transaction.shipment.date_shipped:
                column_id = 'DL#{0} {1}'.format(transaction.shipment.id, transaction.shipment.date_shipped.strftime('%m/%d/%Y'))
            else:
                column_id = 'DL#{0}'.format(transaction.shipment.id)
            if not column_id in product_counts:
                product_counts[column_id] = {}
            product_counts[column_id][transaction.product.id] = {
                'in': 0,
                'out': transaction.cases,
            }
        elif transaction.is_transfer:
            column_id = 'T#{0} {1}'.format(transaction.id, transaction.date_created.strftime('%m/%d/%Y'))
            if not column_id in product_counts:
                product_counts[column_id] = {}
            product_counts[column_id][transaction.product.id] = {
                'in': transaction.cases if not transaction.is_outbound else 0,
                'out': transaction.cases if transaction.is_outbound else 0,
            }
        else:
            column_id = 'SO: {0} {1}'.format(transaction.shipment_order, transaction.date_created.strftime('%m/%d/%Y'))
            if not column_id in product_counts:
                product_counts[column_id] = {}
            product_counts[column_id][transaction.product.id] = {
                'in': transaction.cases,
                'out': 0,
            }
        if not column_id in [column['id'] for column in columns]:
#        if not column_id in column_ids:
            column_date = transaction.date_created
            shipment_id = transaction.id
            if transaction.shipment:
                shipment_id = transaction.shipment.id
                column_date = transaction.shipment.date_shipped
            try:
                column_date = column_date.date()
            except AttributeError:
                column_date = timezone.now().date()
            columns.append({
                'id': column_id,
                'date': column_date,
                'shipment_id': shipment_id,
                'is_month_end': False,
            })
#            logger.info('{0} {1}'.format(shipment_id, column_id))
#            column_ids[column_id] = True

    async_task.percent_complete = 100
    async_task.save()
    logger.info('done with transactions')

    # Do end-of-month columns
    month_begin = date_from.replace(day=1)
    month_end = date_to.replace(day=1)
    for dt in rrule.rrule(rrule.MONTHLY, dtstart=month_begin, until=month_end):
        if dt > date_from and dt <= date_to:
            previous_day = dt - timedelta(days=1)
            column_id = 'End {0}'.format(previous_day.strftime('%b %Y'))
            columns.append({
                'id': column_id,
                'date': dt.date(),
                'shipment_id': 0,
                'is_month_end': True,
            })
            product_counts[column_id] = {}

    columns = sorted(columns, key=lambda column_data: (column_data['date'], column_data['shipment_id']), reverse=True)

    product_balance = {}
    for product in products:
#        product_balance[product.id] = product.cases_inventory
        product_balance[product.id] = product.cases_available

    for column in columns:
#        logger.info('{0} {1} {2}'.format(column['shipment_id'], column['date'], column['id']))
        for product in products:
#            if column['is_month_end']:
#                product_counts[column['id'][product.id] = {'in': 0, 'out': 0}
            if not product.id in product_counts[column['id']]:
                product_counts[column['id']][product.id] = {'in': 0, 'out': 0}

            product_counts[column['id']][product.id]['balance'] = product_balance[product.id]
            if product_counts[column['id']][product.id]['in']:
                product_balance[product.id] -= product_counts[column['id']][product.id]['in']
            if product_counts[column['id']][product.id]['out']:
                product_balance[product.id] += product_counts[column['id']][product.id]['out']
#            product_counts[column['id']][product.id]['balance'] = product_balance[product.id]
#        logger.info(product_counts[column['id']][2310])

#        response.write(product_counts)
#        response.write(columns)
#        response.write('{0}\n'.format(history_item.id))

    filename = 'InventoryList - {0} - {1}.csv'.format(client.company_name_clean, timezone.now().strftime('%m-%d-%Y %H%M%S'))
    with open('{0}/reports/{1}'.format(settings.MEDIA_ROOT, filename), mode='w') as csvfile:
#    with open('{0}/reports/InventoryList.csv'.format(settings.MEDIA_ROOT), mode='w') as csvfile:
        writer = csv.writer(csvfile)

        columns = sorted(columns, key=lambda column_data: (column_data['date'], column_data['shipment_id']))
        columns = [column for column in columns if column['date'] < date_to.date()]

        writer.writerow(['Item #', 'Client ID', 'Description', 'Packing/cs', 'Recvd/Deliv'] + [column['id'] for column in columns])

        for product in products:
            writer.writerow([
                product.item_number_force_string,
                product.client_tag,
                product.name,
                product.packing,
                'IN',
            ] + [product_counts[column['id']][product.id]['in'] for column in columns])
            writer.writerow([
                product.item_number_force_string,
                product.client_tag,
                product.name,
                product.packing,
                'OUT',
            ] + [product_counts[column['id']][product.id]['out'] for column in columns])
            writer.writerow([
                product.item_number_force_string,
                product.client_tag,
                product.name,
                product.packing,
                'BAL',
            ] + [product_counts[column['id']][product.id]['balance'] for column in columns])

    logger.info('Done writing CSV')
    async_task.is_complete = True
#    async_task.result_url = '{0}reports/{1}'.format(settings.MEDIA_URL, filename)
    async_task.result_file = 'reports/{0}'.format(filename)
    async_task.result_content_type = 'text/csv'
#    async_task.result_url = reverse('mgmt:async-task-result', kwargs={'async_task_id': async_task.id})
    async_task.save()
    return 'done'
    return response


@shared_task
def generate_delivery_list(async_task_id, client_id, fromdate, todate):

    async_task = AsyncTask.objects.get(pk=async_task_id)
    client = Client.objects.get(pk=client_id)
    client_tree = [c['obj'] for c in client.children]

    date_to = timezone.now() + timedelta(days=30)
    date_from = timezone.now() - timedelta(days=365)
    try:
        date_from = datetime.strptime(fromdate, '%m/%d/%Y')
        date_to = datetime.strptime(todate, '%m/%d/%Y')
    except:
        pass

    transactions = Transaction.objects.filter(
        client__in=client_tree,
        date_created__gt=date_from,
        date_created__lte=date_to,
        shipment__status=Shipment.Status.SHIPPED
    )

    rows = []
    status_update_interval = transactions.count() / 20
    for i, transaction in enumerate(transactions):
        if transactions.count() > 100 and i % status_update_interval == 0:
            async_task.percent_complete = math.ceil(i / float(transactions.count()) * 100)
            async_task.save()
            logger.info(i)
            logger.info(async_task.percent_complete)
        if transaction.is_return:
            rows.append({
                'date': transaction.receivable.returned_product.date_returned.date(),
                'shipment_id': 'RETURN',
                'location': transaction.receivable.returned_product.location.name,
                'item_number': transaction.product.item_number_force_string,
                'client_tag': transaction.product.client_tag,
                'product_name': transaction.product.name,
                'month': transaction.receivable.returned_product.date_returned.month,
                'year': transaction.receivable.returned_product.date_returned.year,
                'cases': transaction.receivable.returned_product.cases_undamaged,
                'packing': transaction.product.packing,
                'units': transaction.total_quantity,
            })
        elif transaction.shipment:
            rows.append({
                'date': transaction.shipment.date_shipped.date(),
                'shipment_id': transaction.shipment.id,
                'location': transaction.shipment.location.name,
                'item_number': transaction.product.item_number_force_string,
                'client_tag': transaction.product.client_tag,
                'product_name': transaction.product.name,
                'month': transaction.shipment.date_shipped.month,
                'year': transaction.shipment.date_shipped.year,
                'cases': transaction.cases * -1,
                'packing': transaction.product.packing,
                'units': transaction.total_quantity * -1,
            })

    filename = 'DeliveryList - {0} - {1}.csv'.format(client.company_name_clean, timezone.now().strftime('%m-%d-%Y %H%M%S'))
    with open('{0}/reports/{1}'.format(settings.MEDIA_ROOT, filename), mode='w') as csvfile:

        writer = csv.writer(csvfile)
        writer.writerow([
            'Date',
            'DL #',
            'Store',
            'SKU #',
            'Client ID',
            'SKU Desc',
            'Month',
            'Year',
            'Cases Out Total',
            'PACKING per case by DL history',
            'QTY Pcs',
        ])
        for row in sorted(rows, key=lambda row_data: (row_data['date'], row_data['shipment_id'])):
            writer.writerow([
                row['date'].strftime('%m/%d/%Y'),
                row['shipment_id'],
                row['location'],
                row['item_number'],
                row['client_tag'],
                row['product_name'],
                row['month'],
                row['year'],
                row['cases'],
                row['packing'],
                row['units'],
            ])

    logger.info('Done writing CSV')
    async_task.is_complete = True
    async_task.percent_complete = 100
    async_task.result_file = 'reports/{0}'.format(filename)
    async_task.result_content_type = 'text/csv'
    async_task.save()

    return 'done'


@shared_task
def generate_incoming_list(async_task_id, client_id, fromdate, todate):

    async_task = AsyncTask.objects.get(pk=async_task_id)
    client = Client.objects.get(pk=client_id)
    client_tree = [c['obj'] for c in client.children]

    date_to = timezone.now() + timedelta(days=30)
    date_from = timezone.now() - timedelta(days=365)
    try:
        date_from = datetime.strptime(fromdate, '%m/%d/%Y')
        date_to = datetime.strptime(todate, '%m/%d/%Y')
    except:
        pass

    transactions = Transaction.objects.filter(client__in=client_tree, date_created__gt=date_from, date_created__lte=date_to)

    rows = []
    status_update_interval = transactions.count() / 20
    for i, transaction in enumerate(transactions):
        if transactions.count() > 100 and i % status_update_interval == 0:
            async_task.percent_complete = math.ceil(i / float(transactions.count()) * 100)
            async_task.save()
            logger.info(i)
            logger.info(async_task.percent_complete)

        if transaction.receivable or transaction.is_transfer:
            cases = transaction.cases
            units = transaction.total_quantity
            if transaction.is_transfer:
                if transaction.is_outbound:
                    purchase_order = 'TRANSFER OUT'
                    cases *= -1
                    units *= -1
                else:
                    purchase_order = 'TRANSFER IN'
            elif transaction.receivable:
                purchase_order = transaction.receivable.purchase_order

            rows.append({
                'date': transaction.date_created.date(),
                'month': transaction.date_created.month,
                'year': transaction.date_created.year,
                'purchase_order': purchase_order,
                'shipment_order': transaction.shipment_order,
                'item_number': transaction.product.item_number_force_string,
                'client_tag': transaction.product.client_tag,
                'product_name': transaction.product.name,
                'cases': cases,
                'packing': transaction.product.packing,
                'units': units,
            })

    filename = 'IncomingList - {0} - {1}.csv'.format(client.company_name_clean, timezone.now().strftime('%m-%d-%Y %H%M%S'))
    with open('{0}/reports/{1}'.format(settings.MEDIA_ROOT, filename), mode='w') as csvfile:

        writer = csv.writer(csvfile)
        writer.writerow([
            'Date',
            'Month',
            'Year',
            'PO #',
            'SO #',
            'Item #',
            'Client ID',
            'Description',
            'Cases In',
            'PACKING per case',
            'QTY Pcs',
        ])
        for row in sorted(rows, key=lambda row_data: row_data['date']):
            writer.writerow([
                row['date'].strftime('%m/%d/%Y'),
                row['month'],
                row['year'],
                row['purchase_order'],
                row['shipment_order'],
                row['item_number'],
                row['client_tag'],
                row['product_name'],
                row['cases'],
                row['packing'],
                row['units'],
            ])

    logger.info('Done writing CSV')
    async_task.is_complete = True
    async_task.percent_complete = 100
    async_task.result_file = 'reports/{0}'.format(filename)
    async_task.result_content_type = 'text/csv'
    async_task.save()

    return 'done'


@shared_task
def generate_location_list(async_task_id, client_id):

    async_task = AsyncTask.objects.get(pk=async_task_id)
    client = Client.objects.get(pk=client_id)

    filename = 'LocationList - {0} - {1}.csv'.format(client.company_name_clean, timezone.now().strftime('%m-%d-%Y %H%M%S'))
    with open('{0}/reports/{1}'.format(settings.MEDIA_ROOT, filename), mode='w') as csvfile:

        writer = csv.writer(csvfile)
        writer.writerow([
            'Name',
            'Address',
            'Address 2',
            'City',
            'State',
            'ZIP',
            'Contact',
            'Email',
            'Phone',
        ])
        for location in client.location_set.filter(is_active=True):
            writer.writerow([
                location.name,
                location.address,
                location.address_2,
                location.city,
                location.state,
                location.postal_code,
                location.contact_user.user.full_name,
                location.contact_user.user.email,
                location.contact_user.user.phone_number,
            ])

    logger.info('Done writing CSV')
    async_task.is_complete = True
    async_task.percent_complete = 100
    async_task.result_file = 'reports/{0}'.format(filename)
    async_task.result_content_type = 'text/csv'
    async_task.save()

    return 'done'


@shared_task
def generate_contact_list(async_task_id, client_id):

    async_task = AsyncTask.objects.get(pk=async_task_id)
    client = Client.objects.get(pk=client_id)

    filename = 'ContactList - {0} - {1}.csv'.format(client.company_name_clean, timezone.now().strftime('%m-%d-%Y %H%M%S'))
    with open('{0}/reports/{1}'.format(settings.MEDIA_ROOT, filename), mode='w') as csvfile:

        writer = csv.writer(csvfile)
        writer.writerow([
            'Email',
            'First Name',
            'Last Name',
            'Title',
            'Phone',
            'Ext',
            'Fax',
            'Mobile',
        ])
        for client_user in client.contacts.all():
            writer.writerow([
                client_user.user.email,
                client_user.user.first_name,
                client_user.user.last_name,
                client_user.title,
                client_user.user.phone_number,
                client_user.user.phone_extension,
                client_user.user.fax_number,
                client_user.user.mobile_number,
            ])

    logger.info('Done writing CSV')
    async_task.is_complete = True
    async_task.percent_complete = 100
    async_task.result_file = 'reports/{0}'.format(filename)
    async_task.result_content_type = 'text/csv'
    async_task.save()

    return 'done'


@shared_task
def email_purchase_order(request, shipment_id):

    template_name = 'warehouse/purchase_order.html'
    max_products_per_page = 20

    try:
        shipment = Shipment.objects.get(pk=shipment_id)
    except Shipment.DoesNotExist:
        return None

    static_url = '%s://%s%s' % (request['scheme'], request['host'], settings.STATIC_URL)
    media_url = '%s://%s%s' % (request['scheme'], request['host'], settings.MEDIA_URL)

    with override_settings(STATIC_URL=static_url, MEDIA_URL=media_url):
        template = get_template(template_name)
        context = {
            'shipment': shipment,
            'invq_transactions': shipment.transaction_set.filter(product__accounting_prepay_type=Product.AccountingPrepayType.INVQ),
            'total_pages': int(math.ceil(float(shipment.transaction_set.count()) / float(max_products_per_page))),
            'max_products_per_page': max_products_per_page,
            'remainder_rows': list(range(max_products_per_page - (shipment.transaction_set.count() % max_products_per_page))),
        }
        context['pages'] = list(range(context['total_pages']))

        html = template.render(context)

    options = {
        'page-size': 'Letter',
        'margin-top': '0.52in',
        'margin-right': '0.25in',
        'margin-bottom': '0.0in',
        'margin-left': '0.25in',
        'encoding': "UTF-8",
        'no-outline': None,
    }

    kwargs = {}
    wkhtmltopdf_bin = os.environ.get('WKHTMLTOPDF_BIN')
    if wkhtmltopdf_bin:
        kwargs['configuration'] = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_bin)

    pdf = pdfkit.from_string(html, False, options, **kwargs)

    attachments = []
    attachments.append({'filename': f'po-{shipment.id}', 'content': pdf, 'mimetype': 'application/pdf'})

    email_context = {
        'shipment': shipment,
    }

    utils.send_templated_email(
        [settings.PO_EMAIL],
        email_context,
        'Purchase Order for {0} - DL {1}'.format(shipment.client.company_name, shipment.id),
        'email/purchase_order.txt',
        'email/purchase_order.html',
        attachments=attachments,
    )

    return 'done'
