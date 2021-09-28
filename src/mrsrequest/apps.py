from django import apps


class MRSRequestAppConfig(apps.AppConfig):
    name = 'mrsrequest'
    verbose_name = 'Demandes'

    def ready(self):
        try:
            import uwsgi  # noqa
        except ImportError:
            return

        from djcall.models import Caller, Cron
        caller, created = Caller.objects.get_or_create(
            callback='mrsrequests.'
                     'models.anonymize_mrsrequests_older_than_33_months'
        )

        Cron.objects.update_or_create(
            caller=caller,
            defaults=dict(
                hour=6,
                minute=6,
            )
        )

        caller, created = Caller.objects.get_or_create(
            callback='mrsrequests.models.remove_attachments_without_mrsrequest'
        )

        Cron.objects.update_or_create(
            caller=caller,
            defaults=dict(
                hour=6,
                minute=46,
            )
        )
