from django.views import generic


class StatisticsView(generic.TemplateView):
    template_name = 'mrspage/statistics.html'
