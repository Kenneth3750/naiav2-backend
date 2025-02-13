from dotenv import load_dotenv
from services.llm import LLMService
import os
from services.files import B2FileService
from .repositories import ChatRepository

def get_rain_probability(location):
    import random
    random_temp = random.randint(0, 100)
    print("Función get_rain_probability ejecutada")
    return "The probability of rain in {} is {}%".format(location, random_temp)



class ChatService():
    def generate_response(self, username, user_input, user_id, thread_id, assistant_id, is_first_message):
        role_id = 1
        file_service = B2FileService()
        image_url = file_service.get_current_file_url(user_id)
        messages = None
        if not thread_id:
            messages = ChatRepository.get_last_conversation(user_id, role_id)
        available_tools = {
            "get_rain_probability": get_rain_probability
        }
        llm_service = LLMService(available_tools, thread_id, assistant_id)
        return llm_service.generate_response(user_input, image_url, username, messages)
    
    def delete_current_thread(self, thread_id):
        LLMService.delete_thread(thread_id)
