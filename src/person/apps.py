from django import apps


class PersonAppConfig(apps.AppConfig):
    name = 'person'
    verbose_name = 'Personnes'

    def ready(self):
        try:
            import uwsgi  # noqa
        except ImportError:
            return

        from djcall.models import Caller, Cron
        caller, created = Caller.objects.get_or_create(
            callback='person.models.delete_orphan_persons'
        )

        Cron.objects.update_or_create(
            caller=caller,
            defaults=dict(
                hour=6,
                minute=26,
            )
        )
