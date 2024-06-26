from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def settings_constants(request):

    context = {
        'company_name': settings.COMPANY_NAME,
        'support_email': settings.SUPPORT_EMAIL,
        'site_email': settings.SITE_EMAIL,
        'delivery_email': settings.DELIVERY_EMAIL,
        'company_phone_number': settings.COMPANY_PHONE_NUMBER,
        'frontsite_url': settings.FRONTSITE_URL,
        'selected_client': request.selected_client,
        'one_year_ago': timezone.now() - timedelta(days=365),
        'one_month_from_now': timezone.now() + timedelta(days=31),
        'now': timezone.now(),
        'password_expire_days': settings.PASSWORD_EXPIRE_DAYS,
    }
    return context

