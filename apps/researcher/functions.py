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

def scholar_search(query="machine learning healthcare", num_results=3, status="", user_id=0):
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
    params = {
        "engine": "google_scholar",
        "q": query,
        "api_key": api_key,
        "num": num_results,
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
        return convert_to_html(search_result)

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


def write_document(query, context="", user_id=0, status="", role_id=0):
    """
    This feature is responsible for generating specific documents 
    based on the topic the user is consulting.
    """
    load_dotenv()
    set_status(user_id, status, 1)
    client = OpenAI(api_key=os.getenv("open_ai"))
    try:

        messages = [
            {
                "role": "system",
                "content": "You are an expert creating scientific documents. Generate comprehensive, well-structured academic content in markdown format with proper headings, citations, and detailed explanations.",
            }
        ]

        if context:
            messages.append(
                {"role": "user", "content": f"here are some context about {context}"}
            )

        messages.append(
            {"role": "user", "content": f"Generate a document based on this topic {query}"}
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




def answer_from_user_rag(user_id: int, pregunta: str, k: int = 3, status:str = "", role_id: int = 0) -> dict:
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
