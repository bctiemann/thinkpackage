import json
from datetime import datetime

from django.utils import timezone
from django.core.management.base import BaseCommand

from ims.models import Product


class Command(BaseCommand):

    START_DATE = '01/01/2000'

    def handle(self, *args, **options):
        products_with_discrepancies = []

        date_from = datetime.strptime(self.START_DATE, '%m/%d/%Y')
        all_active_products = Product.objects.filter(is_active=True).exclude(client__is_active=False).order_by('client', 'id')

        for product in all_active_products:
            history = product.get_history(date_from)
            if not history:
                continue
            for transaction in history:
                pass
            initial_cases = transaction.cases or 0
            append_data = {
                'product': product.name,
                'product_id': product.id,
                'product_item_number': product.item_number,
                'client': product.client.company_name,
                'client_id': product.client.id,
                'initial_cases': initial_cases,
                'differential_cases': transaction.cases_remaining_differential,
            }
            # if product.id == 4315:
            #     print(append_data)
            if transaction.cases_remaining_differential != initial_cases:
                products_with_discrepancies.append(append_data)

        print(f'{len(products_with_discrepancies)}/{all_active_products.count()} total active products have discrepancies')
        print(json.dumps(products_with_discrepancies))

        now = timezone.now()
        filename = now.strftime('%Y%d%m-%H%M%S.json')
        with open(f'product_history/{filename}', 'a') as file:
            json.dump(products_with_discrepancies, file)
