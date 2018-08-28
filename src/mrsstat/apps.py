from django import apps


class DefaultAppConfig(apps.AppConfig):
    name = 'mrsstat'

    def ready(self):
        try:
            import uwsgi  # noqa
        except ImportError:
            return

        from djcall.models import Caller, Cron
        caller, created = Caller.objects.get_or_create(
            callback='mrsstat.models.Stat.objects.create_missing'
        )

        Cron.objects.update_or_create(
            caller=caller,
            defaults=dict(hour=2, minute=0)
        )
