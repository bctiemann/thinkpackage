from rest_framework import serializers

from ims.models import Product


class ClientSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    company_name = serializers.CharField(max_length=150)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'item_number', 'packing', 'cases_inventory']
