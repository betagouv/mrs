from crudlfap import shortcuts as crudlfap

from .models import Rating


class RatingRouter(crudlfap.Router):
    model = Rating
    allowed_groups = ['Admin', 'Superviseur']
    material_icon = 'star'
    views = [
        crudlfap.DetailView,
        crudlfap.ListView,
    ]

    def get_queryset(self, view):
        user = view.request.user

        if user.is_superuser or user.profile == 'admin':
            return self.model.objects.all()
        elif user.profile == 'superviseur':
            return self.model.objects.filter(
                mrsrequest__caisse__in=view.request.user.caisses.all()
            )

        return self.model.objects.none()

RatingRouter().register()
