from openai import OpenAI
import openai
import json
from dotenv import load_dotenv
import os
class LLMService:
    def __init__(self, available_tools, thread_id, assistant_id):
        load_dotenv()
        self.assistant_id = assistant_id
        self.client = OpenAI(api_key=os.getenv("open_ai"))
        self.available_tools = available_tools
        self.thread_id = thread_id

    def _init_conversation(self, messages, username, user_input, image_url):
        if not self.thread_id:
            if messages:
                messages_array = json.loads(messages)
                messages_array.insert(0, {
                    "role": "user",
                    "content": f"This is just an info message. From now on you will address me as {username}. If you used to call me by another name, do not use it cause this is a different person using this app."
                })
            else:
                messages_array = [{
                    "role": "user",
                    "content": f"This is just an info message. From now on you will address me as {username}."
                }]
            messages_array.insert(0, self._create_message_input(user_input, image_url))
            thread = self.client.beta.threads.create()
            for msg in reversed(messages_array):  
                self.client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role=msg["role"],
                    content=msg["content"]
                )
        else:
            print("Recuperando el thread existente...")
            try:
                thread = self.client.beta.threads.retrieve(self.thread_id)
                print("Thread recuperado con id: ", thread.id)
            except Exception as e:
                raise Exception("Failed to retrieve thread:", e)
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"This is just an info message. From now on you will address me as {username}. If you used to call me by another name, do not use it cause this is a different person using this app."
            )
            new_input = self._create_message_input(user_input, image_url)
            print("Creando nuevo mensaje...")
            print(new_input)
            print("*"*50)
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=new_input["content"]
            )
        return thread
    
    def _create_message_input(self, user_input, image_url):
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
    
    def retrieve_thread_messages(self):
        return self.client.beta.threads.messages.list(thread_id=self.thread_id)

    
    def generate_response(self, user_input, image_url, username, messages):
        thread = self._init_conversation(messages, username, user_input, image_url)
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=self.assistant_id
        )
        if run.status == 'completed':
            message_response = self.client.beta.threads.messages.list(
                thread_id=thread.id
            )
            print(message_response)

        else:
            print(run.status)

        if run.status == "failed":
            print(run)
            raise Exception("Failed to run model")
        if run.required_action is not None:
            tool_outputs = []
            for tool in run.required_action.submit_tool_outputs.tool_calls:
                if tool.function.name in self.available_tools.keys():
                    function_to_call = self.available_tools[tool.function.name]
                    function_args = json.loads(tool.function.arguments)
                    tool_output = function_to_call(**function_args)
                    tool_outputs.append(
                        {
                            "tool_call_id": tool.id,
                            "output": tool_output
                        }
                    )

            if tool_outputs:
                try:
                    run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                    )
                    print("Tool outputs submitted successfully.")
                except Exception as e:
                    print("Failed to submit tool outputs:", e)
                else:
                    print("No tool outputs to submit.")


            if run.status == 'completed':
                message_response = self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                print(message_response)
            else:
                print(run.status)
        
        messages = []
        for msg in message_response.data:
            if msg.role == "assistant" and hasattr(msg, "tool_calls"):
                messages.append({
                    "role": msg.role,
                    "content": " ".join(content.text.value for content in msg.content if hasattr(content, "text")),
                    "tool_calls": [
                        {
                            "function_name": tool.function.name,
                            "arguments": tool.function.arguments,
                            "tool_call_id": tool.id
                        } for tool in msg.tool_calls
                    ]
                })
            else:
                messages.append({
                    "role": msg.role,
                    "content": " ".join(content.text.value for content in msg.content if hasattr(content, "text"))
                })
        response = messages[0]["content"]
        print("*"*50)
        print("message_data", response)
        print("*"*50)

        json_response = {
            "messages": messages,
            "response": response,
            "thread_id": thread.id
        }

        return json_response
    
    @staticmethod
    def delete_thread(thread_id):
        client = OpenAI(api_key=os.getenv("open_ai"))
        try:
            client.beta.threads.delete(thread_id)
        except Exception as e:
            raise Exception("Failed to delete thread:", e)
