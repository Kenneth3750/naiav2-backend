from apps.researcher.services import ResearcherService, RealtimeResearchService
from apps.uniguide.services import UniGuideService, RealtimeUniGuideService
from apps.mental.services import MentalHealthService, RealtimeBienestarService
from apps.personal.services import PersonalAssistantService, RealtimePersonalAssistantService
from apps.skills.services import SkillsTrainerService, RealtimeSkillsTrainerService
from apps.recepcionist.services import RecepcionistService, RealtimeReceptionistService
from apps.gobernacion.services import GobernacionService, RealtimeGobernacionService
from apps.mompox.services import RealtimeMompoxService
from .funcs import ToeflRealtime

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
        self.role_id = role_id
        if role_id == "ciudadano" or role_id == 7:
            self.role = RealtimeGobernacionService()
        elif role_id == 1:
            self.role = RealtimeResearchService()
        elif role_id == 2:
            self.role = RealtimeUniGuideService()
        elif role_id == 3:
            self.role = RealtimePersonalAssistantService()
        elif role_id == 4:
            self.role = RealtimeSkillsTrainerService()
        elif role_id == 5:
            self.role = RealtimeReceptionistService()
        elif role_id == 6 or role_id == "biela":
            self.role = RealtimeBienestarService()
        elif role_id == "mompox" or role_id == 8:
            self.role = RealtimeMompoxService()

        elif role_id == 123:
            self.role = ToeflRealtime()
        

        else:
            raise Exception(f"Realtime Role {role_id} not found")

    def get_role(self, user_id, memory):
        tools, prompt, voice = self.role.get_realtime_tools(user_id, memory)
        session_config = {
                "session": {
                    "type": "realtime",
                    "model": "gpt-realtime",
                    "output_modalities": ["audio"],
                    "audio": {
                        "output": {
                            "voice": voice,
                        },
                    },
                    "instructions": prompt,
                    "tools": tools,
                    "tool_choice": "auto"
                }
            }
        return session_config