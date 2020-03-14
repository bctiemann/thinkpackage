from django.apps import AppConfig
from django.db.models.signals import post_save


class ImsConfig(AppConfig):
    name = 'ims'

    def ready(self):
        Client = self.get_model('Client')
        post_save.connect(self.populate_client_ancestors, sender=Client)

    def populate_client_ancestors(self, sender, **kwargs):
        client = kwargs.get('instance')
        if not client.ancestors:
            client.ancestors = [client.id]
            client.save()
