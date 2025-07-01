from rest_framework.response import Response
from rest_framework import status
from apps.skills.services import SkillsTrainerDBService
from rest_framework.decorators import api_view


@api_view(['GET'])
def get_title_training_reports(requests, service = SkillsTrainerDBService()):
    try:
        user_id = requests.query_params.get('user_id')
        if not user_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        training_reports = service.list_user_training_reports(user_id)
        return Response(training_reports, status=status.HTTP_200_OK)
    except Exception as e:
        print("Error in get_title_training_reports: ", str(e))
        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_training_report_by_id(requests, service = SkillsTrainerDBService()):
    try:
        report_id = requests.query_params.get('report_id')
        if not report_id:
            return Response({"error": "report_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        training_report = service.get_training_report_by_id(report_id)
        return Response(training_report, status=status.HTTP_200_OK)
    except Exception as e:
        print("Error in get_training_report_by_id: ", str(e))
        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

