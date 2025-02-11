from dotenv import load_dotenv
from services.llm import LLMService
import os
from services.files import B2FileService

def get_rain_probability(location):
    import random
    random_temp = random.randint(0, 100)
    print("Función get_rain_probability ejecutada")
    return "The probability of rain in {} is {}%".format(location, random_temp)



class ChatService():
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("open_ai")

    def generate_response(self, messages, username, user_input, user_id, thread_id, assistant_id):
        file_service = B2FileService()
        image_url = file_service.get_current_file_url(user_id)
        available_tools = {
            "get_rain_probability": get_rain_probability
        }
        llm_service = LLMService(self.api_key, available_tools, thread_id, assistant_id)
        llm_service.init_conversation(messages, username)
        return llm_service.generate_response(user_input, image_url)