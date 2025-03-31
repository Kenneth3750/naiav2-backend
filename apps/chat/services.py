from dotenv import load_dotenv
from services.llm import LLMService
import os
import json
from services.files import B2FileService
from .repositories import ChatRepository
from .functions import num_tokens_from_messages
from apps.roles.services import RoleService

max_tokens = 3000

def read_json_transcript(json_file_path):
    with open(json_file_path, "r") as json_file:
        return json.load(json_file)

class ChatService():
    def generate_response(self, user_input, user_id, role_id):
        file_service = B2FileService()
        role = RoleService(role_id)
        tools, available_tools, system_prompt = role.get_role()
        image_url = file_service.get_current_file_url(user_id)
        messages = ChatRepository.get_current_conversation(user_id, role_id)
        if not messages:
            messages = ChatRepository.get_last_conversation(user_id, role_id)
        num_tokens = num_tokens_from_messages(json.loads(messages)) if messages else 0
        llm_service = LLMService(available_tools, tools, system_prompt)
        response = llm_service.generate_response(user_input, image_url, messages)
        ChatRepository.save_current_conversation(user_id, role_id, json.dumps(response["messages"]))
        response["num_tokens"] = num_tokens
        response["response"] = json.loads(response["response"])
        if num_tokens >= max_tokens:
            response["warning"] = "The conversation has reached the maximum number of tokens. The conversation will be resumed."
        response.pop("messages")
        # response['lipsync'] = read_json_transcript("default.json")
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
        messages = json.loads(messages)
        for message in messages:
            if message["role"] == "assistant":
                if isinstance(message["content"], str):
                    try:
                        message["content"] = json.loads(message["content"])
                    except json.JSONDecodeError:
                        pass
        return messages

    def make_resume(self, messages):
        num_tokens = num_tokens_from_messages(json.loads(messages))
        if num_tokens > max_tokens:
            new_messages = LLMService.make_resume(messages)
            return new_messages
        return messages
    
    def upload_image(self, user_id, image):
        file_service = B2FileService()
        is_uploaded = file_service.upload_image(user_id, image)
        if not is_uploaded:
            raise Exception("The image could not be uploaded. Check the B2 service.")
        pass        
