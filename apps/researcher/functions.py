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
import json
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
                <a href="{result['link']}" class="read-more" target="_blank">Read More</a>
            </div>
        """

    html += """
        </div>
    </div>
    <style>
        .search-results {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
            color: #0B3954;
            margin: 10px 0;
        }
        .authors {
            color: #006621;
        }
        .read-more {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: #0B3954;
            background-color: rgba(11, 57, 84, 0.1);
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 6px;
            border: 1px solid #0B3954;
            margin-top: 12px;
            font-family: inherit;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .read-more:hover {
            background-color: rgba(11, 57, 84, 0.2);
        }
        .read-more:active {
            background-color: rgba(11, 57, 84, 0.3);
        }
        .read-more::before {
            content: '';
            display: inline-block;
            width: 18px;
            height: 18px;
            margin-right: 8px;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%230B3954' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/%3E%3Cpolyline points='7 10 12 15 17 10'/%3E%3Cline x1='12' y1='15' x2='12' y2='3'/%3E%3C/svg%3E");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
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
    query la información almacenada en el vectorstore del usuario y genera una respuesta.
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

            
        visualization_messages = [
            {
                "role": "system",
                "content": """You are a data visualization expert specializing in creating clear, professional charts for academic publications.

Create a clean, publication-ready HTML visualization that can be easily converted to static PNG/JPG images for academic articles. The visualization should focus on clarity and academic style rather than interactivity.

TECHNICAL REQUIREMENTS:
1. Use D3.js or Chart.js via CDN (preferred libraries for static visualization)
2. Include ALL JavaScript and CSS inline within a single HTML file
3. Set a FIXED WIDTH of 600px and appropriate height (typically 400-450px) for the chart
4. Set both HTML and BODY elements to have no margin and padding
5. The chart container should have width:600px and appropriate height with no excess margins
6. Avoid complex animations or transitions that won't translate to static images
7. Use a white background to ensure compatibility with print publications
8. Ensure all text is readable when converted to an image (appropriate font sizes)


ACADEMIC STYLE REQUIREMENTS:
1. Use a simple, professional color palette appropriate for academic journals
2. Include clear, properly formatted titles, axis labels, and legends
3. Use serif fonts for better readability in print (Times New Roman or similar)
4. Add appropriate grid lines where they enhance readability
5. Format numbers with appropriate precision and thousand separators
6. Include error bars or confidence intervals where applicable

DATA PRESENTATION BEST PRACTICES:
1. Start numeric axes at zero when appropriate for accurate visual comparison
2. Use consistent scales across related charts
3. Clearly indicate units of measurement on axes
4. Limit the number of data series to prevent visual clutter
5. Order categorical data in a meaningful way (e.g., chronological, ascending/descending values)
6. Use appropriate chart types for the data relationships being shown

ATTRIBUTION REQUIREMENTS:
1. Include a simple, clean caption below the visualization
2. Format citations according to academic standards (APA, MLA, etc.)
3. Include all data sources with complete citation information


Return ONLY the HTML code with embedded JavaScript and CSS. The code should render a visualization that looks good as a static image without interactive elements."""
            },
            {
                "role": "user",
                "content": f"""Create a publication-ready graph for an academic article based on this request: {user_query}

Using this data: {information_for_graph}

Requirements:
1. The graph MUST have a fixed width of exactly 600px (this is critical for our frontend)
2. The visualization should be simple, clear, and suitable for converting to a static image format (PNG/JPG)
3. The graph should have appropriate proportions (not look squished or stretched)
4. Do not add any comments or explanations in the HTML code
5. The graph should be simple and clear, suitable for academic publication"""
            }
        ]
        
        visualization_response = client.chat.completions.create(
            model="gpt-4.1-mini",
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
    
def factual_web_query(query: str, status: str = "", user_id: int = 0) -> dict:
    """
    This function searches the internet for information using the SerpAPI.

    Args_
        query (str): The search query.

    """
    try:
        api_key = os.getenv("SERPAPI_KEY")
        if not api_key:
            raise ValueError("SERPAPI_KEY not found in .env file")
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "outpuyt": "json",
        }
        set_status(user_id, status, 1)
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])
        
        html_output = """
        <div class="naia-search-container">
            <h2 class="search-title">Resultados de búsqueda</h2>
            <div class="search-query-box">
              <span class="search-icon">🔍</span>
              <span class="query-text">{}</span>
            </div>
            <div class="results-container">
        """.format(query)
        
        for i, result in enumerate(organic_results[:10], 1):
            title = result.get("title", "No Title Available")
            link = result.get("link", "#")
            snippet = result.get("snippet", "No description available.")
            
            html_output += f"""
            <div class="result-card">
                <div class="result-number">{i}</div>
                <div class="result-content">
                  <a href="{link}" class="result-title" target="_blank">{title}</a>
                  <div class="result-url">{link}</div>
                  <p class="result-snippet">{snippet}</p>
                </div>
            </div>
            """
        
        html_output += """
            </div>
        </div>
        <style>
            .naia-search-container {
              font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
              width: 100%;
              max-width: 100%;
              margin: 0;
              padding: 12px;
              background: rgba(255, 255, 255, 0.7);
              border-radius: 10px;
              box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
            }
            .search-title {
              color: #0c2461; /* blue-950 equivalent */
              font-size: 20px;
              margin-bottom: 12px;
              text-align: center;
              font-weight: 600;
            }
            .search-query-box {
              background: rgba(240, 249, 255, 0.8); /* sky-50 equivalent */
              padding: 10px 12px;
              border-radius: 8px;
              margin-bottom: 16px;
              display: flex;
              align-items: center;
              border-left: 3px solid #0284c7; /* sky-600 equivalent */
            }
            .search-icon {
              font-size: 16px;
              margin-right: 10px;
            }
            .query-text {
              font-size: 14px;
              color: #333;
              font-weight: 500;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            }
            .results-container {
              display: flex;
              flex-direction: column;
              gap: 12px;
            }
            .result-card {
              display: flex;
              background: white;
              border-radius: 8px;
              padding: 12px;
              box-shadow: 0 2px 8px rgba(0,0,0,0.03);
              transition: transform 0.2s, box-shadow 0.2s;
              position: relative;
              overflow: hidden;
              border-left: 2px solid transparent;
            }
            .result-card:hover {
              transform: translateY(-2px);
              box-shadow: 0 4px 12px rgba(0,0,0,0.08);
              border-left-color: #0284c7; /* sky-600 equivalent */
            }
            .result-number {
              background: #0c2461; /* blue-950 equivalent */
              color: white;
              width: 24px;
              height: 24px;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              font-weight: bold;
              margin-right: 12px;
              flex-shrink: 0;
              font-size: 12px;
            }
            .result-content {
              flex-grow: 1;
              min-width: 0; /* Helps with text truncation */
            }
            .result-title {
              font-size: 15px;
              color: #0c2461; /* blue-950 equivalent */
              text-decoration: none;
              font-weight: 600;
              margin-bottom: 4px;
              display: block;
              line-height: 1.3;
              overflow: hidden;
              text-overflow: ellipsis;
              display: -webkit-box;
              -webkit-line-clamp: 2;
              -webkit-box-orient: vertical;
            }
            .result-title:hover {
              text-decoration: underline;
            }
            .result-url {
              font-size: 12px;
              color: #0284c7; /* sky-600 equivalent */
              margin-bottom: 6px;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
              max-width: 100%;
            }
            .result-snippet {
              font-size: 13px;
              color: #555;
              line-height: 1.4;
              margin: 0;
              overflow: hidden;
              text-overflow: ellipsis;
              display: -webkit-box;
              -webkit-line-clamp: 3;
              -webkit-box-orient: vertical;
            }
        </style>
        """
        with open(f"search_results_{user_id}.html", "w", encoding="utf-8") as f:
            f.write(html_output)
        
        return {"search_results": html_output}
    except Exception as e:
        print(f"Error during search: {str(e)}")
        return {"error": str(e)}


def deep_content_analysis_for_specific_information(query: str, url: str = None, user_id: int = 0, status: str = ""):
    """
    Performs an in-depth search and information retrieval on specific topics.
    
    Args:
        query (str): The required search query
        url (str, optional): Optional URL to focus the search. Defaults to None.
        user_id (int, optional): User ID for status updates. Defaults to 0.
        status (str, optional): Status message. Defaults to "".
        
    Returns:
        dict: A dictionary with search results or error information
    """
    try:
        if user_id:
            set_status(user_id, status or "Performing deep content analysis...", 1)
        
        load_dotenv()
        

        search_options = {}
        if url:
            search_options["url"] = url
            print(f"Using URL for focused search: {url}")
        else:
            print("Performing general search without URL")
        
        if url:
            system_content = """You are a specialized search agent with advanced information retrieval capabilities.
Your responsibilities:
1. Focus your search primarily on the provided URL
2. Extract key facts, figures, and insights from this source and related materials
3. Organize the information in a coherent, well-structured format
4. Provide proper attribution to all sources
5. Return ONLY a JSON response with two keys: 'info' (containing comprehensive results) and 'html' (containing reference information)

Present information that is factual, balanced, and thoroughly researched."""
        else:
            system_content = """You are a specialized search agent with advanced information retrieval capabilities.
Your responsibilities:
1. Search for authoritative, detailed information on the query topic
2. Extract key facts, figures, and insights from multiple reliable sources
3. Organize the information in a coherent, well-structured format
4. Provide proper attribution to all sources
5. Return ONLY a JSON response with two keys: 'info' (containing comprehensive results) and 'html' (containing reference information)

Present information that is factual, balanced, and thoroughly researched."""

        # Make API call
        completion = client.chat.completions.create(
            model="gpt-4o-search-preview",
            web_search_options=search_options,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": f"Search for: {query}. Return your response as a JSON with two keys: 'html' and 'info'."}
            ]
        )
        
        # Extract and parse response
        response_content = completion.choices[0].message.content
        
        # Attempt to parse as JSON to validate
        try:
            import json
            parsed_json = json.loads(response_content)
            return response_content
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON response", "raw_response": response_content})
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error during deep content analysis: {str(e)}\n{error_details}")
        return {"error": str(e), "details": error_details}
