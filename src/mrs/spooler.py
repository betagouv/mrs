import json
import uwsgi


def spooler(env):
    if env.get(b'task') == b'update_stats':
        from mrsstat.models import Stat
        from mrsrequest.models import MRSRequest
        Stat.objects.update_stats(
            MRSRequest.objects.filter(
                pk__in=json.loads(env['body'].decode('ascii')),
            )
        )
    return uwsgi.SPOOL_OK
