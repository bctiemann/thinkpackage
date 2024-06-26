# Generated by Django 3.0.3 on 2020-03-28 23:35

from django.db import migrations


def convert_ids(apps, _):

    shipment_doc_model: ShipmentDoc = apps.get_model("ims", "ShipmentDoc")

    for shipment_doc in shipment_doc_model.objects.all():
        shipment_doc.save()


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0077_auto_20200328_2323'),
    ]

    operations = [
        migrations.RunPython(convert_ids, reverse_code=migrations.RunPython.noop),
        migrations.RenameField(
            model_name='shipmentdoc',
            old_name='uuid',
            new_name='id',
        ),
    ]
