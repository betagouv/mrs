from datetime import datetime

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand

from contact.models import Contact
from contact.forms import ContactForm


class Command(BaseCommand):
    help = 'Send emails based on log entries, to recover when email was down'

    def add_arguments(self, parser):
        parser.add_argument(
            'start_dt',
            help='Start datetime, YYYYMMDDHHMM',
        )
        parser.add_argument(
            'end_dt',
            help='Start datetime, YYYYMMDDHHMM',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Actually send the emails, instead of just out-putting them',
        )

    def handle(self, *args, **options):
        start_dt = datetime.strptime(options['start_dt'], '%Y%m%d%H%M%S')
        end_dt = datetime.strptime(options['end_dt'], '%Y%m%d%H%M%S')
        contacts = Contact.objects.filter(
            creation_datetime__gte=start_dt,
            creation_datetime__lte=end_dt,
        ).select_related('mrsrequest', 'mrsrequest__insured')

        if not options.get('confirm'):
            setattr(
                settings,
                'EMAIL_BACKEND',
                'django.core.mail.backends.console.EmailBackend'
            )

        for contact in contacts:
            mrsrequest = getattr(
                contact,
                'mrsrequest',
                None,
            )

            form = ContactForm(dict(
                motif=contact.subject,
                nom=contact.name,
                email=contact.email,
                message=contact.message,
                caisse=getattr(contact.caisse, 'id', None),
                mrsrequest_display_id=getattr(mrsrequest, 'display_id', None),
            ))
            form.full_clean()
            email = EmailMessage(**form.get_email_kwargs())
            email.send()
