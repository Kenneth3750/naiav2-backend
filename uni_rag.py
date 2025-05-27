from apps.uniguide.functions import create_rag, query_rag


if __name__ == "__main__":
    import os
    import sys
    from dotenv import load_dotenv
    import shutil
    load_dotenv()
    
    # Delete chromadb_uniguide folder if it exists
    chromadb_path = os.path.join(os.path.dirname(__file__), 'chromadb_uniguide')
    if os.path.exists(chromadb_path) and os.path.isdir(chromadb_path):
        shutil.rmtree(chromadb_path)
        print(f"Deleted existing chromadb_uniguide folder at {chromadb_path}")

    

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    create_rag()

    query = "¿Cómo puedo actualizar mi documento de identidad?"
    response = query_rag(user_id = 1, question = query, k = 2, status = "Guayando")
    print(f"Response for query '{query}': {response}")