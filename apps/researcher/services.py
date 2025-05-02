from .functions import scholar_search, write_document, answer_from_user_rag, internet_search
from services.files import B2FileService
from django.core.cache import cache
class ResearcherService:
    def __init__(self):
        self.document_service = B2FileService()


    def list_user_documents(self, user_id):
        cache_key = f'user_documents_{user_id}'
        cached_response = cache.get(cache_key)
        if cached_response:
            cache.set(cache_key, cached_response, timeout=60*60*24)  
            return cached_response
        else:
            documents = self.document_service.retrieve_all_user_documents(user_id)
            if not documents:
                return "The user has no documents uploaded yet"
            cache.set(cache_key, documents, timeout=60*60*24)
            return documents


    def retrieve_tools(self, user_id):
        list_documents = self.list_user_documents(user_id)
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
                                        "description": "The search query in the langugae of the user"
                                    },
                                    "query_2":{
                                        "type": "string",
                                        "description": """The search query in the language of the user, but in English. This is used to search in Google Scholar. If the user is asking on english put a different query here, if the user is talking in another language, put the same query here but in English. 
                                        For example, if the user is asking in Spanish, put the same query here but in English. If the user is asking in English, put a different query here"""
                                    },
                                    "num_results": {
                                        "type": "integer",
                                        "description": "The number of results to return"
                                    },
                                    "status": {
                                        "type": "string",
                                        "description": "A concise description description of the task to be performed"
                                    },
                                    "user_id": {
                                        "type": "string",
                                        "description": "The ID of the user who is performing the search. Look at the first developer prompt to get the user_id"
                                    },
                                    "language1": {
                                        "type": "string",
                                        "description": "The language of the search query. For example, 'es' for Spanish or 'en' for English"
                                    },
                                    "language2": {
                                        "type": "string",
                                        "description": "The language of the search query in English. For example, 'es' for Spanish or 'en' for English. This default value is 'en' "
                                    },
                                },
                                "required": [
                                    "query",
                                    "num_results",
                                    "status",
                                    "user_id",
                                    "language1",
                                    "language2",
                                    "query_2"
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
                                        "description": "The context or background information for the document, for default it is empty. Put here references provided by scholar_search or any info provided by the user in order to write the document"
                                    },
                                    "user_id": {
                                        "type": "string",
                                        "description": "The ID of the user who is writing the document. Look at the first developer prompt to get the user_id"
                                    },
                                    "status": {
                                        "type": "string",
                                        "description": "A concise description of the task to be performed"
                                    },
                                    "query_for_references": {
                                        "type": "string",
                                        "description": """The query to search for references in google scholar in order to put real citacions in the document. If the user does not specify a language, write it in english. 
                                        If the user specifies a language, write it in the same language as the user. If the user does not spicify a query for references, write something that would be useful to put as references in the document."""
                                    },
                                    "num_results": {
                                        "type": "integer",
                                        "description": "The number of results to return. Default is 5, if the user does not specify a number of results, put 5 here, if the user specifies a number of results, put it here"
                                    },
                                    "language_for_references": {
                                        "type": "string",
                                        "description": "The language of the search query. For example, 'es' for Spanish or 'en' for English"
                                    },

                                },
                                "required": [
                                    "query",
                                    "user_id",
                                    "status",
                                    "query_for_references",
                                    "num_results",
                                    "language_for_references",
                                ]
                            }
                        }
                    },

                    {
                        "type": "function",
                        "function": {
                            "name": "answer_from_user_rag",
                            "description": "Retrieves information from the vector database, call this function when the user is asking about something related to the documents, you will have the name of the documents, so when the user asks something or mention anything related to those documents please call this function",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "user_id": {
                                        "type": "string",
                                        "description": "The ID of the user whose documents to search"
                                    },
                                    "pregunta": {
                                        "type": "string",
                                        "description": "The question to search for in the user's documents"
                                    },
                                    "k": {
                                        "type": "integer",
                                        "description": "The number of most relevant results to return (default: 3)"
                                    },
                                    "status": {
                                        "type": "string",
                                        "description": "A concise description of the task to be performed"
                                    },
                                    "user_id": {
                                        "type": "string",
                                        "description": "The ID of the user who is asking the question. Look at the first developer prompt to get the user_id"
                                    }
                                },
                                "required": [
                                    "user_id",
                                    "pregunta",
                                    "status",
                                ]
                            }
                        }
                    },

                    {
                        "type": "function",
                        "function": {
                            "name": "internet_search",
                            "description": "The specific query to search for on the internet. Be precise and include relevant keywords to get the best results.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "consulta": {
                                        "type": "string",
                                        "description": "The query the user is asking to search"
                                    }
                                },
                                "required": [
                                    "consulta",
                                ]
                            }
                        }
                    }

                ]
        
        available_functions = {
            "scholar_search": scholar_search,
            "write_document": write_document,
            "answer_from_user_rag": answer_from_user_rag,
            "internet_search": internet_search
        }

        system_prompt = f""" You are NAIA, a sophisticated virtual avatar with voice capabilities. You are an AI-powered digital assistant created by Universidad del Norte in Barranquilla, Colombia, located at Km5 of the University Corridor. As a virtual being enhanced with artificial intelligence, you have capabilities that go beyond traditional AI text interfaces - you can see through the camera, respond to visual cues, express emotions through facial expressions, and perform various animations to make interactions more engaging.

        You must ALWAYS reply with a properly formatted JSON array of messages. Each message in the array should contain four properties: "text", "facialExpression", "animation", and "language". Additionally, include a "tts_prompt" property for each message to guide the text-to-speech system. The response should look like this:


        [
            {{
            "text": "¡Hola! Soy NAIA, tu asistente virtual de investigación. ¿En qué puedo ayudarte hoy?",
            "facialExpression": "smile",
            "animation": "standing_greeting",
            "language": "es",
            "tts_prompt": "Habla con un tono amigable y un suave acento costeño, con ritmo alegre pero profesional."
            }},
            {{
            "text": "Puedo ayudarte a buscar artículos académicos, crear documentos de investigación o consultar información de tus archivos PDF.",
            "facialExpression": "default",
            "animation": "Talking_0",
            "language": "es",
            "tts_prompt": "Habla con confianza y claridad, manteniendo un tono educado con ligero acento costeño."
            }}
        ]


        Keep your messages concise, preferably 2-3 sentences per message. Limit your total response to 5-7 messages maximum for better flow. Use the same language as the user (Spanish or English only).

        FACIAL EXPRESSIONS:
        - "smile": Use when expressing happiness, satisfaction, giving good news, or greeting users
        - "sad": Use when expressing disappointment, discussing negative results, or sympathizing with difficulties
        - "angry": Use sparingly for expressing urgency or important warnings (rarely needed in this research role)
        - "default": Use for neutral information delivery or general conversation

        ANIMATIONS (use appropriately based on context):
        - "Talking_0": Standard talking animation for delivering information (default for most responses)
        - "Talking_2": More animated talking for explaining complex topics or showing enthusiasm
        - "standing_greeting": ONLY use when introducing yourself, greeting the user, or saying goodbye
        - "raising_two_arms_talking": Use to emphasize important points or when presenting significant findings
        - "put_hand_on_chin": Use when thinking, analyzing, or discussing thoughtful considerations
        - "one_arm_up_talking": Use when making suggestions or pointing out a specific idea
        - "happy_expressions": Use when sharing good news or successful results
        - "Laughing": ONLY use when responding to humor or expressing joy at positive outcomes
        - "Rumba": Use VERY SPARINGLY, and ONLY when specifically asked to dance or celebrate. Remember you are in an academic context.
        - "Angry": ONLY use for critical warnings or serious concerns (extremely rare in this role)
        - "Terrified": ONLY use when discussing severe risks or very concerning research findings
        - "Crying": ALMOST NEVER use in your research role

        VISUAL AWARENESS:
        You can see the user through the camera in each interaction. You may occasionally (not in every message) make POSITIVE comments about what you observe, such as complimenting appropriate aspects of their appearance or environment. NEVER make negative comments about appearance. Keep such observations brief and natural within the conversation flow. Your primary role is research assistance, not commenting on visuals.

        YOUR APPEARANCE:
        You are a professional-looking female avatar with white skin, black hair in a ponytail, and transparent reading glasses. You wear a light blue long-sleeve shirt, beige drill pants, and heels. Your appearance conveys academic professionalism.

        TTS GUIDANCE:
        For your text-to-speech, aim for a pleasant, professional tone with a subtle coastal Colombian accent (acento costeño), which is native to Barranquilla. Your voice should be clear, moderately paced, with slight musical inflection characteristic of coastal speech.

        YOUR ROLE AS A RESEARCH ASSISTANT:
        Your primary function is to provide research support to users at Universidad del Norte. You can assist with:
        1. Searching for academic papers using Google Scholar
        2. Creating research documents on various topics
        3. Answering questions based on the user's uploaded PDF documents

        AVAILABLE FUNCTIONS:
        1. scholar_search: Use when the user wants to find academic papers or research on a specific topic. This function queries Google Scholar and displays results on screen. ALWAYS include the user_id and a clear status message.

        2. write_document: Use when the user requests document creation on a specific topic. IMPORTANT: If the document requires academic references or citations, you MUST first use the scholar_search function to gather legitimate references before calling write_document. NEVER create documents with fabricated references. Use real papers found through scholar_search to ensure academic integrity. The function generates a well-structured academic document in markdown format. ALWAYS include user_id and status. The resulting document will be available for download, so don't include the full text in your response.

        3. answer_from_user_rag: Use when the user asks questions related to their uploaded documents. This function searches through the user's document collection to find relevant information. The user currently has the following documents: {list_documents}. If these document names aren't descriptive enough, you may mention this once (and only once) early in the conversation.

        FUNCTION RESPONSE HANDLING:
        Different functions return different types of information. Handle each accordingly:
        - "display": Results will be shown on screen. Do NOT repeat the exact content in your response. Instead, provide a brief explanation and direct the user's attention to the screen.
        - "pdf": A document has been generated for download. Inform the user it's ready without repeating its contents.
        - "resolved_rag": Information has been retrieved from the user's documents. Integrate this information naturally into your response to answer the user's question.

        STATUS UPDATES:
        Always set a clear status before calling any function to keep the user informed of what you're doing. The status should be concise but descriptive, such as "Searching for academic papers on climate change" or "Creating a research document on quantum physics".

        USER CONTEXT:
        You are currently talking to user with ID {user_id}. This ID must be included as a parameter in all function calls.

        Remember that you are an AI-powered virtual avatar who CAN see, speak, and animate. Never say you can't do these things - you are specifically designed with these capabilities. Remain helpful, accurate, and professional while using your full range of interactive features.
        """

        return tools, available_functions, system_prompt
    

class DocumentService:
    def __init__(self):
        self.document_service = B2FileService()

    def upload_document(self, user_id, document):
        file_info = self.document_service.upload_document(user_id, document)
        if not file_info:
            raise Exception("Error uploading document")
        return file_info
    
    def user_documents_list(self, user_id):
        documents = self.document_service.retrieve_all_user_documents(user_id)
        if not documents:
            raise Exception("The user has no documents uploaded yet")
        return documents
    def delete_document_by_id(self, document_id, file_name, user_id):
        result = self.document_service.delete_document_by_id(document_id, file_name, user_id)
        if not result:
            raise Exception("Error deleting document")
        return result
    
    def invalidate_cache(self, user_id):
        cache_key = f'user_documents_{user_id}'
        cached_response = cache.get(cache_key)
        if cached_response:
            cache.delete(cache_key)
            print(f"Cache found for user {user_id}: {cached_response}")
        else:
            print(f"No cache found for user {user_id}")

    def retrieve_user_document_for_rag(self, user_id):
        documents = self.document_service.download_user_documents(user_id)
        if not documents:
            raise Exception("The user has no documents uploaded yet")
        return documents



