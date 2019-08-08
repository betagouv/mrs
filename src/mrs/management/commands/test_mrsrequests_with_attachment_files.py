import requests
from requests.auth import HTTPBasicAuth

from django.core.management.base import BaseCommand

from mrsrequest.models import MRSRequest


class Command(BaseCommand):
    help = 'Test if all MRSRequests are accessible and have correct ' \
           'attachment_files'
    # Example :
    # mrs test_mrsrequests_with_attachment_files -du my_username
    # -dp my_password --env staging -bal basic_auth_login -bap basic_auth_pass

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--django_username',
            '-du',
            help='Django username '
                 '-- Default "dev"'
        )
        parser.add_argument(
            '--django_password',
            '-dp',
            help='Django password '
                 '-- Default "dev"'
        )
        parser.add_argument(
            '--env',
            help='Execution environment : "dev" / "staging" / "prod" '
                 '-- Default = "dev"',
        )
        parser.add_argument(
            '--basicauthlogin',
            '-bal',
            help='Login for Basic Auth (use only with --env staging)',
        )
        parser.add_argument(
            '--basicauthpass',
            '-bap',
            help='Login for Basic Auth (use only with --env staging)',
        )

    def handle(self, *args, **options):   # noqa
        # self.stdout.write(
        #     self.style.NOTICE(options)
        # )

        env = options.get("env") or "dev"
        django_username = options.get("django_username") or "dev"
        django_password = options.get("django_password") or "dev"

        self.stdout.write(
            self.style.SUCCESS("Environment : {}".format(env.upper()))
        )

        auth = None
        if env == "dev":
            base_url = "http://localhost:8000"
        elif env == "staging":
            base_url = "https://staging.mrs.beta.gouv.fr"
            basicauthlogin = options.get("basicauthlogin") or None
            basicauthpass = options.get("basicauthpass") or None
            if basicauthlogin and basicauthpass:
                auth = HTTPBasicAuth(basicauthlogin, basicauthpass)
        elif env == "prod":
            base_url = "https://mrs.beta.gouv.fr"

        sess = requests.Session()

        r_csrf = sess.get(
            "{}/admin/login".format(base_url),
            auth=auth
        )
        if r_csrf.status_code != 200:
            self.stdout.write(
                self.style.ERROR("CSRF request failed : {}".format(
                    r_csrf.status_code
                ))
            )
            return
        else:
            self.stdout.write(
                self.style.SUCCESS("CSRF request OK")
            )

        csrftoken = r_csrf.cookies["csrftoken"]

        r_login = sess.post(
            "{}/admin/login".format(base_url),
            data={
                "username": django_username,
                "password": django_password,
                "csrfmiddlewaretoken": csrftoken,
            },
            auth=auth
        )

        if r_login.status_code != 200:
            self.stdout.write(
                self.style.ERROR("Login request failed : {}".format(
                    r_login.status_code
                ))
            )
            return
        else:
            self.stdout.write(
                self.style.SUCCESS("Login request OK")
            )

        reqs = MRSRequest.objects.all().order_by("-creation_datetime")

        count = 0
        for req in reqs:
            self.stdout.write(
                self.style.SUCCESS(
                    f'{count} - {req.creation_datetime}'
                )
            )
            count += 1
            req_id = req.id
            r_test = sess.get(
                "{}/admin/mrsrequest/{}".format(base_url, req_id),
                auth=auth
            )

            if r_test.status_code == 500:
                if "FileNotFoundError" in r_test.text:
                    self.stdout.write(
                        self.style.ERROR(
                            "MRSRequest {} test failed : "
                            "File not found".format(req_id))
                    )
                elif "attribute has no file associated with it" in r_test.text:
                    self.stdout.write(
                        self.style.ERROR(
                            "MRSRequest {} test failed : "
                            "Attachment_file empty".format(req_id))
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            "MRSRequest {} test failed : "
                            "Other".format(req_id))
                    )
            elif r_test.status_code == 200:
                if "Personne transport" in r_test.text:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "MRSRequest {} test OK".format(req_id)
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            "MRSRequest {} test failed, "
                            "logged out ?".format(req_id))
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "MRSRequest {} test failed : "
                        "status_code = {}".format(req_id, r_test.status_code))
                )
