from crudlfap import shortcuts as crudlfap

from django import test

from freezegun import freeze_time

from mrsuser.models import User
from responsediff.test import ResponseDiffTestMixin


class FrontCrawlTest(ResponseDiffTestMixin, test.TestCase):
    @freeze_time('2018-05-05 13:37:42')
    def test_crawl(self):
        self.assertWebsiteSame(selector='#app--wrapper')

    def get_content_replace_patterns(self, response):
        return super().get_content_replace_patterns(response) + [
            ('\n.*id_mrsrequest_uuid.*\n', ''),
            (
                '\n.*<(a|img|input).*(name|id|href|class)="[^"]*captcha[^"]*"[^>]*>[^\n]*',
                ''
            ),
        ]

    def skip_url(self, url):
        return '.wav' in url or super().skip_url(url)


class LiquidateurCrawlTest(ResponseDiffTestMixin, test.TestCase):
    fixtures = [
        'src/mrs/tests/data.json',
        'src/mrsstat/tests/test_mrsstat.json',
    ]
    username = 'a'
    strip_parameters = ['_next']

    @freeze_time('2018-05-05 13:37:42')
    def test_crawl(self):
        client = test.Client()
        client.force_login(User.objects.get(username=self.username))

        self.assertWebsiteSame(
            url='/admin/',
            client=client,
            selector='#modal-body-ajax',
        )

    def skip_url(self, url):
        if super().skip_url(url):
            return True
        return url.endswith('logout') or url.endswith('manifest.json')


class SuperuserCrawlTest(LiquidateurCrawlTest):
    username = 'test'

    def setUp(self):
        super().setUp()
        self.covered = []
        for u in User.objects.all()[1:]:
            self.covered += [
                crudlfap.site[User][view].clone(object=u).url
                for view in ('update', 'detail', 'password')
            ]

    def skip_url(self, url):
        if super().skip_url(url):
            return True
        if 'group' in url or 'permission' in url:
            return True
        return url.endswith('/su')


class StatCrawlTest(LiquidateurCrawlTest):
    username = 'stata'


class SupportCrawlTest(LiquidateurCrawlTest):
    username = 'supporta'
