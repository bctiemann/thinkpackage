# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Customer(models.Model):
    customerid = models.IntegerField(primary_key=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    createdon = models.DateTimeField(auto_now_add=True)
    is_preferred = models.BooleanField(default=False, db_column='preferred')
    is_enabled = models.BooleanField(default=True, db_column='enabled')
    notes = models.TextField(blank=True)
    company_name = models.CharField(max_length=150, null=True, blank=True, db_column='coname')
    has_warehousing = models.BooleanField(default=True, db_column='warehousing')
    parent = models.ForeignKey('Customer', null=True, blank=True)

    def unicode(self):
        return (self.customer_name)

    class Meta:
        db_table = 'Customers'
