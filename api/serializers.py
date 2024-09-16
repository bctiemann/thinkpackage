from rest_framework import serializers

from ims.models import User, Product, AsyncTask, Shipment, Transaction


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'first_name', 'last_name', 'phone_number', 'phone_extension', 'fax_number')


class ClientSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    company_name = serializers.CharField(max_length=150)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'item_number', 'packing', 'cases_inventory')


class AsyncTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsyncTask
        fields = ('id', 'name', 'is_complete', 'has_failed', 'percent_complete', 'result_url', 'result_filename')


class SPSItemSerializer(serializers.ModelSerializer):
    item = serializers.CharField(source='product.item_number')
    description = serializers.CharField(source='product.name')
    pack_size = serializers.IntegerField(source='product.packing')
    qty_cs = serializers.IntegerField(source='cases')
    unit_rate = serializers.DecimalField(source='product.unit_price', max_digits=10, decimal_places=5)
    case_price = serializers.DecimalField(source='total_price', max_digits=12, decimal_places=5)
    accounting_prepay_type = serializers.CharField(source='product.get_accounting_prepay_type_display')

    class Meta:
        model = Transaction
        fields = ('item', 'description', 'pack_size', 'qty_cs', 'unit_rate', 'case_price', 'accounting_prepay_type',)


class SPSOrderSerializer(serializers.ModelSerializer):
    po = serializers.CharField(source='id')
    po_date = serializers.DateTimeField(source='date_created')
    client_po = serializers.CharField(source='purchase_order_number')
    dl = serializers.IntegerField(source='id')
    company_name = serializers.CharField(source='client.company_name')
    contact = serializers.CharField(source='user.full_name', allow_null=True)
    job_title = serializers.CharField(source='requester_job_title')
    email = serializers.EmailField(source='user.email', allow_null=True)
    main_phone = serializers.CharField(source='user.phone_number', allow_null=True)
    subsidiary = serializers.CharField()
    client_internal_id = serializers.CharField(source='location.netsuite_client_id', allow_null=True)
    address_internal_id = serializers.CharField(source='location.netsuite_address_id', allow_null=True)
    ship_to_company = serializers.CharField(source='location.client.company_name', allow_null=True)
    ship_to_client_name = serializers.CharField(source='location.contact_user.user.full_name', allow_null=True)
    ship_to_phone = serializers.CharField(source='location.contact_user.user.phone_number', allow_null=True)
    ship_to_email = serializers.CharField(source='location.contact_user.user.email', allow_null=True)
    ship_to_address_1 = serializers.CharField(source='location.address', allow_null=True)
    ship_to_address_2 = serializers.CharField(source='location.address_2', allow_null=True)
    ship_to_city = serializers.CharField(source='location.city', allow_null=True)
    ship_to_state = serializers.CharField(source='location.state', allow_null=True)
    ship_to_zip = serializers.CharField(source='location.postal_code', allow_null=True)
    items = SPSItemSerializer(source='transaction_set.all', many=True)
    total_amount = serializers.DecimalField(source='total_price', max_digits=12, decimal_places=5)
    delivery_charge = serializers.DecimalField(max_digits=12, decimal_places=5)
    po_deadline = serializers.DateField(source='purchase_order_deadline')

    class Meta:
        model = Shipment
        fields = ('po', 'po_date', 'client_po', 'dl', 'company_name', 'contact', 'job_title',
                  'email', 'main_phone', 'subsidiary', 'client_internal_id', 'address_internal_id', 'ship_to_company',
                  'ship_to_client_name', 'ship_to_phone', 'ship_to_email', 'ship_to_address_1', 'ship_to_address_2',
                  'ship_to_city', 'ship_to_state', 'ship_to_zip', 'items', 'total_amount', 'delivery_charge', 'po_deadline')
