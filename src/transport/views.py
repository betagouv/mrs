from material.frontend.views import ModelViewSet

from .models import Bill, Transport


class TransportViewSet(ModelViewSet):
    model = Transport


class BillViewSet(ModelViewSet):
    model = Bill
