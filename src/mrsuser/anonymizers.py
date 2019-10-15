from hattori.base import BaseAnonymizer, faker
from mrsuser.models import User


class MRSUserAnonymizer(BaseAnonymizer):
    model = User

    attributes = [
        ('email', faker.email),
        ('first_name', faker.first_name),
        ('last_name', faker.last_name),
    ]

    def get_query_set(self):
        return User.objects.all()
