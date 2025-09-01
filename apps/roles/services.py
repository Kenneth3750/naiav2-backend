from apps.researcher.services import ResearcherService
from apps.uniguide.services import UniGuideService
from apps.mental.services import MentalHealthService
from apps.personal.services import PersonalAssistantService
from apps.skills.services import SkillsTrainerService
from apps.recepcionist.services import RecepcionistService
from apps.gobernacion.services import GobernacionService, RealtimeGobernacionService


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
        elif role_id == 5:
            self.role = RecepcionistService()
            print("RoleService Receptionist")
        elif role_id == 6:
            self.role = MentalHealthService()
            print("RoleService MentalHealth")
        elif role_id == 7:
            self.role = GobernacionService()
            print("RoleService Gobernacion")
        else:
            raise Exception(f"Role {role_id} not found")

    def get_role(self, user_id, messages):
        tools, available_functions, prompts = self.role.retrieve_tools(user_id, messages)
        return tools, available_functions, prompts
    

class RealtimeRoleService:
    def __init__(self, role_id):
        if role_id == "ciudadano":
            self.role = RealtimeGobernacionService()

    def get_role(self, user_id):
        tools, prompt = self.role.get_realtime_tools(user_id)
        return tools, prompt