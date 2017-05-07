# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin


from ims.models import Client

import logging
logger = logging.getLogger(__name__)


class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'created_on', 'company_name',)
    list_editable = ()
    list_filter = ()
admin.site.register(Client, ClientAdmin)
