from django.conf import settings


def settings_constants(request):

    context = {
        'support_email': settings.SUPPORT_EMAIL,
        'site_email': settings.SITE_EMAIL,
        'delivery_email': settings.DELIVERY_EMAIL,
        'company_phone_number': settings.COMPANY_PHONE_NUMBER,
    }
    return context

