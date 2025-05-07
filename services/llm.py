from openai import OpenAI
import json
from dotenv import load_dotenv
import os
import time
import requests


class LLMService:
    _client = None

    def __init__(self, available_tools, tools, system_prompt):
        load_dotenv()
        self.system_prompt = system_prompt
        if LLMService._client is None:
            LLMService._client = OpenAI(api_key=os.getenv("open_ai"))
        self.client = LLMService._client
        self.available_tools = available_tools
        self.tools = tools

    def _init_conversation(self, messages, user_input, image_url):
        if messages:
            print("Mensajes desde la base de datos.... ")
            messages_array = messages
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
            print("No se ha añadido una imagen a la conversación")
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
            # Verify image URL is accessible
            try:
                response = requests.head(image_url, timeout=5)
                if response.status_code < 200 or response.status_code >= 300:
                    print(f"La imagen no es accesible. Código de estado: {response.status_code}")
                    return {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_input
                            }
                        ],
                    }
            except Exception as e:
                print(f"Error al verificar la URL de la imagen: {str(e)}")
                return {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_input
                        }
                    ],
                }
                
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
        
    def _clean_json_response(self, content):
        """
        Limpia el contenido de la respuesta para extraer el JSON literal si está envuelto
        en comillas invertidas y la palabra json.
        """
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {content}") from e


    
    def generate_response(self, user_input, image_url, messages):
        model = "gpt-4.1-mini"
        messages = self._init_conversation(messages, user_input, image_url)
        start_time = time.time()
        function_results = []
        
     
        max_function_chain_length = 5
        current_chain_length = 0
        
        # Process the initial request
        completions = self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=self.tools
        )
        response = completions.choices[0].message
        print(f"Initial response type: {'content' if response.content else response}")
        print(f"Initial response: {response.content}")
        while response.content is None and response.tool_calls and current_chain_length < max_function_chain_length:
            current_chain_length += 1
            print(f"Processing function call {current_chain_length} of max {max_function_chain_length}")

            # Add assistant's function call message
            assistant_message = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    } for tool_call in response.tool_calls
                ]
            }
            messages.append(assistant_message)
            
            # Execute each tool call
            for tool_call in response.tool_calls:
                if tool_call.function.name in self.available_tools.keys():
                    function_to_call = self.available_tools[tool_call.function.name]
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"Executing function: {tool_call.function.name}")
                    tool_output = function_to_call(**function_args)
                    
                    # Add function result to message history
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(json.dumps(tool_output))
                    })
                    
                    # Track all function results for the final response
                    function_results.append(tool_output)
            
            # Get the next response based on the function results
            completions = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=self.tools,
            )
            response = completions.choices[0].message
            print(f"Next response type: {'content' if response.content else 'tool_call'}")
        
        # If we got a text response or hit the max chain length
        if response.content is not None:
            # Add the final text response
            assistant_message = {"role": "assistant", "content": response.content}
            messages.append(assistant_message)
        elif current_chain_length >= max_function_chain_length:
            # We hit the maximum chain length without getting a text response
            # Force a final response without tool calls
            print("Hit maximum function chain length, forcing final response")
            completions = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=None,  # Disable tools for final response
            )
            final_content = completions.choices[0].message.content
            messages.append({"role": "assistant", "content": final_content})
        
        # Final processing
        messages.pop(0)  # Remove the developer message
        messages = self._eliminate_image_from_message(messages)
        end_time = time.time()
        
        # Get the final content for the response
        final_message = messages[-1]
        final_content = final_message.get("content", "")
        
        print(f"Final response content: {final_content}")
        json_response = {
            "response": self._clean_json_response(final_content) if final_content else {},
            "messages": messages,
            "function_results": function_results,
            "processing_time": end_time - start_time
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
            model = "gpt-4.1-mini"

            if isinstance(messages, str):
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

