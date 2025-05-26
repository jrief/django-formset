from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.utils.deprecation import MiddlewareMixin


class AutoLoginMiddleware(MiddlewareMixin):
    """
    Middleware to automatically login as admin user.
    """

    def process_request(self, request):
        try:
            request.user = get_user_model().objects.get(username='admin')
        except get_user_model().DoesNotExist:
            try:
                request.user = get_user_model().objects.create_user(
                    username='admin',
                    password='secret',
                    is_superuser=True,
                    is_staff=True,
                )
            except IntegrityError:
                # prevent race condition during end-to-end tests
                request.user = get_user_model().objects.get(username='admin')
