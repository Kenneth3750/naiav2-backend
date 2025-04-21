from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.status.services import update_operation_status

class StatusView(APIView):
    """
    API view to check the status of the server.
    """

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to check the server status.
        """
        try:
            user_id = request.query_params.get('user_id')
            role_id = request.query_params.get('role_id')
            if not user_id or not role_id:
                return Response({"error": "user_id and role_id are required"}, status=status.HTTP_400_BAD_REQUEST)
            status_code = update_operation_status(user_id, role_id)
            return Response({"status": status_code}, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)