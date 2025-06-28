from .models import TrainingReport
from apps.users.models import User
from django.forms.models import model_to_dict


class SkillsTrainerRepository:
    def list_user_training_reports(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            return TrainingReport.objects.filter(user=user).order_by('-created_at').values('title', 'created_at', 'id')
        except User.DoesNotExist:
            raise ValueError(f"User with id {user_id} does not exist")
    def get_training_report_by_id(self, report_id):
        try:
            report = TrainingReport.objects.get(id=report_id)
            return report.values() if hasattr(report, 'values') else model_to_dict(report)
        except TrainingReport.DoesNotExist:
            raise ValueError(f"Training report with id {report_id} does not exist")
