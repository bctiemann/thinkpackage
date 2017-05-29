from rest_framework import serializers


class ClientSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    company_name = serializers.CharField(max_length=150)


class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    item_number = serializers.CharField(max_length=12)
    packing = serializers.IntegerField()
    cases_inventory = serializers.IntegerField()
