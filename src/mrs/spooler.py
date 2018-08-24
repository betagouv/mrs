import json
import pickle

from django.conf import settings
from django.core.mail import EmailMessage

try:
    import uwsgi
except ImportError:
    uwsgi = None


def make_liquidation_email(title, body, mrsrequest):
    return EmailMessage(
        title,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [mrsrequest.caisse.liquidation_email],
        reply_to=[settings.TEAM_EMAIL],
        attachments=[mrsrequest.pmt.tuple()] + [
            bill.tuple() for bill in mrsrequest.bill_set.all()
        ]
    )


def liquidation_email_send(title, body, mrsrequest):
    if uwsgi:
        uwsgi.spool({
            b'task': b'liquidation_email_send',
            b'body': pickle.dumps([
                title,
                body,
                mrsrequest.pk,
            ]),
            b'spooler': b'/spooler/mail',
        })
    else:
        email = make_liquidation_email(title, body, mrsrequest)
        email.send()


def email_send(email):
    if uwsgi:
        uwsgi.spool({
            b'task': b'email_send',
            b'body': pickle.dumps(email),
            b'spooler': b'/spooler/mail',
        })
    else:
        email.send()


def spooler(env):
    from mrsrequest.models import MRSRequest
    if env.get(b'task') == b'update_stats':
        from mrsstat.models import Stat
        Stat.objects.update_stats(
            MRSRequest.objects.filter(
                pk__in=json.loads(env['body'].decode('ascii')),
            )
        )
    elif env.get(b'task') == b'email_send':
        email = pickle.loads(env['body'])
        email.send()
    elif env.get(b'task') == b'liquidation_email_send':
        title, body, mrsrequest_pk = pickle.loads(env['body'])
        mrsrequest = MRSRequest.objects.get(pk=mrsrequest_pk)
        email = make_liquidation_email(title, body, mrsrequest)
        email.send()
    return uwsgi.SPOOL_OK
