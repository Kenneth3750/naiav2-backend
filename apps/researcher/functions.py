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
import smtplib
import os
from email.mime.text import MIMEText

load_dotenv()

DEFAULT_FROM_EMAIL=os.getenv("DEFAULT_FROM_EMAIL")
EMAIL_HOST_PASSWORD=os.getenv("EMAIL_HOST_PASSWORD")

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
            color: #ffffff;
            background-color: #1f2937; /* Gris 800 de Tailwind */
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 6px;
            border: none;
            margin-top: 12px;
            font-family: inherit;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .read-more:hover {
            background-color: #111827;
        }
        .read-more:active {
            background-color: #374151
        }
        
    </style>
    """
    return {"display": html}


def write_document(query, context="", user_id=0, status="", query_for_references=None, language_for_references="en", num_results=5, document_type="academic", use_internet=False, use_rag=False, specific_documents=None):
    """
    This feature is responsible for generating comprehensive documents 
    based on the topic the user is consulting, with the ability to leverage multiple
    information sources including internet search and user's own documents.
    """
    load_dotenv()
    set_status(user_id, status, 1)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("open_ai"))
    
    try:
        full_context = []
        
        # 1. Add explicitly provided context
        if context:
            full_context.append(f"### CONTEXT PROVIDED:\n{context}")
        
        # 2. Search for academic references if requested
        academic_refs = ""
        if query_for_references and query_for_references.lower() != "none":
            try:
                references = get_references(query_for_references, num_results, language_for_references)
                if references and "error" not in references:
                    academic_refs = f"### ACADEMIC REFERENCES:\n{json.dumps(references, indent=2)}"
                    full_context.append(academic_refs)
            except Exception as e:
                print(f"Error searching for academic references: {str(e)}")
        
        # 3. Search user documents via RAG if requested
        if use_rag:
            try:
                rag_results = answer_from_user_rag(
                    user_id=user_id,
                    pregunta=f"Find relevant information about: {query}",
                    k=5,
                    status=f"Searching your documents for information about {query}"
                )
                if rag_results and "error" not in rag_results and "resolved_rag" in rag_results:
                    rag_content = f"### USER DOCUMENT CONTENT:\n{rag_results['resolved_rag']}"
                    full_context.append(rag_content)
            except Exception as e:
                print(f"Error querying RAG: {str(e)}")
        set_status(user_id, status, 1)
        # 4. Perform internet search if requested
        if use_internet:
            try:
                # Use GPT-4o-search-preview for comprehensive research
                research_messages = [
                    {
                        "role": "system",
                        "content": """You are a specialized research agent with internet access. Your task is to gather comprehensive, 
                        accurate, and up-to-date information for creating an authoritative document. Follow these guidelines:

                        1. Search for diverse, high-quality sources related to the topic
                        2. Gather detailed information including key concepts, latest developments, statistics, expert opinions, and examples
                        3. Focus on authoritative sources: academic journals, reputable news sites, official documentation, expert analyses
                        4. Note any controversies, debates, or alternative viewpoints on the topic
                        5. Include recent developments and cutting-edge information
                        6. Organize the information coherently by subtopics
                        7. Maintain scholarly neutrality while gathering comprehensive information
                        8. Include proper attribution to sources
                        
                        Provide a thorough research report that would give a writer all the necessary information to create 
                        an authoritative document on the topic. Use clear section headings to organize information by subtopics."""
                    },
                    {
                        "role": "user",
                        "content": f"Research comprehensive information for a document about: {query}"
                    }
                ]
                
                research_response = client.chat.completions.create(
                    model="gpt-4o-search-preview",
                    messages=research_messages
                )
                
                web_research = f"### WEB RESEARCH RESULTS:\n{research_response.choices[0].message.content}"
                full_context.append(web_research)
                print("Web search completed")
            except Exception as e:
                print(f"Error in web search: {str(e)}")
        
        combined_context = "\n\n".join(full_context)
        
        document_type_guide = {
            "academic": "a formal academic document with educational focus and conceptual rigor",
            "report": "a clear, direct business or technical report focused on data and analysis",
            "essay": "a reflective essay with coherent idea development and argumentation",
            "brief": "a concise, brief document presenting only essential information",
            "creative": "a creative text with narrative or expressive style",
            "notes": "organized study notes to facilitate learning and reference",
            "presentation": "content for a visual presentation with clear and concise points"
        }
        
        type_description = document_type_guide.get(document_type.lower(), "a well-structured document")
        
        info_sources = []
        if academic_refs:
            info_sources.append("academic references")
        if use_rag and any("USER DOCUMENT CONTENT" in ctx for ctx in full_context):
            info_sources.append("your personal documents")
        if use_internet and any("WEB RESEARCH RESULTS" in ctx for ctx in full_context):
            info_sources.append("current internet sources")
        
        info_sources_text = ", ".join(info_sources) if info_sources else "available information"
        
        messages = [
            {
                "role": "system",
                "content": f"""You are an expert writer specializing in creating {type_description}. 
                Your task is to generate high-quality content on the requested topic.
                
                IMPORTANT FORMATTING INSTRUCTIONS:
                1. DO use Markdown for document structure:
                - Use # for main titles (H1)
                - Use ## for section headings (H2)
                - Use ### for subheadings (H3)
                2. DO NOT use Markdown inside paragraphs:
                - DO NOT use asterisks for bold or italic text within paragraphs
                - Instead of **bold** text, use ALL CAPS or "quotation marks" for emphasis
                - Instead of *italic* text, use 'single quotes' or underscores_around_words
                3. For lists:
                - Use proper Markdown numbered lists (1., 2., etc.)
                - Use proper Markdown bullet lists (-, *, etc.)
                4. Use blank lines between paragraphs and sections
                5. For tables, use proper Markdown table format
                
                CONTENT GUIDELINES:
                - Be creative and flexible in structure according to document type and topic
                - Organize information logically and coherently
                - Adapt tone and style to the document's purpose
                - Include relevant and up-to-date information
                - Properly cite sources when appropriate
                
                You have creative freedom to structure the document in the most effective way for its purpose."""
            },
            {
                "role": "user",
                "content": f"""Based on {info_sources_text}, generate {type_description} on the following topic: {query}

    Here is all the available information for creating this document:

    {combined_context}

    Make sure to:
    1. Create a well-structured and organized document
    2. Incorporate information from all provided sources
    3. Use proper Markdown for headings, but avoid Markdown formatting within paragraphs
    4. Ensure accuracy and depth in the content
    """
            }
        ]

        openai_response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages
        )

        print("Document successfully generated")
        return {"pdf": openai_response.choices[0].message.content}
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating document: {str(e)}\n{error_details}")
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
                "content": """You are a data visualization expert specializing in creating STATIC charts for academic publications. Your visualizations must be print-ready and should work perfectly as static images without ANY interactive elements.

⚠️ CRITICAL: STATIC IMAGE FORMAT REQUIREMENTS ⚠️
This visualization will be converted to a STATIC IMAGE (PNG/JPG) for use in academic papers. Therefore:
1. DO NOT include ANY interactive elements (tooltips, hover effects, zoom, etc.)
2. DO NOT include ANY animations or transitions
3. DO NOT rely on mouse interactions of any kind
4. ALL information must be visible in the static view
5. Charts must be fully self-contained and understandable without interaction

⚠️ ACADEMIC PAPER FORMATTING STANDARDS ⚠️
Follow these strict formatting standards for academic publications:
1. TITLE FORMAT:
   - Include a BOLD, clear title at the TOP of the visualization
   - Title font size: 16-18px
   - Title font weight: bold
   - Title alignment: center
   - Title must be descriptive and concise
   - Title should summarize what the chart shows

2. LEGEND FORMAT:
   - Position legend preferably inside the chart area if space allows
   - Clear, high-contrast colors with distinctive shapes/patterns
   - Ensure legend items are fully labeled with no truncation
   - Legend font size: 12-14px

3. CAPTION/DESCRIPTION FORMAT:
   - Place explanatory text ONLY at the BOTTOM of the visualization
   - Caption font size: 12px
   - Include source attribution in the caption when available
   - Keep captions concise but informative
   - Caption should explain key insights or methodology if needed

⚠️ DIMENSION AND SPACE UTILIZATION REQUIREMENTS ⚠️:
1. Set the outer container's FIXED WIDTH to EXACTLY 600px
2. MAXIMIZE THE USAGE OF AVAILABLE HORIZONTAL SPACE:
   - Chart area should occupy at least 85% of the total width (510px or more)
   - Minimize margins on left and right sides (15-30px maximum)
   - Avoid excessive white space on the sides
3. For height, follow these guidelines:
   - Standard charts: 500-550px
   - Simple charts (few data points): 450-500px
   - Complex charts (many data points): 550-650px
4. For charts with many data points:
   - PRESERVE THE 600px WIDTH
   - Make the container vertically scrollable if needed using overflow-y: auto
   - Set a max-height for the scrollable area (e.g., 650px)

⚠️ NUMBER FORMATTING AND SCALE OPTIMIZATION ⚠️:
1. ALWAYS use appropriate number formatting based on the data range:
   - For very small numbers (e.g., 0.0000467), use scientific notation (4.67 × 10⁻⁵)
   - For very large numbers (e.g., 5000000), use abbreviated formats (5M)
   - For currencies, use appropriate symbols and thousand separators
   - For floating-point numbers, use 2-3 decimal places, e.g., 3.14 or 3.141
   - For percentages, use 1-2 decimal places, e.g., 45.6% or 45.67%
2. Implement the most readable scale for the data:
   - For values with wide ranges, consider logarithmic scales
   - Format decimal precision appropriately to the data type
3. Include clear scale indicators directly on axes
4. Adjust tick density for optimal readability (4-7 ticks per axis)

⚠️ LABEL AND AXIS POSITIONING ⚠️:
1. ALL text elements must be fully visible in the static view
2. Position axis titles for maximum clarity:
   - X-axis title: centered below the axis
   - Y-axis title: vertical, centered to the left of the axis
3. Units of measurement should be clearly indicated on or next to axis labels
4. For dual-axis charts, clearly differentiate both scales
5. Position all text to avoid any cutoff or overlap
6. Use rotated labels for x-axis if needed to preserve space

VISUAL STYLE FOR ACADEMIC PUBLICATIONS:
1. Use a clean, professional color palette suitable for both color and grayscale printing
2. Apply high contrast colors for main data series
3. Use distinct patterns for bar/pie charts that will remain distinguishable in grayscale
4. Apply subtle gridlines that enhance readability without overwhelming the data
5. Use serif fonts (Times New Roman or similar) for academic consistency
6. Maintain consistent font sizes throughout (axis: 12px, labels: 12-14px, title: 16-18px)
7. Apply moderate line weights for data series (1.5-2px)

TECHNICAL IMPLEMENTATION:
1. Use Chart.js via CDN (preferred for static, professional visualizations)
2. Include ALL JavaScript and CSS inline within a single HTML file
3. Set explicit width and height in both HTML/CSS and chart configuration
4. Use maintainAspectRatio: false in Chart.js options
5. Configure Chart.js with plugins.tooltip.enabled: false to disable tooltips
6. Disable all animations: animation: { duration: 0 }
7. Use optimal minimal padding: layout: { padding: { left: 15, right: 15, top: 25, bottom: 40 }}

DATA PRESENTATION BEST PRACTICES:
1. Start numeric axes at zero when appropriate for accurate comparison
2. Clearly indicate units of measurement directly on or next to axes
3. Order categorical data logically (chronological, ascending/descending)
4. Select the simplest appropriate chart type for the data
5. If you use multiple symbols/colors, ensure they are clearly defined in the legend above the chart. Never put the legend inside the chart area or below the chart.
6. Avoid excessive use of colors or patterns that may distract from the data
7. Use clear, concise labels for all axes and data series
8. Avoid cluttering the chart with unnecessary elements (e.g., excessive gridlines, background images)
9. Keep the charts desings fresh and modern, avoiding outdated styles or templates

FINAL QUALITY CHECKS:
1. Verify the visualization is complete and understandable without any interaction
2. Confirm chart exactly respects the 600px width constraint
3. Ensure all text elements are fully visible and properly positioned
4. Verify chart area utilizes at least 85% of available width
5. Confirm title is bold, centered, and at the top of the visualization
6. Verify any explanatory text appears ONLY at the bottom

Return ONLY clean, production-ready HTML code with embedded JavaScript and CSS."""
            },
            {
                "role": "user",
                "content": f"""Create a publication-ready STATIC chart for an academic paper based on this request: {user_query}

Using this data: {information_for_graph}

STRICT REQUIREMENTS FOR STATIC ACADEMIC PUBLICATION:
1. The chart MUST have a fixed width of EXACTLY 600px
2. Create a BOLD, CENTERED TITLE at the TOP of the visualization
3. MAXIMIZE chart area (use at least 85% of the available width)
4. ALL information must be visible in the static view - NO tooltips or hover effects
5. NO animations or interactive elements of any kind
6. Format numbers appropriately (scientific notation for very small values, abbreviated formats for large values)
7. Position any explanatory text or captions ONLY at the BOTTOM
8. Use publication-appropriate styling (clean, professional, high contrast)
9. All text must be properly aligned and fully visible without interaction
10. Return ONLY the clean HTML code with embedded CSS/JS
"""            }
        ]
        
        visualization_response = client.chat.completions.create(
            model="gpt-4.1",
            messages=visualization_messages,
            temperature=0.2
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
        image_params = {
            "engine": "google_images",
            "q": query,
            "api_key": api_key,
        }

        search_results = GoogleSearch(image_params)
        image_html = generate_image_carousel_html(search_results.get_dict().get("images_results", []))


        
        return {"search_results": html_output, "graph": image_html}
    except Exception as e:
        print(f"Error during search: {str(e)}")
        return {"error": str(e)}
    

def send_email(to_email: str, subject: str, body: str, status: str = "", user_id: int = 0) -> dict:
    """
    Sends an email using Gmail SMTP server.
    
    Args:
        to_email (str): The recipient's email address
        subject (str): The subject of the email
        body (str): The body content of the email
        status (str, optional): Status message for tracking. Defaults to "".
        user_id (int, optional): User ID for status updates. Defaults to 0.
        
    Returns:
        dict: A dictionary containing either success message or error details
        
    Raises:
        ValueError: If email credentials are not set or if required fields are empty
        SMTPAuthenticationError: If email authentication fails
        SMTPException: For other SMTP-related errors
    """
    # Validate required fields
    if not to_email or not subject or not body:
        return {"error": "Email, subject, and body are required"}
        
    # Basic email format validation
    if '@' not in to_email or '.' not in to_email:
        return {"error": "Invalid email format"}
    
    try:
        if user_id:
            set_status(user_id, status or "Sending email...", 1)

        if not all([DEFAULT_FROM_EMAIL, EMAIL_HOST_PASSWORD]):
            raise ValueError("DEFAULT_FROM_EMAIL and EMAIL_HOST_PASSWORD must be set in the environment variables")
        
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = DEFAULT_FROM_EMAIL
        msg["To"] = to_email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            print("Iniciando conexión con el servidor de correo")
            server.login(DEFAULT_FROM_EMAIL, EMAIL_HOST_PASSWORD)
            print("Login exitoso")
            server.send_message(msg)
            print(f"Email enviado a {to_email}")
        return {"success": 'Email enviado correctamente'}
    
    except smtplib.SMTPAuthenticationError as e:
        error_msg = "Error de autenticación del correo"
        print(f"{error_msg}: {str(e)}")
        return {"error": error_msg}
    except smtplib.SMTPException as e:
        error_msg = "Error en el servidor de correo"
        print(f"{error_msg}: {str(e)}")
        return {"error": error_msg}
    except Exception as e:
        print(f"Error al enviar el email: {str(e)}")
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
    
def generate_image_carousel_html(search_results, max_images=4):
    """
    Genera HTML para un carrusel de imágenes a partir de los resultados de búsqueda de SerpAPI.
    
    Args:
        search_results: Resultados obtenidos de la API de Google Image Search
        max_images: Número máximo de imágenes a mostrar (por defecto 4)
    
    Returns:
        String con HTML para el carrusel de imágenes
    """
    # Limitar a max_images resultados
    results = search_results[:max_images]
    
    if not results:
        return "<div class='no-results'>No se encontraron imágenes para esta búsqueda.</div>"
    
    # Generar HTML para el carrusel
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Resultados de Búsqueda de Imágenes</title>
        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
                background-color: #f8fafc;
                color: #1e293b;
            }
            
            .carousel-container {
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: white;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }
            
            .carousel-title {
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 16px;
                color: #334155;
                display: flex;
                align-items: center;
            }
            
            .carousel-title svg {
                margin-right: 8px;
            }
            
            .carousel {
                position: relative;
                overflow: hidden;
                border-radius: 8px;
            }
            
            .carousel-inner {
                display: flex;
                transition: transform 0.5s ease;
            }
            
            .carousel-item {
                min-width: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            
            .carousel-image {
                width: 100%;
                max-height: 400px;
                object-fit: contain;
                border-radius: 8px;
                background-color: #f1f5f9;
            }
            
            .carousel-caption {
                width: 100%;
                padding: 12px;
                text-align: center;
                font-size: 0.875rem;
                color: #64748b;
                max-width: 100%;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .carousel-indicators {
                display: flex;
                justify-content: center;
                margin-top: 16px;
                gap: 8px;
            }
            
            .carousel-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: #cbd5e1;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }
            
            .carousel-indicator.active {
                background-color: #2563eb;
                transform: scale(1.25);
            }
            
            .carousel-controls {
                position: absolute;
                top: 50%;
                left: 0;
                right: 0;
                transform: translateY(-50%);
                display: flex;
                justify-content: space-between;
                padding: 0 16px;
            }
            
            .carousel-control {
                width: 40px;
                height: 40px;
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                transition: all 0.2s ease;
            }
            
            .carousel-control:hover {
                background-color: white;
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            
            .carousel-attribution {
                margin-top: 12px;
                font-size: 0.75rem;
                color: #94a3b8;
                text-align: center;
            }
            
            .carousel-attribution a {
                color: #3b82f6;
                text-decoration: none;
            }
            
            @media (max-width: 640px) {
                .carousel-container {
                    padding: 12px;
                }
                
                .carousel-image {
                    max-height: 300px;
                }
            }
            
            /* Impresión */
            @media print {
                .carousel-container {
                    box-shadow: none;
                }
                
                .carousel-controls,
                .carousel-indicators {
                    display: none;
                }
                
                .carousel-inner {
                    display: block;
                }
                
                .carousel-item {
                    page-break-inside: avoid;
                    margin-bottom: 20px;
                }
            }
        </style>
    </head>
    <body>
        <div class="carousel-container">
            <h2 class="carousel-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                Resultados de imágenes
            </h2>
            <div class="carousel" id="imageCarousel">
                <div class="carousel-inner" id="carouselInner">
    """
    
    # Generar HTML para cada imagen
    for i, image in enumerate(results):
        # La estructura de los resultados es diferente para 'inline_images'
        title = image.get("title", "").replace('"', "&quot;").replace("'", "&#39;")
        source = image.get("source_name", image.get("source", ""))
        # Usar 'original' u 'thumbnail' según disponibilidad
        image_url = image.get("original", image.get("thumbnail", ""))
        source_url = image.get("source", "")
        
        html += f"""
                    <div class="carousel-item" id="slide{i}">
                        <img src="{image_url}" alt="{title}" class="carousel-image" />
                        <div class="carousel-caption">
                            {title}
                            <div class="text-xs text-gray-500">Fuente: {source}</div>
                        </div>
                    </div>
        """
    
    # Añadir indicadores y controles
    html += """
                </div>
                <div class="carousel-controls">
                    <div class="carousel-control" id="prevButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                    </div>
                    <div class="carousel-control" id="nextButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                    </div>
                </div>
                <div class="carousel-indicators" id="indicators">
    """
    
    # Generar indicadores
    for i in range(len(results)):
        active = "active" if i == 0 else ""
        html += f'<div class="carousel-indicator {active}" data-slide="{i}"></div>'
    
    # Cerrar el HTML con JavaScript para el carrusel
    html += """
                </div>
            </div>
            <div class="carousel-attribution">
                Imágenes proporcionadas a través de Google Image Search
            </div>
        </div>
        
        <script>
            // Carousel functionality
            document.addEventListener('DOMContentLoaded', function() {
                const carousel = document.getElementById('imageCarousel');
                const inner = document.getElementById('carouselInner');
                const indicators = document.querySelectorAll('.carousel-indicator');
                const prevButton = document.getElementById('prevButton');
                const nextButton = document.getElementById('nextButton');
                
                let currentSlide = 0;
                const slideCount = indicators.length;
                
                // Function to show a specific slide
                function showSlide(index) {
                    // Handle boundary cases
                    if (index < 0) index = slideCount - 1;
                    if (index >= slideCount) index = 0;
                    
                    // Update current slide
                    currentSlide = index;
                    
                    // Update carousel position
                    inner.style.transform = `translateX(-${currentSlide * 100}%)`;
                    
                    // Update indicators
                    indicators.forEach((indicator, i) => {
                        if (i === currentSlide) {
                            indicator.classList.add('active');
                        } else {
                            indicator.classList.remove('active');
                        }
                    });
                }
                
                // Set up controls
                prevButton.addEventListener('click', () => {
                    showSlide(currentSlide - 1);
                });
                
                nextButton.addEventListener('click', () => {
                    showSlide(currentSlide + 1);
                });
                
                // Set up indicators
                indicators.forEach((indicator, index) => {
                    indicator.addEventListener('click', () => {
                        showSlide(index);
                    });
                });
                
                // Auto-advance carousel every 5 seconds
                let autoplayInterval = setInterval(() => {
                    showSlide(currentSlide + 1);
                }, 5000);
                
                // Pause autoplay when hovering over carousel
                carousel.addEventListener('mouseenter', () => {
                    clearInterval(autoplayInterval);
                });
                
                // Resume autoplay when mouse leaves
                carousel.addEventListener('mouseleave', () => {
                    autoplayInterval = setInterval(() => {
                        showSlide(currentSlide + 1);
                    }, 5000);
                });
                
                // Handle keyboard navigation
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'ArrowLeft') {
                        showSlide(currentSlide - 1);
                    } else if (e.key === 'ArrowRight') {
                        showSlide(currentSlide + 1);
                    }
                });
                
                // Initialize first slide
                showSlide(0);
            });
            
            // Message parent frame when an image is clicked (for full screen viewing)
            document.querySelectorAll('.carousel-image').forEach(img => {
                img.addEventListener('click', function() {
                    // Check if we're in an iframe
                    if (window.parent !== window) {
                        window.parent.postMessage({
                            type: 'view-image',
                            src: this.src,
                            alt: this.alt
                        }, '*');
                    }
                });
            });
        </script>
    </body>
    </html>
    """
    
    return html

def generate_roles_carousel_html(auto_slide_interval=3000):
    """
    Genera HTML para un carrusel de imágenes de los 5 roles del sistema.
    
    Args:
        auto_slide_interval: Intervalo en milisegundos para el cambio automático de diapositivas
    
    Returns:
        String con HTML para el carrusel de imágenes de roles
    """
    # Lista de roles con sus imágenes y datos usando URLs de Backblaze B2
    base_url = "https://f005.backblazeb2.com/file/prueba-2"
    
    roles = [
        {
            "id": "researcher",
            "title": "Investigador",
            "description": "Investiga y analiza información de diversas fuentes académicas y científicas.",
            "image": f"{base_url}/Research_AF.jpeg",
            "color": "#172554"  # bg-blue-950
        },
        {
            "id": "receptionist",
            "title": "Recepcionista",
            "description": "Gestiona citas, visitantes y espacios comunes con facilidad.",
            "image": f"{base_url}/Receptionist_AF.jpeg",
            "color": "#059669"  # bg-emerald-600
        },
        {
            "id": "trainer",
            "title": "Entrenador de Habilidades",
            "description": "Mejora tus habilidades personales y profesionales con práctica interactiva.",
            "image": f"{base_url}/Personal_Trainer_AF.jpeg",
            "color": "#d97706"  # bg-amber-600
        },
        {
            "id": "assistant",
            "title": "Asistente Personal",
            "description": "Gestiona tu agenda, comunicaciones y tareas diarias de forma eficiente.",
            "image": f"{base_url}/Personal_Assistant_AF.jpeg",
            "color": "#9333ea"  # bg-purple-600
        },
        {
            "id": "guide",
            "title": "Guía Universitario",
            "description": "Navega la vida académica con un asistente especializado en recursos universitarios.",
            "image": f"{base_url}/University_guide_AF.jpeg",
            "color": "#dc2626"  # bg-red-600
        }
    ]
    
    # Generar HTML para el carrusel con manejo más robusto de las imágenes
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Roles de NAIA</title>
        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
                background-color: #f8fafc;
                color: #1e293b;
            }
            
            .carousel-container {
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: white;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }
            
            .carousel-title {
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 16px;
                color: #334155;
                display: flex;
                align-items: center;
            }
            
            .carousel-title svg {
                margin-right: 8px;
            }
            
            .carousel {
                position: relative;
                overflow: hidden;
                border-radius: 12px;
            }
            
            .carousel-inner {
                display: flex;
                transition: transform 0.5s ease;
            }
            
            .carousel-item {
                min-width: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                position: relative;
            }
            
            .carousel-image-container {
                position: relative;
                width: 100%;
                height: 400px;
                overflow: hidden;
                background-color: #f1f5f9;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 8px 8px 0 0;
            }
            
            .carousel-image {
                max-width: 100%;
                max-height: 100%;
                width: auto;
                height: auto;
                object-fit: contain;
                border-radius: 8px 8px 0 0;
            }
            
            /* Diseño tipo "Made in Uninorte" */
            .made-in-uninorte {
                position: absolute;
                top: 0;
                left: 0;
                width: 150px;
                height: 150px;
                overflow: hidden;
                z-index: 5;
            }
            
            .made-in-uninorte::before {
                content: 'MADE IN UNINORTE';
                position: absolute;
                top: 30px;
                left: -20px;
                transform: rotate(-45deg);
                background-color: rgba(190, 30, 45, 0.85);
                color: white;
                padding: 5px 50px;
                font-weight: bold;
                font-size: 12px;
                letter-spacing: 1px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            
            /* Fallback para imagen que no carga */
            .carousel-fallback {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                background-size: cover;
                background-position: center;
                color: white;
                font-weight: bold;
                font-size: 2rem;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            
            .carousel-overlay {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(to bottom, transparent, rgba(0,0,0,0.7));
                padding: 30px 20px 20px;
                border-radius: 0 0 8px 8px;
                z-index: 4;
            }
            
            .carousel-caption {
                color: white;
                text-align: center;
                text-shadow: 0 1px 2px rgba(0,0,0,0.5);
            }
            
            .carousel-caption h3 {
                font-size: 1.75rem;
                font-weight: 700;
                margin-bottom: 8px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            
            .carousel-caption p {
                font-size: 1rem;
                opacity: 0.9;
                max-width: 600px;
                margin: 0 auto;
                text-shadow: 0 1px 2px rgba(0,0,0,0.3);
            }
            
            .role-badge {
                position: absolute;
                top: 16px;
                right: 16px;
                padding: 6px 12px;
                border-radius: 20px;
                color: white;
                font-weight: 600;
                font-size: 0.875rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                z-index: 10;
            }
            
            .carousel-indicators {
                display: flex;
                justify-content: center;
                margin-top: 16px;
                gap: 8px;
            }
            
            .carousel-indicator {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background-color: #cbd5e1;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .carousel-indicator.active {
                width: 24px;
                border-radius: 12px;
                transform: scale(1);
            }
            
            .carousel-controls {
                position: absolute;
                top: 50%;
                left: 0;
                right: 0;
                transform: translateY(-50%);
                display: flex;
                justify-content: space-between;
                padding: 0 16px;
                pointer-events: none;
            }
            
            .carousel-control {
                width: 40px;
                height: 40px;
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 2px 6px rgba(0,0,0,0.2);
                transition: all 0.2s ease;
                pointer-events: auto;
                z-index: 20;
            }
            
            .carousel-control:hover {
                background-color: white;
                box-shadow: 0 4px 8px rgba(0,0,0,0.25);
                transform: scale(1.05);
            }
            
            .carousel-attribution {
                margin-top: 12px;
                font-size: 0.75rem;
                color: #94a3b8;
                text-align: center;
            }
            
            @media (max-width: 640px) {
                .carousel-container {
                    padding: 12px;
                }
                
                .carousel-image-container {
                    height: 300px;
                }
                
                .carousel-caption h3 {
                    font-size: 1.5rem;
                }
                
                .carousel-caption p {
                    font-size: 0.875rem;
                }
                
                .made-in-uninorte::before {
                    font-size: 10px;
                    top: 20px;
                    left: -30px;
                }
            }
        </style>
    </head>
    <body>
        <div class="carousel-container">
            <h2 class="carousel-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                Roles disponibles en NAIA
            </h2>
            <div class="carousel" id="rolesCarousel">
                <div class="carousel-inner" id="carouselInner">
    """
    
    # Generar HTML para cada rol con manejo de errores en imágenes
    for i, role in enumerate(roles):
        html += f"""
                    <div class="carousel-item" id="slide{i}">
                        <div class="made-in-uninorte"></div>
                        <div class="role-badge" style="background-color: {role['color']}">
                            {role['title']}
                        </div>
                        <div class="carousel-image-container" style="background-color: {role['color']}20;">
                            <img 
                                src="{role['image']}" 
                                alt="{role['title']}" 
                                class="carousel-image" 
                                onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                            />
                            <div class="carousel-fallback" 
                                 style="display: none; background-color: {role['color']};">
                                <span>{role['title']}</span>
                            </div>
                            <div class="carousel-overlay">
                                <div class="carousel-caption">
                                    <h3>{role['title']}</h3>
                                    <p>{role['description']}</p>
                                </div>
                            </div>
                        </div>
                    </div>
        """
    
    # Añadir indicadores y controles
    html += """
                </div>
                <div class="carousel-controls">
                    <div class="carousel-control" id="prevButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                    </div>
                    <div class="carousel-control" id="nextButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                    </div>
                </div>
                <div class="carousel-indicators" id="indicators">
    """
    
    # Generar indicadores con colores personalizados para cada rol
    for i, role in enumerate(roles):
        active = "active" if i == 0 else ""
        html += f'<div class="carousel-indicator {active}" data-slide="{i}" style="background-color: {role["color"] if active else "#cbd5e1"}"></div>'
    
    # Cerrar el HTML con JavaScript para el carrusel
    # Usamos un string de formato con la variable auto_slide_interval
    html += f"""
                </div>
            </div>
            <div class="carousel-attribution">
                Selecciona un rol para empezar a usar NAIA
            </div>
        </div>
        
        <script>
            // Carousel functionality
            document.addEventListener('DOMContentLoaded', function() {{
                const carousel = document.getElementById('rolesCarousel');
                const inner = document.getElementById('carouselInner');
                const indicators = document.querySelectorAll('.carousel-indicator');
                const prevButton = document.getElementById('prevButton');
                const nextButton = document.getElementById('nextButton');
                
                // Colores de los roles para los indicadores
                const roleColors = [
                    "#172554", // Investigador (blue-950)
                    "#059669", // Recepcionista (emerald-600)
                    "#d97706", // Entrenador (amber-600)
                    "#9333ea", // Asistente (purple-600)
                    "#dc2626"  // Guía (red-600)
                ];
                
                let currentSlide = 0;
                const slideCount = indicators.length;
                
                // Function to show a specific slide
                function showSlide(index) {{
                    // Handle boundary cases
                    if (index < 0) index = slideCount - 1;
                    if (index >= slideCount) index = 0;
                    
                    // Update current slide
                    currentSlide = index;
                    
                    // Update carousel position with smooth animation
                    inner.style.transform = `translateX(-${{currentSlide * 100}}%)`;
                    
                    // Update indicators
                    indicators.forEach((indicator, i) => {{
                        if (i === currentSlide) {{
                            indicator.classList.add('active');
                            indicator.style.backgroundColor = roleColors[i];
                        }} else {{
                            indicator.classList.remove('active');
                            indicator.style.backgroundColor = "#cbd5e1";
                        }}
                    }});
                }}
                
                // Set up controls
                prevButton.addEventListener('click', () => {{
                    showSlide(currentSlide - 1);
                }});
                
                nextButton.addEventListener('click', () => {{
                    showSlide(currentSlide + 1);
                }});
                
                // Set up indicators
                indicators.forEach((indicator, index) => {{
                    indicator.addEventListener('click', () => {{
                        showSlide(index);
                    }});
                    
                    // Add hover effect to show the role color
                    indicator.addEventListener('mouseenter', () => {{
                        if (index !== currentSlide) {{
                            indicator.style.backgroundColor = roleColors[index] + "80"; // Add transparency
                        }}
                    }});
                    
                    indicator.addEventListener('mouseleave', () => {{
                        if (index !== currentSlide) {{
                            indicator.style.backgroundColor = "#cbd5e1";
                        }}
                    }});
                }});
                
                // Auto-advance carousel every {auto_slide_interval} milliseconds
                let autoplayInterval = setInterval(() => {{
                    showSlide(currentSlide + 1);
                }}, {auto_slide_interval});
                
                // Handle keyboard navigation
                document.addEventListener('keydown', (e) => {{
                    if (e.key === 'ArrowLeft') {{
                        showSlide(currentSlide - 1);
                    }} else if (e.key === 'ArrowRight') {{
                        showSlide(currentSlide + 1);
                    }}
                }});
                
                // Initialize first slide
                showSlide(0);
                
                // Ensure images are displayed properly
                document.querySelectorAll('.carousel-image').forEach(img => {{
                    // Center image in container
                    function centerImage() {{
                        const container = img.parentElement;
                        if (img.naturalWidth > 0 && img.naturalHeight > 0) {{
                            // Image is loaded, apply proper sizing
                            img.style.maxWidth = '80%';  // Allow space around the image
                            img.style.maxHeight = '80%';
                        }}
                    }}
                    
                    if (img.complete) {{
                        centerImage();
                    }} else {{
                        img.onload = centerImage;
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    """
    
    return html

def explain_naia_roles(user_id, status, auto_slide_interval=3000):
    """
    Generates a carousel with the 5 NAIA roles and returns detailed role descriptions.
    
    Args:
        auto_slide_interval: Interval in milliseconds for auto-advancing slides
        user_id: The ID of the user requesting the role explanation
        status: A concise description of the task to be performed
        
    Returns:
        Dictionary with HTML for the roles carousel and detailed role descriptions
    """
    set_status(user_id, status, 1)  
    html_content = generate_roles_carousel_html(auto_slide_interval=auto_slide_interval)
    
    # Detailed information about each role based on official documentation
    roles_details = {
        "researcher": {
            "title": "Research Assistant",
            "description": "The Research Assistant role helps with document drafting, searching for academic articles, analyzing texts, and generating content. It offers professional support for research and academic writing tasks.",
            "capabilities": [
                "Literature search and citation management",
                "Academic writing assistance and document drafting",
                "Text analysis and comparative reviews",
                "Research methodology guidance",
                "Data visualization and presentation"
            ]
        },
        "receptionist": {
            "title": "Receptionist",
            "description": "The Receptionist role attends to visitors, manages reservations for common areas, sends messages, provides tourist information, and recommends restaurants and local events.",
            "capabilities": [
                "Visitor management and check-in assistance",
                "Scheduling and coordination of common spaces",
                "Message handling and communication",
                "Local information and recommendations",
                "Event coordination support"
            ]
        },
        "trainer": {
            "title": "Personal Skills Trainer",
            "description": "The Personal Skills Trainer helps improve communication, leadership, and teamwork through simulations, language practice, advice on clothing and posture, and provides personalized training summaries.",
            "capabilities": [
                "Communication skill development exercises",
                "Leadership and teamwork simulations",
                "Language practice and feedback",
                "Professional presentation guidance",
                "Personalized improvement tracking"
            ]
        },
        "assistant": {
            "title": "Personal Assistant",
            "description": "The Personal Assistant manages daily tasks such as sending emails, scheduling meetings, creating reminders, attending to visitors, providing agenda information, weather updates, and assisting with other administrative tasks.",
            "capabilities": [
                "Email and communication management",
                "Calendar and scheduling coordination",
                "Task and reminder tracking",
                "Information gathering and reporting",
                "Administrative workflow optimization"
            ]
        },
        "guide": {
            "title": "University Guide",
            "description": "The University Guide provides information about courses, events, activities, and campus locations, searches for data in university documentation, and sends relevant academic information to students' personal email addresses.",
            "capabilities": [
                "Campus navigation and location assistance",
                "Course and academic program information",
                "University event and activity updates",
                "Academic resources and documentation access",
                "Administrative procedures guidance"
            ]
        }
    }
    
    return {
        "graph": html_content,
        "title": "NAIA's Available Roles",
        "roles_info": roles_details,
        "context": "NAIA (Nimble Artificial Intelligence Assistant) is a multimodal, multirole assistant designed to provide personalized assistance in the university environment. NAIA integrates multiple AI tools including language models, facial recognition, image description, and voice-to-text/text-to-voice conversion. With its visual capabilities, NAIA can make observations about the environment, enriching interaction. These five roles help address different needs within the university community, reducing stress and mental fatigue associated with work overload."
    }