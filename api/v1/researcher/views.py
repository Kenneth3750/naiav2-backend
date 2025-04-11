from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from apps.researcher.services import DocumentService

@api_view(["POST"])
def upload_research_document(request):
    try:
        user_id = request.data.get('user_id')
        document = request.FILES.get('document')
        
        if not user_id or not document:
            return Response({"error": "user_id y document son requeridos"}, status=status.HTTP_400_BAD_REQUEST)
        # Check if file is a PDF
        if document.content_type != 'application/pdf':
            return Response({"error": "El archivo debe ser un PDF"}, status=status.HTTP_400_BAD_REQUEST)

        document_service = DocumentService()
        result = document_service.upload_document(user_id, document)
        
        return Response({"message": f"File uploaded", "info": result}, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)