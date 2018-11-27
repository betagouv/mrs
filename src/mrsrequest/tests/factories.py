import factory

from pytest_factoryboy import register


@registery
class TransportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'mrsrequest.transport'


@register
class MRSRequestFactory(factory.django.DjangoModelFactory):
    transport_set = factory.RelatedFactory(TransportFactory, 'user', action=models.UserLog.ACTION_CREATE)

    class Meta:
        model = 'mrsrequest.mrsrequest'
