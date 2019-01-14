from mrsrequest.models import MRSRequest


class AuthenticationBackend:
    def authenticate(self, *args):
        """
        Always return ``None`` to prevent authentication within this backend.
        """
        return None

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_authenticated:
            return False

        if not perm.startswith('mrsrequest.mrsrequest_detail'):
            return False

        if not isinstance(obj, MRSRequest):
            return

        return (
            user_obj.profile == 'admin'
            or obj.caisse in user_obj.caisses.all()
        )
