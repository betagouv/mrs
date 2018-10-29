import json

from crudlfap import shortcuts as crudlfap
from django import template
from django.conf import settings

from djcall.models import Caller

from .forms import EmailForm
from .models import EmailTemplate


class EmailViewMixin:
    template_name = 'mrsemail/form.html'
    body_class = 'modal-fixed-footer'
    form_class = EmailForm

    def log_insert(self):
        if hasattr(self, 'object_list'):
            objects = self.object_list
        else:
            objects = [self.object]

        for obj in objects:
            obj.logentries.create(
                user=self.request.user,
                comment=self.log_message,
                data=self.log_data,
                action=self.action_flag,
            )

    def get_log_data(self):
        return dict(
            body=self.form.cleaned_data['body'],
            subject=self.form.cleaned_data['subject'],
        )

    def get_log_message(self):
        return self.form.cleaned_data['template']

    def get_form(self):
        form = super().get_form() or self.form
        qs = form.fields['template'].queryset
        form.fields['template'].queryset = qs.filter(
            menu=self.emailtemplates_menu
        )
        return form

    def templates_json(self):
        context = template.Context({'display_id': self.object.display_id})
        templates = {
            i.pk: dict(
                subject=template.Template(i.subject).render(context),
                body=template.Template(i.body).render(context),
            ) for i in EmailTemplate.objects.filter(
                menu=self.emailtemplates_menu
            )
        }
        return json.dumps(templates)

    def form_valid(self):
        Caller(
            callback='djcall.django.email_send',
            kwargs=dict(
                subject=self.form.cleaned_data['subject'],
                body=self.form.cleaned_data['body'],
                to=[self.object.insured.email],
                reply_to=[settings.TEAM_EMAIL],
            )
        ).spool('mail')
        self.form.cleaned_data['template'].counter += 1
        self.form.cleaned_data['template'].save()
        return super().form_valid()


class EmailTemplateListView(crudlfap.ListView):
    table_sequence = (
        'name',
        'subject',
        'counter',
        'active',
    )


crudlfap.Router(
    EmailTemplate,
    allowed_groups=['Admin'],
    material_icon='mail',
    views=[
        EmailTemplateListView,
        crudlfap.CreateView,
        crudlfap.UpdateView,
    ]
).register()
