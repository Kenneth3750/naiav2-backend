import os

from dotenv import load_dotenv
from openai import OpenAI
from serpapi import GoogleSearch
from ..status.services import set_status
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import tempfile

load_dotenv()

openai_api_key = os.getenv("open_ai")

client = OpenAI(
    api_key= openai_api_key
)

def get_references(query="", num_results=5, language="en"):
    """
    This function searches for academic papers using Google Scholar API.
    It retrieves the title, authors, snippet, and link of the papers.
    """
    load_dotenv()
    api_key = os.getenv("SERPAPI_KEY")

    if not api_key:
        print("Error: SERPAPI_KEY not found in .env file")
        return

    # Configure search parameters
    params = {
        "engine": "google_scholar",
        "q": query,
        "api_key": api_key,
        "num": num_results,
        "hl": language,
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        search_result = {"query": query, "results": []}

        print(f"\n=== Search Results for: {query} ===\n")
        for i, result in enumerate(results.get("organic_results"), 1):
            research_information = {
                "result_number": i,
                "title": result.get("title", "N/A"),
                "authors": [
                    author.get("name", "N/A")
                    for author in result.get("publication_info", {})
                    .get("authors", [])
                ],
                "snippet": result.get("snippet", "N/A"),
                "link": result.get("link", "N/A"),
            }
            search_result["results"].append(research_information)
            print(f"Result {i}:")
        return search_result
    except (ValueError, TypeError, KeyError) as e:
        print(f"Error during search: {str(e)}")
        return {"error": str(e),
                "action": "Do not put references on the text"}
    except ConnectionError as e:
        print(f"Connection error during search: {str(e)}")
        error_msg = f"Connection error during search: {str(e)}"
        return {"error": str(e),
        "action": "Do not put references on the text"}


def scholar_search(query="", query_2 = "", num_results=3, status="", user_id=0, language1="", language2="en"):
    """
    This function searches for academic papers using Google Scholar API.
    It retrieves the title, authors, snippet, and link of the papers.
    """
    set_status(user_id, status, 1)
    load_dotenv()
    api_key = os.getenv("SERPAPI_KEY")

    if not api_key:
        print("Error: SERPAPI_KEY not found in .env file")
        return

    # Configure search parameters
    params_1 = {
        "engine": "google_scholar",
        "q": query,
        "api_key": api_key,
        "num": num_results,
        "hl": language1,
    }
    
    params_2 = {
        "engine": "google_scholar",
        "q": query_2,
        "api_key": api_key, 
        "num": num_results,
        "hl": language2,
    }

    try:
        # Combined search result object
        combined_results = {"query": f"{query} & {query_2}", "results": []}
        
        # First query
        if query:
            search1 = GoogleSearch(params_1)
            results1 = search1.get_dict()
            
            print(f"\n=== Search Results for: {query} ===\n")
            for i, result in enumerate(results1.get("organic_results", []), 1):
                research_information = {
                    "result_number": i,
                    "query_source": "query_1",
                    "title": result.get("title", "N/A"),
                    "authors": [
                        author.get("name", "N/A")
                        for author in result.get("publication_info", {})
                        .get("authors", [])
                    ],
                    "snippet": result.get("snippet", "N/A"),
                    "link": result.get("link", "N/A"),
                }
                combined_results["results"].append(research_information)
                print(f"Result {i} from query 1")
                print(f"Title: {result.get('title', 'N/A')}")
        
        if query_2:
            search2 = GoogleSearch(params_2)
            results2 = search2.get_dict()
            
            print(f"\n=== Search Results for: {query_2} ===\n")
            offset = len(combined_results["results"])
            for i, result in enumerate(results2.get("organic_results", []), 1):
                research_information = {
                    "result_number": i + offset,
                    "query_source": "query_2",
                    "title": result.get("title", "N/A"),
                    "authors": [
                        author.get("name", "N/A")
                        for author in result.get("publication_info", {})
                        .get("authors", [])
                    ],
                    "snippet": result.get("snippet", "N/A"),
                    "link": result.get("link", "N/A"),
                }
                combined_results["results"].append(research_information)
                print(f"Result {i} from query 2")
                print(f"Title: {result.get('title', 'N/A')}")
                
        return convert_to_html(combined_results)

    except (ValueError, TypeError, KeyError) as e:
        print(f"Error during search: {str(e)}")
        raise ValueError(f"Error during search: {str(e)}") from e
    except ConnectionError as e:
        print(f"Connection error during search: {str(e)}")
        error_msg = f"Connection error during search: {str(e)}"
        raise ConnectionError(error_msg) from e


def convert_to_html(search_result):
    """Convert search results to HTML format"""
    html = f"""
    <div class="search-results">
        <h2>Search Results for: {search_result['query']}</h2>
        <div class="results-container">
    """

    for result in search_result["results"]:
        html += f"""
            <div class="result-card">
                <h3>Result {result['result_number']}</h3>
                <h4 class="title">{result['title']}</h4>
                <p class="authors"><strong>Authors:</strong> {', '.join(result['authors'])}</p>
                <p class="snippet">{result['snippet']}</p>
                <a href="{result['link']}" target="_blank" class="read-more">Read More</a>
            </div>
        """

    html += """
        </div>
    </div>
    <style>
        .search-results {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .result-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .title {
            color: #1a0dab;
            margin: 10px 0;
        }
        .authors {
            color: #006621;
        }
        .read-more {
            display: inline-block;
            color: white;
            background: #1a73e8;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 10px;
        }
    </style>
    """
    return {"display": html}


def write_document(query, context="", user_id=0, status="", query_for_references=None, language_for_references="en", num_results=5):
    """
    This feature is responsible for generating specific documents 
    based on the topic the user is consulting.
    """
    load_dotenv()
    set_status(user_id, status, 1)
    if query:
        references = get_references(query_for_references, num_results, language_for_references)

    client = OpenAI(api_key=os.getenv("open_ai"))
    try:

        messages = [
            {
                "role": "system",
                "content": """You are an expert academic writer specializing in creating high-quality research documents for Universidad del Norte in Barranquilla, Colombia. Your task is to generate comprehensive, well-structured academic content in markdown format that meets university standards.

IMPORTANT REFERENCE GUIDELINES:
- You must ONLY use references explicitly provided in the context. Never invent or fabricate citations.
- If no references are provided, acknowledge this limitation and create content based on general knowledge only.
- Format all citations consistently using APA 7th edition style.
- Include a properly formatted reference list at the end of the document.

DOCUMENT STRUCTURE:
1. Title: Create a descriptive, academic title relevant to the topic
2. Abstract: A concise summary (100-150 words) of the document's purpose and findings
3. Introduction: Present the topic, its relevance, and outline the document's structure
4. Main Body: Organized into logical sections with clear headings and subheadings
   - Use H2 (##) for main sections and H3 (###) for subsections
   - Support claims with evidence from provided references
   - Include relevant data, examples, or case studies when appropriate
   - Define specialized terminology when first introduced
5. Discussion/Analysis: Interpret findings, address implications, and consider limitations
6. Conclusion: Summarize key points and suggest areas for further research
7. References: List all cited works in APA format, alphabetically by author

WRITING STYLE:
- Maintain formal, objective academic tone throughout
- Use precise, discipline-appropriate terminology
- Write in third person (avoid "I", "we", "you")
- Use active voice where possible for clarity
- Ensure logical flow between paragraphs and sections
- Balance depth with accessibility for university-level readers
- Avoid unsupported claims, exaggerations, or speculation

FORMATTING:
- Use proper markdown syntax for all elements
- Use bullet points or numbered lists for series of related items
- Format tables using markdown table syntax where appropriate
- Describe any necessary figures or diagrams in markdown
- Use emphasis (italic, bold) sparingly and only when needed for clarity
- Keep paragraphs focused and reasonably sized (4-6 sentences typical)

Your document should demonstrate scholarly rigor while remaining accessible to academic readers. Focus on creating content that would be valuable for research, teaching, or academic reference at Universidad del Norte.""",
            }
        ]

        if context or references:
            messages.append(
                {"role": "user", "content": f"""Use these references and information as the basis for your document: {context}\n
                Use this real referencess: {references}\n
                If the content of the references is a json with an error as a key, do not use it as a reference."""}
            )

        messages.append(
            {"role": "user", "content": f"Generate a well-structured academic document in markdown format based on this topic: {query}\n Do not create references or citations if the were not provided by me before.\n\n\n"}
        )

        openai_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )

        messages.append(
            {"role": "assistant", "content": openai_response.choices[0].message.content}
        )
        return {"pdf": openai_response.choices[0].message.content}
    except Exception as e:
        print(f"Error generating document: {str(e)}")
        return {"error": str(e)}

# Rag function 

def save_user_document_for_rag(pdf_files: List[bytes], user_id:int):
    """
    this function is to save the user pdf file into their own vector database
    pdf_file: list of file in byte format (max 5)
    user_id: 
    """
    if len(pdf_files) > 5 :
        raise ValueError("Maximo se permiten 5 archivos PDF.")
    
    all_documents = []

    for file_bytes in pdf_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file_bytes)
            tmp_file_path = tmp_file.name
        
        loader = PyPDFLoader(tmp_file_path)
        docs = loader.load()
        all_documents.extend(docs)

    if not all_documents:
        raise ValueError("No se pudieron extraer textos de los PDFs-")
    
    # Limpieza del archivo temporal
    os.unlink(tmp_file_path)
    
    # split
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=100,
        chunk_overlap=50
    )

    chunks = text_splitter.split_documents(all_documents)


    # store
    persist_dir = f"./chromadb_user/{user_id}"
    os.makedirs(persist_dir, exist_ok=True)

    embeddings = OpenAIEmbeddings(api_key=openai_api_key,
                                  model="text-embedding-3-large")

    vector_store = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    vector_store.add_documents(chunks)

    vector_store.persist()

    return f"Documents from user {user_id} were correctly saved"




def answer_from_user_rag(user_id: int, pregunta: str, k: int = 3, status:str = "") -> dict:
    """
    Consulta la información almacenada en el vectorstore del usuario y genera una respuesta.
    """
    try:
        set_status(user_id, status, 1)
        persist_dir = f"./chromadb_user/{user_id}"

        if not os.path.exists(persist_dir):
            raise FileNotFoundError(f"No existe información para el usuario: {user_id}")

        embeddings = OpenAIEmbeddings(api_key=openai_api_key,
                                    model="text-embedding-3-large")
        
        vector_store = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

        resultados = vector_store.similarity_search(pregunta, k=k)

        if not resultados:
            return "No se encontraron documentos relevantes para tu pregunta."
        
        rag_results = []
        for i, doc in enumerate(resultados, 1):
            rag_results.append(f"Documento {i}: {doc.page_content}")

        result_text = "\n\n".join(rag_results)
        print(f"Resultados de RAG: {result_text}")
        return {"resolved_rag": result_text}
    except Exception as e:
        print(f"Error al recuperar documentos: {str(e)}")
        return {"error": str(e)}

def create_graph(user_query: str, information_for_graph: str, user_id: int, status: str = "", internet_is_required: bool = False) -> dict:
    """
    This function creates a graph based on the user query and the information provided,
    using two specialized agents: a research agent (GPT-4o-search-preview) and a 
    visualization agent (GPT-4.1).
    """
    set_status(user_id, status, 1)
    client = OpenAI(api_key=openai_api_key)
    try:
        if internet_is_required:            
            research_messages = [
                {
                    "role": "system",
                    "content": """You are a specialized data research agent with internet access. Your job is to find and structure numerical data for visualization.

When given a search query:
1. Search for the most recent, accurate data from authoritative sources (government agencies, international organizations, academic institutions)
2. Focus on gathering complete datasets rather than isolated statistics
3. Structure the data in a clean, organized format that's ready for visualization
4. Include all necessary context (date ranges, measurement units, categories)
5. Provide complete source information for each data point or dataset
6. Format your response as a structured dataset with clear labels, values, and attribution

Return ONLY the structured data - no explanations, analysis, or background information.
Example format:
{
  "title": "Colombia GDP Growth 2015-2025",
  "data": [
    {"year": 2015, "value": 3.0},
    {"year": 2016, "value": 2.1},
    ...
  ],
  "unit": "Percent annual growth",
  "sources": [
    "World Bank Economic Indicators Database (2023)",
    "IMF World Economic Outlook (April 2024)"
  ]
}"""
                },
                {
                    "role": "user",
                    "content": f"Find and structure data for the following visualization: {information_for_graph}"
                }
            ]
            
            research_response = client.chat.completions.create(
                model="gpt-4o-search-preview",
                messages=research_messages
            )
            
            data_content = research_response.choices[0].message.content
            print(f"Research agent response: {data_content}")
            
            information_for_graph = data_content

        # Agent 2: Visualization Agent
        visualization_messages = [
            {
                "role": "system",
                "content": """You are a world-class data visualization expert specializing in creating beautiful, interactive HTML visualizations.

Create a self-contained HTML visualization based on the user's request. The visualization will be embedded directly into an existing web application, so provide ONLY the HTML code.

TECHNICAL REQUIREMENTS:
1. Use modern visualization libraries via CDN (Chart.js, D3.js, Plotly, ApexCharts, etc.)
2. Include ALL JavaScript and CSS inline within a single HTML file
3. Ensure the visualization is responsive (adapts to different screen sizes)
4. Set container width to 100% with appropriate min/max constraints
5. Include error handling for data processing and rendering
6. Use proper semantic HTML structure

AESTHETIC REQUIREMENTS:
1. Use a cohesive, professional color palette (with sufficient contrast)
2. Include clear, properly formatted titles, labels, and legends
3. Use appropriate font sizes and spacing for readability
4. Apply subtle animations and transitions where appropriate
5. Implement clean, minimal design that focuses on the data

INTERACTIVITY REQUIREMENTS:
1. Add hover tooltips showing precise data values
2. Include zoom/pan capabilities for complex visualizations
3. Implement filters or toggles for multi-series data
4. Add click interactions to reveal additional details
5. Ensure all interactive elements have proper visual feedback

ATTRIBUTION REQUIREMENTS:
1. Include a dedicated 'Data Sources' section at the bottom
2. Format each citation consistently with source name, year, and organization
3. Make attribution text readable but visually subordinate to the main visualization

COMMON GRAPH TYPES & BEST PRACTICES:
- Line charts: Use for time series, include clear markers at data points
- Bar charts: Maintain consistent spacing, use horizontal bars for long labels
- Pie/donut charts: Limit to 7-8 slices maximum, order from largest to smallest
- Scatter plots: Include regression lines when appropriate
- Maps: Use appropriate projections, include clear legends
- Timelines: Create clear intervals, highlight key events

Note: The code you produce will be directly embedded in a production application. Test mentally for errors and edge cases before finalizing your code.

Return ONLY the HTML code with embedded JavaScript and CSS."""
            },
            {
                "role": "user",
                "content": f"""Create a graph based on this request: {user_query}

Using this data: {information_for_graph}"""
            }
        ]
        
        visualization_response = client.chat.completions.create(
            model="gpt-4.1",
            messages=visualization_messages
        )
        
        response_content = visualization_response.choices[0].message.content
        
        # Clean any markdown code block markers from the response
        if response_content.startswith("```html"):
            response_content = response_content.replace("```html", "", 1)
        elif response_content.startswith("```"):
            response_content = response_content.replace("```", "", 1)
        
        # Always check for and remove trailing code block markers
        if response_content.endswith("```"):
            response_content = response_content[:-3]
        
        # Trim any extra whitespace
        response_content = response_content.strip()
        
        # Write the cleaned HTML to file (for debugging/logging)
        with open(f"graph_{user_id}.html", "w", encoding="utf-8") as f:
            f.write(response_content)
            
        return {"graph": response_content}
    except Exception as e:
        print(f"Error generating graph: {str(e)}")
        return {"error": str(e)}

def internet_search(consulta: str):


    """
    Esta función realiza la búsqueda por internet. retorna 

    Args_
    consulta: es la query para buscar en internet

    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-search-preview",
            web_search_options={},
            messages=[
        {
            "role": "user",
            "content": f"Vas a buscar en internet la siguiente información {consulta}, la respuesta la darás en un json de la siguiente manera la primera key es 'html' y la segunda key es 'info'. el valor de 'info' quiero que sea completo y denso. y el value de html quiero que sea sobre las referencias donde encontraste la información.",
        }
    ], )

        respuesta_json = completion.choices[0].message.content
        return respuesta_json


    except Exception as e:
        print(f"Error al buscar en internet {str(e)}")
        return {"error": str(e)}
