from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status




class UniGuideAnalysisView(APIView):
    def post(self, request):
        try:
            form_data = request.POST.dict()
            user_id = form_data.get('user_id')
            print(type(form_data))
            print("Received form data:", form_data)

            if not user_id:
                return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({"message": "Form data received successfully", "data": form_data}, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
