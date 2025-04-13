from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.researcher.services import DocumentService
from django.utils.cache import patch_response_headers
from django.core.cache import cache
from rest_framework.decorators import api_view
from apps.researcher.functions import save_user_document_for_rag
class ResearchDocumentView(APIView):
    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            document = request.FILES.get('document')
            
            if not user_id or not document:
                return Response({"error": "user_id and document are required"}, status=status.HTTP_400_BAD_REQUEST)
            # Check if file is a PDF
            if document.content_type != 'application/pdf':
                return Response({"error":"The file must be a pdf"}, status=status.HTTP_400_BAD_REQUEST)

            document_service = DocumentService()
            result = document_service.upload_document(user_id, document)
            
            return Response({"message": f"File uploaded", "info": result}, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        try:
            user_id = request.query_params.get('user_id')
            
            if not user_id:
                return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            cache_key = f'user_documents_{user_id}'

            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data, status=status.HTTP_200_OK)
            
            document_service = DocumentService()
            documents = document_service.user_documents_list(user_id)
            
            cache.set(cache_key, {"documents": documents}, timeout=60*60)

            response = Response({"documents": documents}, status=status.HTTP_200_OK)
            patch_response_headers(response, cache_timeout=60*60)
            
            return response
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        try:
            file_id = request.query_params.get('file_id')
            file_name = request.query_params.get('file_name')
            user_id = request.query_params.get('user_id')
            
            if not file_id:
                return Response({"error": "file_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            document_service = DocumentService()
            result = document_service.delete_document_by_id(file_id, file_name, user_id)
            
            return Response({"message": "File deleted", "info": result}, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(["POST"])
def save_document_changes(request):
    try:
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        document_service = DocumentService()
        documents = document_service.retrieve_user_document_for_rag(user_id)
        save_user_document_for_rag(documents, user_id)
        document_service.invalidate_cache(user_id)
        response = Response({"message": "Changes made successfully"}, status=status.HTTP_200_OK)
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)