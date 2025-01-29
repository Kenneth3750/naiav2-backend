from .models import User


class UserRepository:
    def get_user_by_id(self, user_id):
        return User.objects.get(id=user_id)