from datetime import datetime

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand

from mrsrequest.crudlfap import MRSRequestValidateMixin
from mrsrequest.models import MRSRequestLogEntry


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
            'action',
            help='Name of the action (contact, validated, rejected, canceled)',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Actually send the emails, instead of just out-putting them',
        )

    def handle(self, *args, **options):
        start_dt = datetime.strptime(options['start_dt'], '%Y%m%d%H%M%S')
        end_dt = datetime.strptime(options['end_dt'], '%Y%m%d%H%M%S')
        logentries = MRSRequestLogEntry.objects.filter(
            datetime__gte=start_dt,
            datetime__lte=end_dt,
        )

        logentries = logentries.select_related(
            'mrsrequest',
            'mrsrequest__insured'
        ).distinct()

        if options.get('action'):
            action = 'ACTION_' + options['action'].upper()
            logentries = logentries.filter(
                status=getattr(MRSRequestLogEntry, action)
            )

        if not options.get('confirm'):
            setattr(
                settings,
                'EMAIL_BACKEND',
                'django.core.mail.backends.console.EmailBackend'
            )

        for logentry in logentries:
            if logentry.action == MRSRequestLogEntry.ACTION_VALIDATED:
                MRSRequestValidateMixin().mail_insured(logentry.mrsrequest)
            else:
                email = EmailMessage(
                    subject=logentry.data['subject'],
                    body=logentry.data['body'],
                    to=[logentry.mrsrequest.insured.email],
                    reply_to=[settings.TEAM_EMAIL],
                    from_email=settings.DEFAULT_FROM_EMAIL,
                )
                email.send()
