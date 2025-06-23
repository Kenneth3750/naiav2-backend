from .models import User
from django.db.utils import IntegrityError

class UserRepository:
    def get_user_by_id(self, user_id):
        return User.objects.get(id=user_id)
    def get_user_by_email(self, email):
        return User.objects.get(email=email)
    def create_user(self, name, family_name, email, photo_url):
        try:
            return User.objects.create(name=name, family_name=family_name, email=email, photo_url=photo_url)
        except IntegrityError:
            raise Exception(f"User with email {email} already exists")
    
    def get_user_by_email(self, email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
