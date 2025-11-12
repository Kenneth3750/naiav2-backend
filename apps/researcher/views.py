from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .functions import (
    scholar_search,
    write_document,
    answer_from_user_rag,
    factual_web_query,
    create_graph,
    send_email,
    get_current_news,
    explain_naia_roles,
    deep_content_analysis_for_specific_information
)


@api_view(['POST'])
def search_academic_papers(request):
    """Search for academic papers using Google Scholar"""
    try:
        query = request.data.get('query')
        query_2 = request.data.get('query_2', '')
        num_results = request.data.get('num_results', 3)
        status_msg = request.data.get('status', 'Searching for academic papers...')
        user_id = request.data.get('user_id', 1)
        language1 = request.data.get('language1', 'en')
        language2 = request.data.get('language2', 'en')

        if not query:
            return Response({'error': 'query is required'}, status=status.HTTP_400_BAD_REQUEST)

        result = scholar_search(query, query_2, num_results, status_msg, user_id, language1, language2)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_document(request):
    """Create written documents of any type"""
    try:
        query = request.data.get('query')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')
        document_type = request.data.get('document_type')
        use_internet = request.data.get('use_internet')
        use_rag = request.data.get('use_rag')
        context = request.data.get('context', '')
        query_for_references = request.data.get('query_for_references', 'None')
        num_results = request.data.get('num_results', 5)
        language_for_references = request.data.get('language_for_references', 'en')
        specific_documents = request.data.get('specific_documents', [])

        if not all([query, user_id, status_msg, document_type, use_internet is not None, use_rag is not None]):
            return Response(
                {'error': 'query, user_id, status, document_type, use_internet, and use_rag are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = write_document(
            query=query,
            context=context,
            user_id=user_id,
            status=status_msg,
            query_for_references=query_for_references,
            language_for_references=language_for_references,
            num_results=num_results,
            document_type=document_type,
            use_internet=use_internet,
            use_rag=use_rag,
            specific_documents=specific_documents
        )
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def search_user_documents(request):
    """Search within user's uploaded PDF documents"""
    try:
        user_id = request.data.get('user_id')
        pregunta = request.data.get('pregunta')
        status_msg = request.data.get('status')
        k = request.data.get('k', 3)
        specific_documents = request.data.get('specific_documents', [])

        if not all([user_id, pregunta, status_msg]):
            return Response(
                {'error': 'user_id, pregunta, and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = answer_from_user_rag(user_id, pregunta, k, status_msg, specific_documents)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def search_web(request):
    """Search the internet for factual information"""
    try:
        query = request.data.get('query')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status', 'Searching the web...')

        if not all([query, user_id]):
            return Response({'error': 'query and user_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        result = factual_web_query(query, status_msg, user_id)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def generate_graph(request):
    """Create academic graphs and visualizations"""
    try:
        user_query = request.data.get('user_query')
        information_for_graph = request.data.get('information_for_graph')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')
        internet_is_required = request.data.get('internet_is_required')

        if not all([user_query, information_for_graph, user_id, status_msg, internet_is_required is not None]):
            return Response(
                {'error': 'user_query, information_for_graph, user_id, status, and internet_is_required are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = create_graph(user_query, information_for_graph, user_id, status_msg, internet_is_required)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def send_user_email(request):
    """Send email to user or specified address"""
    try:
        to_email = request.data.get('to_email')
        subject = request.data.get('subject')
        body = request.data.get('body')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status', 'Sending email...')

        if not all([to_email, subject, body, user_id]):
            return Response(
                {'error': 'to_email, subject, body, and user_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = send_email(to_email, subject, body, status_msg, user_id)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def get_current_news(request):
    """Get latest news from a specific location"""
    try:
        location = request.data.get('location')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')
        query = request.data.get('query')
        language = request.data.get('language')

        if not all([location, user_id, status_msg, query, language]):
            return Response(
                {'error': 'location, user_id, status, query, and language are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = get_current_news(location, user_id, status_msg, query, language)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def explain_roles(request):
    """Explain NAIA roles and capabilities"""
    try:
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')

        if not all([user_id, status_msg]):
            return Response({'error': 'user_id and status are required'}, status=status.HTTP_400_BAD_REQUEST)

        result = explain_naia_roles(user_id, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def deep_content_analysis(request):
    """Deep content analysis for specific information"""
    try:
        url = request.data.get('url')
        user_query = request.data.get('user_query')
        user_id = request.data.get('user_id')
        status_msg = request.data.get('status')

        if not all([url, user_query, user_id, status_msg]):
            return Response(
                {'error': 'url, user_query, user_id, and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = deep_content_analysis_for_specific_information(url, user_query, user_id, status_msg)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
