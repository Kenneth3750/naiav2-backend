from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.uniguide.functions import (
    why_is_uninorte_at_the_top,
    engineering_opportunities_at_uninorte,
    electrical_electronic_engineering_future,
    inscription_process_for_engineering
)




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


class WhyUninorteTopView(APIView):
    def post(self, request):
        try:
            result = why_is_uninorte_at_the_top()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EngineeringOpportunitiesView(APIView):
    def post(self, request):
        try:
            result = engineering_opportunities_at_uninorte()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ElectricalEngineeringFutureView(APIView):
    def post(self, request):
        try:
            result = electrical_electronic_engineering_future()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InscriptionProcessView(APIView):
    def post(self, request):
        try:
            result = inscription_process_for_engineering()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
