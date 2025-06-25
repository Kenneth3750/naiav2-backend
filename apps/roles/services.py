from apps.researcher.services import ResearcherService
from apps.uniguide.services import UniGuideService
from apps.mental.services import MentalHealthService
from apps.personal.services import PersonalAssistantService
from apps.skills.services import SkillsTrainerService


class RoleService:
    def __init__(self, role_id):
        if role_id == 1:
            self.role = ResearcherService()
            print("RoleService Researcher")
        elif role_id == 2:
            self.role = UniGuideService()
            print("RoleService UniGuide")
        elif role_id == 3:
            self.role = PersonalAssistantService()
            print("RoleService PersonalAssistant")
        elif role_id == 4:
            self.role = SkillsTrainerService()
            print("RoleService SkillsTrainer")
        elif role_id == 6:
            self.role = MentalHealthService()
            print("RoleService MentalHealth")
        else:
            raise Exception(f"Role {role_id} not found")

    def get_role(self, user_id, messages):
        tools, available_functions, prompts = self.role.retrieve_tools(user_id, messages)
        return tools, available_functions, prompts