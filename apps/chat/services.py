from services.llm import LLMService
import json
from services.files import B2FileService
from .repositories import ChatRepository
from .functions import num_tokens_from_messages
from apps.status.services import delete_status
from apps.roles.services import RoleService
import time
max_tokens = 3000

def read_json_transcript(json_file_path):
    with open(json_file_path, "r") as json_file:
        return json.load(json_file)

class ChatService():

    def generate_response(self, user_input, user_id, role_id):
        total_start_time = time.time()
        timing_info = {}
        
        # 1. Get B2 File Service
        start_time = time.time()
        file_service = B2FileService()
        timing_info["b2_service_init"] = time.time() - start_time
        
        # 2. Get Role and delete status
        start_time = time.time()
        role = RoleService(role_id)
        delete_status(user_id, role_id)
        timing_info["role_and_status"] = time.time() - start_time
        
        # 3. Get tools and system prompt
        start_time = time.time()
        tools, available_tools, system_prompt = role.get_role(user_id)
        timing_info["get_tools_and_prompt"] = time.time() - start_time
        
        # 4. Get image URL
        start_time = time.time()
        image_url = file_service.get_current_file_url(user_id)
        timing_info["get_image_url"] = time.time() - start_time
        print("image_url", image_url)
        
        # 5. Get conversation history
        start_time = time.time()
        messages = ChatRepository.get_current_conversation(user_id, role_id)
        if not messages:
            messages = ChatRepository.get_last_conversation(user_id, role_id)
        timing_info["get_conversation"] = time.time() - start_time
        
        # 6. Count tokens
        start_time = time.time()
        num_tokens = num_tokens_from_messages(messages) if messages else 0
        timing_info["token_counting"] = time.time() - start_time
        print("num_tokens", num_tokens)
        
        # 7. Initialize LLM service
        start_time = time.time()
        llm_service = LLMService(available_tools, tools, system_prompt)
        timing_info["llm_service_init"] = time.time() - start_time
        
        # 8. Generate LLM response (this is expected to be the longest step)
        start_time = time.time()
        response = llm_service.generate_response(user_input, image_url, messages)
        timing_info["llm_response_generation"] = time.time() - start_time
        
        # 9. Save conversation
        start_time = time.time()
        ChatRepository.save_current_conversation(user_id, role_id, json.dumps(response["messages"]))
        timing_info["save_conversation"] = time.time() - start_time
        
        # 10. Final response processing
        start_time = time.time()
        response["num_tokens"] = num_tokens
        if num_tokens >= max_tokens:
            response["warning"] = "The conversation has reached the maximum number of tokens. The conversation will be resumed."
        response.pop("messages")
        timing_info["final_processing"] = time.time() - start_time
        
        # Total time
        total_time = time.time() - total_start_time
        timing_info["total_time"] = total_time
        
        # Print timing information
        print("\n--- TIMING INFORMATION ---")
        print(f"Total processing time: {total_time:.4f} seconds")
        for step, duration in timing_info.items():
            percentage = (duration / total_time) * 100
            print(f"  {step}: {duration:.4f} seconds ({percentage:.1f}%)")
        print("-------------------------\n")
        
        # Add timing info to response for debugging
        response["timing_info"] = timing_info
        
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
        if isinstance(messages, str):
            messages = json.loads(messages)
        elif isinstance(messages, list):
            messages = [json.loads(message) if isinstance(message, str) else message for message in messages]
        for message in messages:
            if message["role"] == "assistant":
                if isinstance(message["content"], str):
                    try:
                        message["content"] = json.loads(message["content"])
                    except json.JSONDecodeError:
                        pass
        return messages

    def make_resume(self, messages):
        num_tokens = num_tokens_from_messages(json.loads(messages) if isinstance(messages, str) else messages)
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