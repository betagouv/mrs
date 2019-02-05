import csv
from chardet.universaldetector import UniversalDetector
from crudlfap import shortcuts as crudlfap

from django import forms
from django.contrib.auth.models import Group
from django.db.models import Case, Count, When, IntegerField

import django_tables2 as tables

from caisse.models import Caisse
from mrsrequest.models import MRSRequestLogEntry

from .models import User


class UserForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        Group.objects.all(),
        required=False,
    )
    caisses = forms.ModelMultipleChoiceField(
        Caisse.objects.filter(active=True),
        required=False,
    )
    new_password = forms.CharField(
        label='Mot de passe',
        required=False,
        help_text='Laisser ce champs vide pour ne pas changer le mot de passe'
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'groups',
            'caisses',
            'is_superuser',
            'is_active',
        ]

    def clean(self):
        data = super().clean()
        groups = data.get('groups', [])
        caisses = self.cleaned_data.get('caisses', [])
        su = data.get('is_superuser', False)

        if not su and not groups:
            self.add_error('groups', 'Ce champ est obligatoire.')

        admin = False
        for group in groups:
            if group.name == 'Admin':
                admin = True

        if not (admin or su) and not caisses:
            self.add_error('caisses', 'Ce champ est obligatoire.')
        return data

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password', '')
        if not (self.instance.password or new_password):
            raise forms.ValidationError('Ce champ est obligatoire.')
        return new_password

    def save(self, commit=True):
        if self.cleaned_data.get('new_password', ''):
            self.instance.set_password(self.cleaned_data['new_password'])
        return super().save(commit=commit)


crudlfap.site[User]['update'].form_class = UserForm
crudlfap.site[User]['update'].fields.append('is_active')
crudlfap.site[User]['create'].form_class = UserForm
crudlfap.site[User]['list'].filter_fields = [
    'groups',
    'caisses',
]

crudlfap.site[User]['list'].table_fields = [
    'caisses',
    'is_active',
    'email',
    'first_name',
    'last_name',
    'groups',
]

crudlfap.site[User]['list'].table_columns = dict(
    modifications=tables.Column(
        accessor='count_updates',
        verbose_name='Modifications',
    )
)


def get_queryset(self):
    return super(type(self), self).get_queryset().annotate(
        count_updates=Count(Case(
            When(
                mrsrequestlogentry__action=MRSRequestLogEntry.ACTION_UPDATE,
                then=1
            ),
            output_field=IntegerField(),
        ))
    )


crudlfap.site[User].views['list'].get_queryset = get_queryset


CSV_COLUMNS = (
    'nom',
    'prenom',
    'numero agent',
    'profil',
    'numero organisme',
    'mail',
)


class ImportView(crudlfap.FormView):
    allowed_groups = ['Admin']
    menus = ['main', 'model']
    material_icon = 'cloud_upload'
    turbolinks = False
    form_invalid_message = 'Erreurs durant l\'import'
    form_valid_message = 'Importé avec succès'
    body_class = 'full-width'
    template_name = 'mrsuser/user_import.html'

    class form_class(forms.Form):
        csv = forms.FileField()

    def preflight(self):
        self.first_line_found = None
        self.missing_columns = dict()

        detector = UniversalDetector()
        for i, line in enumerate(self.request.FILES['csv'].readlines()):
            if self.first_line_found is None:
                self.first_line_found = line.strip()
            if len(line.strip().split(b';')) != len(CSV_COLUMNS):
                self.missing_columns[i + 1] = line
            detector.feed(line)
            if detector.done:
                break
        detector.close()
        self.encoding = detector.result['encoding']

        self.errors = dict()
        self.success = dict()

        for number, line in self.missing_columns.items():
            self.missing_columns[number] = line.decode(self.encoding)

        self.first_line_found = self.first_line_found.decode(self.encoding)
        self.first_line_expected = ';'.join(CSV_COLUMNS)

    def form_valid(self):
        self.preflight()

        if self.first_line_found != self.first_line_expected:
            return self.render_to_response()

        def decode_utf8(input_iterator):
            for l in input_iterator:
                yield l.decode(self.encoding).strip()

        reader = csv.DictReader(
            decode_utf8(self.request.FILES['csv']),
            delimiter=';'
        )

        self.errors = dict()
        self.success = dict()
        for i, row in enumerate(reader):
            if i + 2 in self.missing_columns.keys():
                continue

            obj = '?'
            try:
                obj = self.add_user(row)
            except Exception as e:
                self.errors[i + 1] = dict(
                    row=row,
                    object=obj,
                    message=repr(e),
                )
            else:
                self.success[i + 1] = dict(object=obj, row=row)

        return self.render_to_response()

    def add_user(self, row):
        agent_nb = row['numero agent'].strip()
        last_name = row['nom'].strip().upper()
        username = "{}_{}".format(last_name, agent_nb)

        user, created = User.objects.get_or_create(
            last_name=last_name,
            first_name=row['prenom'].strip(),
            email=row['mail'].strip(),
            username=username,
        )

        if not user.password:
            user.password_reset()

        groups = row['profil'].split(',')
        user.add_groups(groups)

        caisses_ids = row['numero organisme'].split(',')
        caisses = []
        for id in caisses_ids:
            caisses.append(Caisse.objects.get(number=id))

        if caisses:
            user.caisses.add(*caisses)

        return user


class PasswordResetView(crudlfap.ObjectFormView):
    material_icon = 'vpn_key'
    color = 'orange'
    title = 'Envoyer un nouveau mot de passe'
    controller = 'modal'
    action = 'click->modal#open'
    template_name = 'mrsuser/user_password_reset.html'

    class form_class(forms.Form):
        pass

    def form_valid(self):
        resp = super().form_valid()
        self.object.password_reset()
        return resp
        return self.render_to_response()


del crudlfap.site[User].views['delete']
del crudlfap.site[User].views['deleteobjects']

# todo add lublic api to patch router
ImportView.router = crudlfap.site[User]
ImportView.model = User
crudlfap.site[User].views.insert(0, ImportView)

PasswordResetView.model = User
PasswordResetView.router = crudlfap.site[User]
crudlfap.site[User].views.insert(0, PasswordResetView)

crudlfap.site[User].allowed_groups = ['Admin']
crudlfap.site[Group].allowed_groups = ['Admin']
