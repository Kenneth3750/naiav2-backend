from apps.researcher.services import ResearcherService


class RoleService:
    def __init__(self, role_id):
        if role_id == 1:
            self.role = ResearcherService()
            print("RoleService Researcher")
        else:
            raise Exception(f"Role {role_id} not found")

    def get_role(self):
        tools, available_functions, system_prompt = self.role.retrieve_tools()
        return tools, available_functions, system_prompt