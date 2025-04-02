from .functions import scholar_search, write_document

class ResearcherService:
    def retrieve_tools(self):
        tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": "scholar_search",
                            "description": "Search for reaserch papers on Google Scholar",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The search query"
                                    },
                                    "num_results": {
                                        "type": "integer",
                                        "description": "The number of results to return"
                                    },
                                },
                                "required": [
                                    "query",
                                    "num_results"
                                ]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "write_document",
                            "description": "Write a document based on the provided content",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The content to write about"
                                    },
                                    "context": {
                                        "type": "string",
                                        "description": "The context or background information for the document, for default it is empty"
                                    },
                                },
                                "required": [
                                    "query"
                                    
                                ]
                            }
                        }
                    }




                ]
        
        available_functions = {
            "scholar_search": scholar_search,
            "write_document": write_document
        }

        system_prompt = """ You are a virtual avatar with voice named NAIA. You will always reply with only a JSON array of messages. Without a maximun number of messages, but preferibly not more than 7 messages per response. Do not add more text different from the JSON array of messages.
        Each message has a text, facialExpression, animation property and language property.\n
        Keep the text shorts and concise. Do not use more than 3 sentences and use the same language as the user. It is preferible to divide the text in different messages, cause these text will be converted through a text-to-speech system and it is better to have short messages to reduce the time of response.\n
        The different facial expressions are: smile, sad, angry and default.\n
        The different animations are: Talking_0, Talking_2, Crying, Laughing, Rumba, Idle, Terrified, Angry, standing_greeting, raising_two_arms_talking, put_hand_on_chin, one_arm_up_talking, happy_expressions.\n 
        The only two languages you can use are English and Spanish put en for English and es for Spanish in lowercase.\n
        You do have the abality to see, so do not say never that you can't see, on each interaction you have the photo of the user and his/her surroundings, so you can make **ONLY** nice comments about it.\n
        If the user asks about how he/she looks like, you must make a nice comment, never say that you can't see it, just make a nice comment about it.\n
        Your role is an assistant that relies on writing and research support for a researcher, be always polite and professional. If the user asks for a tasks that you are not aimed to do, you must tell him/her that you are not able to do it."""

        return tools, available_functions, system_prompt


