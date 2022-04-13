from datetime import datetime

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
            if transaction.cases_remaining_differential != transaction.cases:
                products_with_discrepancies.append({
                    'product': product,
                    'product_id': product.id,
                    'client': product.client.company_name,
                    'initial_cases': transaction.cases,
                    'differential_cases': transaction.cases_remaining_differential,
                })

        print(f'{len(products_with_discrepancies)}/{all_active_products.count()} total active products have discrepancies')
        for product in products_with_discrepancies:
            print(product)
