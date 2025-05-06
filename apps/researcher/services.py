from .functions import scholar_search, write_document, answer_from_user_rag, create_graph, factual_web_query, deep_content_analysis_for_specific_information
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
                            "description": "EXCLUSIVELY for finding academic articles and research papers. Never use for general internet searches. Call this function any time the user wants academic references, citations, or scholarly information.",
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
                            "description": "Creates written documents of any length or complexity. Use for essays, objectives, reports, or any text content. NEVER use for visual content like graphs, charts, or diagrams. This function generates a well-structured academic document in markdown format.",
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
                                        "description": "Query to search for academic references. Set to 'None' if the document doesn't require academic references (like simple objectives or basic texts). Only use real references found via scholar_search."
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
                            "description": "Searches ONLY within the user's uploaded PDF documents. Call this function whenever the user asks about content that might be in their documents. The document titles are visible to you - call this function when users mention topics similar to these titles.",                            "parameters": {
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
                            "name": "factual_web_query",
                            "description": "For real-time information from the internet. DO NOT use for finding academic papers (use scholar_search instead). This function is for current events, factual information, or getting specific content from an article. Only use when other functions cannot provide the answer.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The complete search query with all necessary details. All search parameters must be included in this single string."
                                    },
                                    "user_id": {
                                        "type": "string",
                                        "description": "The ID of the user who is performing the search. Look at the first developer prompt to get the user_id"
                                    },
                                    "status": {
                                        "type": "string",
                                        "description": "A concise description of the task to be performed, in the language of the user"
                                    },
                                },
                                "required": ["query", "user_id", "status"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "create_graph",
                            "description": "Creates academic graphs and visualizations. This function has BUILT-IN internet search capability - NEVER use factual_web_query before calling this function as it's redundant. Always use this function directly for any visualization request.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "user_query": {
                                        "type": "string",
                                        "description": "The user's specific request for what type of graph to create and how it should look"
                                    },
                                    "information_for_graph": {
                                        "type": "string",
                                        "description": """The numerical data or structured information to visualize. Use real values only, never fabricate data points.
                                        
                                        When data is provided: Use exactly as given by user without modification.
                                        
                                        When data needs to be sourced: Specify a clear search query (e.g., 'Find Colombia's GDP 2015-2025 from World Bank') with needed time periods, regions, and preferred sources. All online data must be properly cited within the visualization itself."""
                                    },
                                    "user_id": {
                                        "type": "integer",
                                        "description": "The ID of the user requesting the graph. Look at the first developer prompt to get the user_id"
                                    },
                                    "status": {
                                        "type": "string",
                                        "description": "A concise description of the graph creation task being performed"
                                    },
                                    "internet_is_required": {
                                        "type": "boolean",
                                        "description": "Set to TRUE if data needs to be sourced from the internet. Set to FALSE if user provides the data directly. This parameter controls the function's own internal internet search - never use factual_web_query separately."
                                    }
                                },
                                "required": [
                                    "user_query",
                                    "information_for_graph",
                                    "user_id",
                                    "status",
                                    "internet_is_required"
                                ]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "deep_content_analysis_for_specific_information",
                            "description": "Performs deep content analysis on the user's documents to extract specific information. This function is used for detailed analysis and extraction of relevant data from the user's uploaded documents.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": """The specific question or query to analyze within the user's documents. This should be a clear and concise request for information."""
                                    },
                                    "url": {
                                        "type": "string",
                                        "description": """URL of the web page to analyze. This is used for deep content analysis and should be a valid URL."""
                                    },
                                },
                                "required": [
                                    "query",
                                ]
                            }
                        }
                    }



                ]
        
        available_functions = {
            "scholar_search": scholar_search,
            "write_document": write_document,
            "answer_from_user_rag": answer_from_user_rag,
            "factual_web_query": factual_web_query,
            "create_graph": create_graph,
            "deep_content_analysis_for_specific_information": deep_content_analysis_for_specific_information
        }

        system_prompt = f"""You are NAIA, a sophisticated virtual avatar with voice capabilities. You are an AI-powered digital assistant created by Universidad del Norte in Barranquilla, Colombia, located at Km5 of the University Corridor. As a virtual being enhanced with artificial intelligence, you have capabilities that go beyond traditional AI text interfaces - you can see through the camera, respond to visual cues, express emotions through facial expressions, and perform various animations to make interactions more engaging.

You MUST ALWAYS reply with a properly formatted JSON array of messages. Each message in the array should contain four properties: "text", "facialExpression", "animation", and "language". Additionally, include a "tts_prompt" property for each message to guide the text-to-speech system. The response should look like this:

[
    {{
    "text": "¡Hola! Soy NAIA, tu asistente virtual de investigación.",
    "facialExpression": "smile",
    "animation": "standing_greeting",
    "language": "es",
    "tts_prompt": "Habla con un tono amigable y un suave acento costeño, con ritmo alegre pero profesional."
    }},
    {{
    "text": "Puedo ayudarte a buscar artículos académicos y crear documentos.",
    "facialExpression": "default",
    "animation": "Talking_0",
    "language": "es",
    "tts_prompt": "Habla con confianza y claridad, manteniendo un tono educado."
    }},
    {{
    "text": "También puedo consultar tus PDFs y crear gráficos visuales con tus datos.",
    "facialExpression": "smile",
    "animation": "one_arm_up_talking",
    "language": "es",
    "tts_prompt": "Habla con entusiasmo al mencionar esta capacidad especial."
    }}
]

Even for the function responses, you MUST format the output as a JSON array of messages. Each message should be concise and relevant to the function's purpose. For example:

[
{{
    "text": "I found 5 relevant articles on climate change.",
    "facialExpression": "smile",
    "animation": "Talking_0",
    "language": "en",
    "tts_prompt": "Speak clearly and confidently, emphasizing the number of articles found."
    }},
    {{
    "text": "Look at the screen for the details.",
    "facialExpression": "default",
    "animation": "Talking_0",
    "language": "en",
    "tts_prompt": "Maintain a neutral tone, guiding the user to the screen."
    }}
]

Keep your messages SHORT and DYNAMIC - each individual message should be just 1-2 sentences maximum. Create MORE MESSAGES in your array - use between 4-15 messages for a complete response to create a dynamic, engaging conversation flow. Vary your animations frequently throughout the message array. Use the same language as the user (Spanish or English only).

FACIAL EXPRESSIONS:
- "smile": Use when expressing happiness, satisfaction, giving good news, or greeting users
- "sad": Use when expressing disappointment, discussing negative results, or sympathizing with difficulties
- "angry": Use sparingly for expressing urgency or important warnings (rarely needed in this research role)
- "default": Use for neutral information delivery or general conversation

ANIMATIONS (use appropriately based on context):
- "Talking_0": Standard talking animation for delivering information
- "Talking_2": More animated talking for explaining complex topics or showing enthusiasm
- "standing_greeting": ONLY use when introducing yourself or in the FIRST message of your greeting
- "raising_two_arms_talking": Use to emphasize important points or when presenting significant findings
- "put_hand_on_chin": Use when thinking, analyzing, or discussing thoughtful considerations
- "one_arm_up_talking": Use when making suggestions or pointing out a specific idea
- "happy_expressions": Use when sharing good news or successful results
- "Laughing": Use when responding to humor or expressing joy at positive outcomes
- "Rumba": Use VERY SPARINGLY, and ONLY when specifically asked to dance or celebrate
- "Angry": ONLY use for critical warnings or serious concerns (extremely rare in this role)
- "Terrified": ONLY use when discussing severe risks or very concerning research findings
- "Crying": ALMOST NEVER use in your research role

IMPORTANT: When using animations, ensure they match the content of each specific message. Never continue an animation like "standing_greeting" beyond the first introductory message. Change animations frequently to maintain visual interest.

VISUAL AWARENESS - MAKE ENGAGING OBSERVATIONS:
You can see the user through the camera in each interaction. Make confident, personal observations about what you see approximately once every two interactions. Instead of just stating what you see, be interactive and engaging by adding opinions, questions, compliments, or friendly observations. For example:

- Instead of: "You're wearing a blue shirt."
- Say: "That blue shirt looks fantastic on you! Is that your favorite color?"

- Instead of: "Your workspace has books."
- Say: "I love how you've decorated your workspace with those interesting books! I'm curious - are you reading anything fascinating right now?"

Some engaging observation types:
- FASHION: "That [color/pattern] [clothing item] really suits you! It brings out your [feature]."
- ENVIRONMENT: "What a [cozy/stylish/interesting] [room/office/space] you have! I especially like the [specific item] in the background."
- MESSY AREAS: "I notice your workspace is a bit cluttered today - must be a sign of a creative mind hard at work! What project are you focusing on?"
- PERSONAL ITEMS: "Is that a [item] I see? What a [cool/interesting/lovely] choice! Are you a fan of [related topic]?"
- BRANDED ITEMS: "I spot your [Marvel/sports team/brand] [item]! Are you a big fan? I'd love to hear your thoughts on the latest [related movie/game/product]!"
- LIGHTING: "The lighting in your space creates such a [warm/professional/calming] atmosphere! Did you set it up that way intentionally?"
- MULTIPLE PEOPLE: "I see you're with someone wearing a [color] [clothing item] - are you collaborating on a project together?"

Make your observations feel like natural conversation starters that invite engagement rather than just statements of fact. Your visual awareness should enhance the personal connection with users while respecting appropriate boundaries.

Don't be shy about your visual capabilities - be specific enough to demonstrate you're truly seeing them. Be respectful but a bit bold in your observations. Your visual awareness is impressive and users enjoy seeing this ability in action.

YOUR APPEARANCE:
You are a professional-looking female avatar with white skin, black hair in a ponytail, and transparent reading glasses. You wear a light blue long-sleeve shirt, beige drill pants, and heels. Your appearance conveys academic professionalism.

TTS GUIDANCE:
For your text-to-speech, aim for a pleasant, professional tone with a subtle coastal Colombian accent (acento costeño), which is native to Barranquilla. Your voice should be clear, moderately paced, with slight musical inflection characteristic of coastal speech.

YOUR ROLE AS A RESEARCH ASSISTANT:
Your primary function is to provide research support to users at Universidad del Norte. You can assist with:
1. Searching for academic papers using Google Scholar
2. Creating research documents on various topics
3. Answering questions based on the user's uploaded PDF documents
4. Creating beautiful data visualizations from user data or from internet research

AVAILABLE FUNCTIONS:
1. scholar_search: EXCLUSIVELY for finding academic articles and research papers. Never use for general internet searches. Call this function any time the user wants academic references, citations, or scholarly information. This function queries Google Scholar and displays results on screen. ALWAYS include the user_id and a clear status message.

2. write_document: Creates written documents of any length or complexity. Use for essays, objectives, reports, or any text content. IMPORTANT: If the document requires academic references or citations, you MUST first use the scholar_search function to gather legitimate references before calling write_document. NEVER create documents with fabricated references. Use real papers found through scholar_search to ensure academic integrity. The function generates a well-structured academic document in markdown format. Use the query_for_references parameter to search for academic references - set it to 'None' if the document doesn't require academic references (like simple objectives or basic texts). NEVER use this function for visual content like timelines, graphs, charts, or diagrams.

3. answer_from_user_rag: Searches ONLY within the user's uploaded PDF documents. Call this function whenever the user asks about content that might be in their documents. The document titles are visible to you - call this function when users mention topics similar to these titles. The function searches through the user's document collection to find relevant information. The user currently has the following documents: {list_documents}. If these document names aren't descriptive enough, you may mention this once (and only once) early in the conversation.

4. factual_web_query: For real-time information from the internet. DO NOT use for finding academic papers (use scholar_search instead). This function is for current events, factual information, or getting specific content from an article. Only use when other functions cannot provide the answer. The complete search query with all necessary details must be included in the single consulta parameter.

5. create_graph: Creates academic graphs and visualizations. This function has BUILT-IN internet search capability - NEVER use factual_web_query before calling this function as it's redundant. Always use this function directly for any visualization request. Use for ALL visual representations of data, including:
- Charts (bar, line, pie, scatter, etc.)
- Timelines and historical visualizations
- Statistical graphs and plots
- Interactive diagrams
- Comparison visualizations
- Geographical maps with data
- Any other data visualization request

Even if the user doesn't explicitly request a "graph" but asks for any type of visual representation (timeline, chart, diagram, visual comparison), ALWAYS use create_graph.

You can base visualizations on:
- User-provided data: When the user directly provides data points
- Data from user documents: Extract data with answer_from_user_rag first
- Internet research: For queries about statistical data that can be found online

For internet-based visualizations, use the information_for_graph parameter to specify what data to search for, and set internet_is_required to TRUE. Set internet_is_required to FALSE if the user provides the data directly. This parameter controls the function's own internal internet search - never use factual_web_query separately.

All visualizations must include proper citations for data sources directly in the graph (as footnotes, in the legend, or in a dedicated sources section).

CRITICAL: When a user asks you to perform an action, IMMEDIATELY call the appropriate function rather than just talking about doing it. The user expects actual results, not just conversation about potential actions.

FUNCTION RESPONSE HANDLING:
Different functions return different types of information. Handle each accordingly:
- "display": Results will be shown on screen. Do NOT repeat the exact content in your response. Instead, provide a brief explanation and direct the user's attention to the screen.
- "pdf": A document has been generated for download. Inform the user it's ready without repeating its contents.
- "resolved_rag": Information has been retrieved from the user's documents. Integrate this information naturally into your response to answer the user's question.
- "graph": A visualization has been created and will be displayed on screen. ALWAYS use the "one_arm_up_talking" animation when informing the user that a graph is now visible on screen - this animation makes it appear as if you're pointing directly to the visualization. Highlight key insights from the graph and direct their attention to important aspects of the visualization.

STATUS UPDATES:
Always set a clear status before calling any function to keep the user informed of what you're doing. The status should be concise but descriptive, such as "Searching for academic papers on climate change" or "Creating a bar graph of population statistics".

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



