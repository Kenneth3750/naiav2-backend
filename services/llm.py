from openai import OpenAI
# import openai 
import json
from dotenv import load_dotenv
import os
import time

class LLMService:
    def __init__(self, available_tools, tools, system_prompt):
        load_dotenv()
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=os.getenv("open_ai"))
        self.available_tools = available_tools
        self.tools = tools

    def _init_conversation(self, messages, user_input, image_url):
        if messages:
            print("Mensajes desde la base de datos.... ")
            messages_array = json.loads(messages)
            messages_array.insert(0, {"role": "developer", "content": self.system_prompt})
        else:
            print("No hay mensajes desde la base de datos, iniciando conversación...")
            messages_array = [{
                "role": "developer",
                "content": self.system_prompt
            }]

        messages_array.append(self._create_message_input(user_input, image_url))

        return messages_array
    
    def _create_message_input(self, user_input, image_url):
        if image_url is None:
            return {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_input
                    }
                ],
            }
        else:
            return {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text",
                            "text": user_input
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": "low"
                            }
                        },
                    ],
                }
    
    def _eliminate_image_from_message(self, messages):
        for message in messages:
            if isinstance(message["content"], list):
                message["content"] = [item for item in message["content"] if item["type"] != "image_url"]
        return messages
    @staticmethod
    def retrieve_thread_messages(thread_id):
        load_dotenv()
        client = OpenAI(api_key=os.getenv("open_ai"))
        try:
            return client.beta.threads.messages.list(thread_id=thread_id)
        except Exception as e:
            raise Exception("Failed to retrieve thread messages:", e)

    
    def generate_response(self, user_input, image_url, messages):
        messages = self._init_conversation(messages, user_input, image_url)
        start_time = time.time()
        completions = self.client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=messages,
            tools=self.tools
        )
        function_results = []
        response = completions.choices[0].message
        if response.content is not None:
            assistant_message = {"role": "assistant", "content": response.content}
            messages.append(assistant_message)
            messages.pop(0)  # Remove the developer message
            messages = self._eliminate_image_from_message(messages)
            end_time = time.time()
            response_time = end_time - start_time
            json_response = {
                "response": response.content,
                "messages": messages,
                "response_time": response_time,
                "function_results": function_results
            }
            return json_response
        tool_calls = response.tool_calls

        if tool_calls:
            assistant_message = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",  # Añadido el campo type
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    } for tool_call in tool_calls
                ]
            }
            messages.append(assistant_message)
            
            for tool_call in tool_calls:
                if tool_call.function.name in self.available_tools.keys():
                    function_to_call = self.available_tools[tool_call.function.name]
                    function_args = json.loads(tool_call.function.arguments)
                    tool_output = function_to_call(**function_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(json.dumps(tool_output))
                    })
                    function_results.append(tool_output)
 

            second_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=self.tools,
            )

            final_message = {"role": "assistant", "content": second_response.choices[0].message.content}
            messages.append(final_message)
            messages.pop(0)
            messages = self._eliminate_image_from_message(messages)  
            end_time = time.time()
            json_response = {
                "response": second_response.choices[0].message.content,
                "messages": messages,
                "response_time": end_time - start_time,
                "function_results": function_results
            }
            return json_response
    
    @staticmethod
    def delete_thread(thread_id):
        load_dotenv()
        client = OpenAI(api_key=os.getenv("open_ai"))
        try:
            client.beta.threads.delete(thread_id)
        except Exception as e:
            raise Exception("Failed to delete thread:", e)
        

    @staticmethod 
    def make_resume(messages):
        try:
            client = OpenAI(api_key=os.getenv("open_ai"))
            model = "gpt-4o-mini"

            messages = json.loads(messages)

            resume_prompt = """This conversation is near to exceed the context window of an AI model.
            Your task is to summarize the json in a way that the AI can understand the context of the conversation 
            and have a strong memory of the user's preferences.
            You must respond with only a text message that summarizes the json. 
            You must start the message with the words "Summary of last conversation:".
            Do not add any other information to the response. Do not greet the user or ask questions. 
            Do not add anything different from the summary.
            Make sure to add on the resume specific details that the AI should remember about the user and the conversation. 
            Details like specific names, dates, places, numbers, and any othe relevant information."""

            messages.append({
                "role": "developer",
                "content": resume_prompt
            })

            completion = client.chat.completions.create(
                model=model,
                messages=messages
            )
            resume_text = completion.choices[0].message.content
    
            # Crear nuevos mensajes con el resumen
            new_messages = [
                {"role": "developer", "content": resume_text}
            ]

            return new_messages
        except Exception as e:
            raise Exception("Failed to make resume:", e)

