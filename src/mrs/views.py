from django.views import generic


class LegalView(generic.TemplateView):
    template_name = 'legal.html'


class FaqView(generic.TemplateView):
    template_name = 'faq.html'


class StatisticsView(generic.TemplateView):
    template_name = 'statistics.html'
