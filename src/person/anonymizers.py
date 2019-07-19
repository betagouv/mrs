from hattori.base import BaseAnonymizer, faker
from person.models import Person

class PersonAnonymizer(BaseAnonymizer):
    model = Person

    attributes = [
        ('first_name', faker.first_name),
        ('last_name', faker.last_name),
        ('birth_date', lambda **kwargs: faker.date_of_birth(tzinfo=None, minimum_age=18, maximum_age=99, **kwargs)),
        ('email', faker.email),
        ('nir', lambda **kwargs: faker.password(length=13, special_chars=False, digits=True, upper_case=True, lower_case=False, **kwargs)),
    ]

    def get_query_set(self):
        return Person.objects.all()
