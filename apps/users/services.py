from .repositories import UserRepository


class UserService():
    def __init__(self):
        self.user_repository = UserRepository()

    def get_user_by_id(self, user_id):
        return self.user_repository.get_user_by_id(user_id)
    
    def create_user(self, name, family_name, email, photo_url):
        try:
            return self.user_repository.create_user(name, family_name, email, photo_url)
        except Exception as e:
            raise e
    def get_user_by_email(self, email):
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise Exception(f"User with email {email} does not exist")
        return user
        