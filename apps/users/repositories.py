from .models import User


class UserRepository:
    def get_user_by_id(self, user_id):
        return User.objects.get(id=user_id)
    def create_user(self, name, family_name, email, photo_url):
        return User.objects.create(name=name, family_name=family_name, email=email, photo_url=photo_url)