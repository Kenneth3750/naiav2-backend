from apps.uniguide.functions import create_rag, query_university_rag
from apps.recepcionist.functions import create_recepcionist_rag, query_recepcionist_rag


if __name__ == "__main__":
    import os
    import sys
    from dotenv import load_dotenv
    import shutil
    load_dotenv()
    
    # Delete chromadb_uniguide folder if it exists
    chromadb_path = os.path.join(os.path.dirname(__file__), 'chromadb_recepcionist')
    if os.path.exists(chromadb_path) and os.path.isdir(chromadb_path):
        shutil.rmtree(chromadb_path)
        print(f"Deleted existing chromadb_recepcionist folder at {chromadb_path}")

    

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    create_recepcionist_rag()

    query = "Cuales son los precios del menu del plaza??"
    response = query_recepcionist_rag(user_id = 1, question = query, k = 2, status = "Guayando")
    print(f"Response for query '{query}': {response}")