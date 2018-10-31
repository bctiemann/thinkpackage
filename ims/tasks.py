from django.conf import settings
from django.core import mail
from django.template import Context
from django.template.loader import get_template
from django.utils import timezone
from django.urls import reverse

from celery import shared_task
from celery.utils.log import get_task_logger

from datetime import datetime, timedelta
import csv
import math

from ims.models import AsyncTask, Client, Product, Shipment, Transaction

import logging
logger = logging.getLogger(__name__)


@shared_task
def generate_inventory_list(async_task_id, client_id, fromdate, todate):

    async_task = AsyncTask.objects.get(pk=async_task_id)
    client = Client.objects.get(pk=client_id)

#    async_task.is_complete = True
#    async_task.save()

#    response = HttpResponse(content_type='text/plain')
#    response = HttpResponse(content_type='text/csv')
#    response['Content-Disposition'] = 'attachment; filename="InventoryList-{0}.csv"'.format(client.company_name)
#    response['Content-Disposition'] = 'inline; filename="InventoryList-{0}.csv"'.format(client.company_name)
#    writer = csv.writer(response)

    date_to = timezone.now() + timedelta(days=30)
    date_from = timezone.now() - timedelta(days=365)
    try:
        date_from = datetime.strptime(fromdate, '%m/%d/%Y')
        date_to = datetime.strptime(todate, '%m/%d/%Y')
    except:
        pass

    products = Product.objects.filter(client=client).order_by('item_number')
#    shipments = Shipment.objects.filter(client=client, date_shipped__gt=date_from, date_shipped__lte=date_to)
#    non_shipment_transactions = Transaction.objects.filter(client=client, shipment__isnull=True, date_created__gt=date_from, date_created__lte=date_to)
    transactions = Transaction.objects.filter(client=client, date_created__gt=date_from, date_created__lte=date_to)

#    transactions = Transaction.objects.filter(date_created__gt=date_from, date_created__lte=date_to)
#    transactions = transactions.annotate(date_requested=Trunc(Coalesce('receivable__date_created', 'date_created'), 'day'))
#    transactions = transactions.annotate(date_in_out=Trunc(Coalesce('shipment__date_shipped', 'date_created'), 'day'))
#    transactions = transactions.order_by('-date_in_out', '-shipment__id')

    product_counts = {}
    columns = []
#    column_ids = {}
#    for shipment in shipments:
#        column_id = 'DL#{0} {1}'.format(shipment.id, shipment.date_shipped.strftime('%m/%d/%Y'))
#        product_counts[column_id] = {}
#        for transaction in shipment.transaction_set.all():
#            product_counts[column_id][transaction.product.id] = {'in': 0, 'out': transaction.cases}
#        columns.append({
#            'id': column_id,
#            'shipment_id': shipment.id,
#            'transaction_id': None,
#            'date': shipment.date_shipped,
#        })

#    for transaction in non_shipment_transactions:
    status_update_interval = transactions.count() / 20
    for i, transaction in enumerate(transactions):
        if i % status_update_interval == 0:
            async_task.percent_complete = math.ceil(i / float(transactions.count()) * 100)
            async_task.save()
            logger.info(i)
            logger.info(async_task.percent_complete)

        if transaction.shipment:
            column_id = 'DL#{0} {1}'.format(transaction.shipment.id, transaction.shipment.date_shipped.strftime('%m/%d/%Y'))
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
            columns.append({
                'id': column_id,
                'date': transaction.date_created,
            })
#            column_ids[column_id] = True

    async_task.percent_complete = 100
    async_task.save()
    logger.info('done with transactions')

    columns = sorted(columns, key=lambda column_data: column_data['date'], reverse=True)

    product_balance = {}
    for product in products:
        product_balance[product.id] = product.cases_inventory

    for column in columns:
        for product in products:
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

    filename = 'InventoryList - {1} - {2}.csv'.format(settings.MEDIA_ROOT, client.company_name, timezone.now().strftime('%m-%d-%Y %H:%M'))
    with open('{0}/reports/{1}'.format(settings.MEDIA_ROOT, filename), mode='w') as csvfile:
#    with open('{0}/reports/InventoryList.csv'.format(settings.MEDIA_ROOT), mode='w') as csvfile:
        writer = csv.writer(csvfile)

        columns = sorted(columns, key=lambda column_data: column_data['date'])

        writer.writerow(['Item #', 'Description', 'Packing/cs', 'Recvd/Deliv'] + [column['id'] for column in columns])

        for product in products:
            writer.writerow([
                product.item_number,
                product.name.encode('utf8'),
                product.packing,
                'IN',
            ] + [product_counts[column['id']][product.id]['in'] for column in columns])
            writer.writerow([
                product.item_number,
                product.name.encode('utf8'),
                product.packing,
                'OUT',
            ] + [product_counts[column['id']][product.id]['out'] for column in columns])
            writer.writerow([
                product.item_number,
                product.name.encode('utf8'),
                product.packing,
                'BAL',
            ] + [product_counts[column['id']][product.id]['balance'] for column in columns])

    logger.info('Done writing CSV')
    async_task.is_complete = True
#    async_task.result_url = '{0}reports/{1}'.format(settings.MEDIA_URL, filename)
    async_task.result_file = 'reports/{0}'.format(filename)
    async_task.result_content_type = 'text/csv'
    async_task.result_url = reverse('mgmt:async-task-result', kwargs={'async_task_id': async_task.id})
    async_task.save()
    return 'done'
    return response
