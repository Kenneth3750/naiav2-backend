# uni_rag.py
import os
import sys
from dotenv import load_dotenv
import shutil
import django

if __name__ == "__main__":
    # Cargar variables de entorno
    load_dotenv()

    # Configurar el módulo de settings de Django (ajusta el nombre según tu proyecto)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naia.settings.dev')
    openai_api_key = os.getenv("open_ai")
    os.environ["OPENAI_API_KEY"] = openai_api_key
    # Inicializar Django antes de cualquier importación de apps
    django.setup()

    # Ahora puedes importar código que depende de Django
    from apps.uniguide.functions import create_rag, query_university_rag
    from apps.recepcionist.functions import create_recepcionist_rag, query_recepcionist_rag

    # Borrar carpeta si existe
    # chromadb_path = os.path.join(os.path.dirname(__file__), 'chromadb_recepcionist')
    # if os.path.exists(chromadb_path) and os.path.isdir(chromadb_path):
    #     shutil.rmtree(chromadb_path)
    #     print(f"Deleted existing chromadb_recepcionist folder at {chromadb_path}")
    chromadb_path = os.path.join(os.path.dirname(__file__), 'chromadb_uniguide')
    if os.path.exists(chromadb_path) and os.path.isdir(chromadb_path):
        shutil.rmtree(chromadb_path)
        print(f"Deleted existing chromadb_uniguide folder at {chromadb_path}")

    # Ejecutar funciones
    create_rag()
    # create_recepcionist_rag()

    # query = "Cuales son los precios del menu del plaza??"
    # response = query_recepcionist_rag(user_id=1, question=query, k=2, status="Guayando")
    # print(f"Response for query '{query}': {response}")
