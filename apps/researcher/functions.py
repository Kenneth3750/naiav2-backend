import os

from dotenv import load_dotenv
from openai import OpenAI
from serpapi import GoogleSearch


def scholar_search(query="machine learning healthcare", num_results=3):
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


def write_document(query, context=""):
    """
    This feature is responsible for generating specific documents 
    based on the topic the user is consulting.
    """
    load_dotenv()
    client = OpenAI(api_key=os.getenv("open_ai"))

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
