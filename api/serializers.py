from rest_framework import serializers

from ims.models import User, Product, AsyncTask


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'first_name', 'last_name', 'phone_number', 'phone_extension', 'fax_number']


class ClientSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    company_name = serializers.CharField(max_length=150)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'item_number', 'packing', 'cases_inventory']


class AsyncTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsyncTask
        fields = ['id', 'name', 'is_complete', 'has_failed', 'percent_complete', 'result_url', 'result_filename']
