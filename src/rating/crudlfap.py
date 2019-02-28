from crudlfap import shortcuts as crudlfap

from .models import Rating


class RatingRouter(crudlfap.Router):
    model = Rating
    allowed_groups = ['Admin']
    material_icon = 'star'
    views = [
        crudlfap.DetailView,
        crudlfap.ListView,
    ]

RatingRouter().register()
