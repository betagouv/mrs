import csv
from chardet.universaldetector import UniversalDetector
from crudlfap import shortcuts as crudlfap
from crudlfap_auth.views import (BecomeUser,
                                 PasswordView as CrudlfapPasswordView)

from django import forms
from django.contrib.auth.models import Group
from django.db.models import Case, Count, When, IntegerField
from django.utils.text import slugify
from django.core.validators import validate_email

import django_tables2 as tables

from caisse.models import Caisse
from mrsrequest.models import MRSRequestLogEntry

from django.contrib.auth.forms import SetPasswordForm

from django.db import transaction

from .models import User


def clean_user_input(input_to_clean):
    return slugify(
        input_to_clean.strip().replace('/', '')
    ).replace('-', '_').upper()


class PasswordForm(SetPasswordForm):

    def __init__(self, *args, **kwargs):
        disabled = kwargs.pop('disabled', None)
        super().__init__(*args, **kwargs)
        if disabled:
            for field in self.fields:
                self.fields[field].disabled = True


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
            'number',
            'first_name',
            'last_name',
            'username',
            'email',
            'groups',
            'caisses',
            'is_superuser',
            'is_active',
        ]

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

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


class AdminUserForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        Group.objects.filter(
            name__in=['UPN', 'Support', 'Stat', 'Superviseur', 'Admin Local']
        ),
        label='Groupes',
    )
    caisses = forms.ModelMultipleChoiceField(
        Caisse.objects.filter(active=True),
    )

    class Meta:
        model = User
        fields = [
            'number',
            'first_name',
            'last_name',
            'username',
            'email',
            'caisses',
            'groups',
            'is_active',
        ]

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        self.fields['caisses'].queryset = request.user.caisses.all()
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.old_username = self.instance.username
        self.old_email = self.instance.email
        self.old_number = self.instance.number

        # Store caisses managed by the current local admin
        self.admin_caisses = request.user.caisses.values_list(
            'id', flat=True)

        # If it's an update form, we store original caisses
        if self.instance.pk:

            self.old_caisses = list(self.instance.caisses.values_list(
                'id', flat=True))

            # We remove local admin caisses, since they will be updated without
            # pain of getting lost
            for caisse in self.old_caisses:
                if caisse in self.admin_caisses:
                    self.old_caisses.remove(caisse)

            for field in self.fields:

                # Case when the admin manages no caisses of the edited user
                # We disable all fields except caisses
                if len(list(set(self.fields['caisses'].queryset)
                       & set(self.instance.caisses.all()))) == 0:
                    self.fields[field].disabled = True

                self.fields['caisses'].disabled = False

            # We allow caisses to be emptied, since a local admin can unselect
            # its lonely caisse for the selected user
            self.fields['caisses'].required = False

        else:
            self.old_caisses = []

    def clean_groups(self):
        groups = self.cleaned_data.get('groups')
        if not groups:
            raise forms.ValidationError(
                'Merci de choisir au moins un groupe'
            )
        return groups

    def clean_caisses(self):
        caisses = self.cleaned_data.get('caisses')
        if not caisses and not self.instance.pk:
            raise forms.ValidationError(
                'Merci de choisir au moins une caisse'
            )
        return caisses

    def save(self, commit=True):

        username = []
        for field in ('last_name', 'number'):
            username.append(
                clean_user_input(self.cleaned_data[field])
            )
        new_username = '_'.join(username)
        reset_password = (
            new_username != self.old_username
            or self.cleaned_data['email'] != self.old_email
        )
        self.instance.username = new_username

        # Retrieve updates from local admin caisses
        new_caisses = list(self.cleaned_data.get('caisses').values_list(
            'id', flat=True))

        # Create final caisse list from saved caisses and local admin caisses
        for caisse_id in (self.old_caisses + new_caisses):
            new_caisses.append(Caisse.objects.get(pk=caisse_id))

        super().save(commit=commit)
        # After the transaction commit we update the caisses_set with our
        # new_caisses list
        transaction.on_commit(lambda: self.instance.caisses.set(new_caisses))

        if reset_password:
            self.instance.password_reset(self.request.user.caisses.first())

        return self.instance


class UserFormMixin:
    def get_form_class(self):
        if self.request.user.profile == 'admin':
            return UserForm
        else:
            return AdminUserForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class UserUpdateView(UserFormMixin, crudlfap.UpdateView):
    allowed_groups = ['Admin', 'Admin Local']


class UserCreateView(UserFormMixin, crudlfap.CreateView):
    allowed_groups = ['Admin', 'Admin Local']


class UserListView(crudlfap.ListView):
    search_fields = [
        'username',
        'email',
        'first_name',
        'last_name'
    ]

    table_fields = [
        'caisses',
        'is_active',
        'email',
        'first_name',
        'last_name',
        'groups',
    ]

    filter_fields = [
        'groups',
        'caisses',
    ]

    table_columns = dict(
        modifications=tables.Column(
            accessor='count_updates',
            verbose_name='Modifications',
        )
    )

    def get_queryset(self):
        update = MRSRequestLogEntry.ACTION_UPDATE
        return super().get_queryset().annotate(
            count_updates=Count(Case(
                When(
                    mrsrequestlogentry__action=update,
                    then=1
                ),
                output_field=IntegerField(),
            ))
        )

    def get_filterset(self):
        filterset = super().get_filterset() or self.filterset
        form = filterset.form
        if self.request.user.profile != 'admin':

            if self.request.user.profile != 'admin local':
                form.fields['caisses'].queryset = (
                    self.request.user.caisses.all()
                )

            form.fields['groups'].queryset = Group.objects.exclude(
                name='Admin',
            )
        return filterset


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
            for inp in input_iterator:
                yield inp.decode(self.encoding).strip()

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
                validate_email(row["mail"])
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

        agent_nb = clean_user_input(row['numero agent'])
        last_name = clean_user_input(row['nom'])
        username = "{}_{}".format(last_name, agent_nb)

        user, created = User.objects.get_or_create(
            last_name=last_name,
            first_name=row['prenom'].strip(),
            email=row['mail'].strip(),
            username=username,
        )

        if not user.password:
            user.password_reset(self.request.user.caisses.first())

        groups = row['profil'].split(',')
        user.add_groups(groups)

        user.number = agent_nb

        caisses_ids = row['numero organisme'].split(',')
        caisses = []
        for id in caisses_ids:
            caisses.append(Caisse.objects.get(number=id.strip()))

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
        # Case when the admin manages at least one caisse of the edited user
        if len(list(set(self.request.user.caisses.all())
               & set(self.object.caisses.all()))) > 0:

            # We actually reset password for the edited user
            self.object.password_reset(self.request.user.caisses.first())
        return resp


class PasswordView(CrudlfapPasswordView):

    def get_form_class(self):

        cls = PasswordForm
        # This fixes the form messages feature from UpdateView
        return type(cls.__name__, (cls,), dict(instance=self.object))

    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.object

        kwargs['disabled'] = False

        # Case when the admin manages no caisses of the edited user
        if(len(list(set(self.request.user.caisses.all())
           & set(self.object.caisses.all()))) == 0):

            # We disable every field of the SetPasswordForm
            kwargs['disabled'] = True

        return kwargs


class UserRouter(crudlfap.Router):
    views = [
        ImportView,
        PasswordResetView.clone(
            allowed_groups=['Admin', 'Admin Local']
        ),
        PasswordView.clone(
            allowed_groups=['Admin', 'Admin Local']
        ),
        UserUpdateView,
        UserCreateView,
        BecomeUser.clone(
            allowed_groups=['Admin'],
        ),
        crudlfap.DetailView.clone(
            exclude=[
                'password',
                'permissions',
            ]
        ),
        UserListView,
    ]
    allowed_groups = ['Admin', 'Superviseur', 'Admin Local']
    material_icon = 'person'
    model = User
    urlfield = 'pk'

    def get_queryset(self, view):
        user = view.request.user

        if user.profile == 'admin':
            return self.model.objects.all()
        elif user.profile == 'superviseur':
            return self.model.objects.filter(
                caisses__in=view.request.user.caisses.all()
            ).exclude(
                groups__name__in=('Superviseur', 'Admin')
            ).distinct()
        elif user.profile == 'admin local':
            return self.model.objects.exclude(
                groups__name='Admin'
            ).distinct()

        return self.model.objects.none()


UserRouter().register()


crudlfap.site[Group].allowed_groups = ['Admin']
