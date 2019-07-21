from django.db.models import Avg
from django.views import generic

from mrsrequest.models import MRSRequest
from person.models import Person


class ProView(generic.TemplateView):
    template_name = 'pro/pro.html'

    @property
    def users_count(self):
        return Person.objects.count()

    @property
    def mrsrequests_count(self):
        return MRSRequest.objects.count()

    @property
    def average_payment_delay(self):
        return '{:0.2f}'.format(
            MRSRequest.objects.aggregate(
                result=Avg('delay')
            )['result'] or 0
        ).replace('.', ',')
