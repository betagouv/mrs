from django import apps


class DefaultAppConfig(apps.AppConfig):
    name = 'caisse'

    def ready(self):
        try:
            import uwsgi  # noqa
        except ImportError:
            return

        from djcall.models import Caller, Cron
        caller, created = Caller.objects.get_or_create(
            callback='caisse.models.daily_mail'
        )

        Cron.objects.update_or_create(
            caller=caller,
            defaults=dict(
                hour=8,
                minute=0,
                weekday='1-5',
            )
        )

        caller, created = Caller.objects.get_or_create(
            callback='caisse.models.monthly_mail'
        )

        Cron.objects.update_or_create(
            caller=caller,
            defaults=dict(
                hour=11,
                minute=30,
                day=11,
            )
        )
