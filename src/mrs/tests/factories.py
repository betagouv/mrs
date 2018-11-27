import factory

from pytest_factoryboy import register


@register
class CaisseFactory(factory.django.DjangoModelFactory):
    code = 312312312
    number = 123
    active = True

    class Meta:
        model = 'caisse.caisse'


@register
class TransportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'mrsrequest.transport'


@register
class MRSRequestFactory(factory.django.DjangoModelFactory):
    transport_set = factory.RelatedFactory(
        TransportFactory,
        'mrsrequest',
    )
    modevp = True
    caisse = factory.SubFactory(CaisseFactory)

    class Meta:
        model = 'mrsrequest.mrsrequest'
