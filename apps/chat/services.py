from dotenv import load_dotenv
from services.llm import LLMService
import os
import json
from services.files import B2FileService
from .repositories import ChatRepository
from .functions import num_tokens_from_messages

max_tokens = 3000

def get_rain_probability(location):
    import random
    random_temp = random.randint(0, 100)
    print("Función get_rain_probability ejecutada")
    return "The probability of rain in {} is {}%".format(location, random_temp)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_rain_probability",
            "description": "Get the probability of rain for a specific location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g., San Francisco, CA"
                    }
                },
                "required": [
                    "location"
                ]
            }
        }
    }
]



class ChatService():
    def generate_response(self, username, user_input, user_id, role_id):
        file_service = B2FileService()
        image_url = file_service.get_current_file_url(user_id)
        messages = ChatRepository.get_current_conversation(user_id, role_id)
        if not messages:
            print("No hay mensajes guardados en redis, buscando en la base de datos...")
            messages = ChatRepository.get_last_conversation(user_id, role_id)
            print("mensajes", messages)
        available_tools = {
            "get_rain_probability": get_rain_probability
        }
        num_tokens = num_tokens_from_messages(json.loads(messages))
        system_prompt = "You are a helpful assistant. You can provide information about the weather, news, or any other topic. Be chatty and friendly. Your name is NAIA. About the images on each input you just need to say nice comments about the user clothes or the background."
        llm_service = LLMService(available_tools, tools, system_prompt)
        response = llm_service.generate_response(user_input, image_url, username, messages)
        print("Guardando conversación actual...")
        ChatRepository.save_current_conversation(user_id, role_id, json.dumps(response["messages"]))
        response["num_tokens"] = num_tokens
        if num_tokens >= max_tokens:
            response["warning"] = "The conversation has reached the maximum number of tokens. The conversation will be resumed."
        response.pop("messages")
        return response
    
    def delete_current_conversation(self, user_id, role_id):
        ChatRepository.delete_current_conversation(user_id, role_id)

    def save_current_conversation(self, user_id, role_id):
        messages = ChatRepository.get_current_conversation(user_id, role_id)
        messages = self.make_resume(messages)
        ChatRepository.update_or_create_today_conversation(user_id, messages, role_id)

    
    def save_and_update_current_conversation(self, user_id, role_id):
        messages = ChatRepository.get_current_conversation(user_id, role_id)
        messages = self.make_resume(messages)
        ChatRepository.update_or_create_today_conversation(user_id, messages, role_id)
        ChatRepository.save_current_conversation(user_id, role_id, json.dumps(messages))


    def get_conversation(self, user_id, role_id):
        messages = ChatRepository.get_current_conversation(user_id, role_id)
        if not messages:
            messages = ChatRepository.get_last_conversation(user_id, role_id)
        messages = self.make_resume(messages)
        return json.loads(messages)

    def make_resume(self, messages):
        num_tokens = num_tokens_from_messages(json.loads(messages))
        if num_tokens > max_tokens:
            new_messages = LLMService.make_resume(messages)
            return new_messages
        return messages
        
