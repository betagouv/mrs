from django.db.models import Avg
from django.views import generic

from mrsrequest.models import MRSRequest
from person.models import Person


class ProView(generic.TemplateView):
    template_name = 'pro/pro.html'

    users_count = Person.objects.count()
    mrsrequests_count = MRSRequest.objects.count()
    average_payment_delay = '{:0.2f}'.format(
        MRSRequest.objects.aggregate(
            result=Avg('delay')
        )['result'] or 0
    ).replace('.', ',')

