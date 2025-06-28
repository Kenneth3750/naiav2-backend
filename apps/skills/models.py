from django.db import models
from apps.users.models import User

class TrainingReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200) 
    training_type = models.CharField(max_length=50) 
    report_html = models.TextField()  
    created_at = models.DateTimeField()  
    
    def __str__(self):
        return f"{self.title} - {self.user.name}"
    
    class Meta:
        ordering = ['-created_at']