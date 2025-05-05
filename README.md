# naiav2-backend



# Keys for the function response: 
- For Researcher
    "display": if the response will be desplayed.
    "pdf": if the response will generate a pdf
    "resolved_rag": If the response comes from the rag 
    "graph": If the response is an html with a graph in it that can be converted to png/jpg
    "search_results": If the response comes from a google search


# Import commnads

shy linting = flake8 . --select=F401,E722 --exclude=.git,__pycache__,*/migrations/*,venv,env,deploy_server.py
clean requirements.txt = python clean.py
    