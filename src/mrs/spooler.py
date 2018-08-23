import json
import pickle

try:
    import uwsgi
except ImportError:
    uwsgi = None


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
    if env.get(b'task') == b'update_stats':
        from mrsstat.models import Stat
        from mrsrequest.models import MRSRequest
        Stat.objects.update_stats(
            MRSRequest.objects.filter(
                pk__in=json.loads(env['body'].decode('ascii')),
            )
        )
    elif env.get(b'task') == b'email_send':
        email = pickle.loads(env['body'])
        email.send()
    return uwsgi.SPOOL_OK
