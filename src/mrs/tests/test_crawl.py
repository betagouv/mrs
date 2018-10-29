from crudlfap import shortcuts as crudlfap

from django import test

from freezegun import freeze_time

from mrsrequest.models import MRSRequest
from mrsuser.models import User
from responsediff.test import ResponseDiffTestMixin


class FrontCrawlTest(ResponseDiffTestMixin, test.TestCase):
    @freeze_time('2018-05-30 13:37:42')  # forward compat and bichon <3
    def test_crawl(self):
        self.assertWebsiteSame(selector='#app--wrapper')

    def get_content_replace_patterns(self, response):
        return super().get_content_replace_patterns(response) + [
            ('\n.*id_mrsrequest_uuid.*\n', ''),
        ]


class LiquidateurCrawlTest(ResponseDiffTestMixin, test.TestCase):
    fixtures = ['src/mrs/tests/data.json']
    username = 'a'
    strip_parameters = ['_next']

    def setUp(self):
        from mrsstat.models import update_stat_for_mrsrequest
        for m in MRSRequest.objects.all():
            update_stat_for_mrsrequest(pk=m.pk)
        super().setUp()

    @freeze_time('2018-05-30 13:37:42')  # forward compat and bichon <3
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
