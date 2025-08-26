from .repositories import UserRepository


class UserService():
    def __init__(self):
        from user_list import user_list
        self.user_repository = UserRepository()
        self.user_list = user_list

    def get_user_by_id(self, user_id):
        return self.user_repository.get_user_by_id(user_id)
    
    def create_user(self, name, family_name, email, photo_url):
        try:
            return self.user_repository.create_user(name, family_name, email, photo_url)
        except Exception as e:
            raise e
    def get_user_by_email(self, email):
        return self.user_repository.get_user_by_email(email)
    
    def create_or_update_user_token(self, user_id, token):
        try:
            self.user_repository.create_or_update_user_token(user_id, token)
        except Exception as e:
            raise e
    def get_user_token(self, user_id):
        try:
            return self.user_repository.get_user_token(user_id)
        except Exception as e:
            raise e
        
    def has_user_permission(self, email):
        print(f"Checking permission for email: '{email}'")
        print(f"Email in list: {email in self.user_list}")
        print(f"User list length: {len(self.user_list)}")
        return True if email in self.user_list else False
        