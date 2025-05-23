from apps.researcher.services import ResearcherService
from apps.uniguide.services import UniGuideService


class RoleService:
    def __init__(self, role_id):
        if role_id == 1:
            self.role = ResearcherService()
            print("RoleService Researcher")
        elif role_id == 2:
            self.role = UniGuideService()
            print("RoleService UniGuide")
        else:
            raise Exception(f"Role {role_id} not found")

    def get_role(self, user_id):
        tools, available_functions, prompts = self.role.retrieve_tools(user_id)
        return tools, available_functions, prompts