from django.db import models
from apps.users.models import User

class SkillCategory(models.Model):
    name = models.CharField(max_length=100)  # "Entrevistas", "Presentaciones", etc.
    description = models.TextField()
    icon = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Skill Categories"

class TrainingSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=50) 
    skill_category = models.ForeignKey(SkillCategory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    session_data = models.JSONField()  
    feedback = models.TextField() 
    session_html = models.TextField() 
    
    def __str__(self):
        return f"{self.user.name} - {self.session_type} - {self.created_at.strftime('%Y-%m-%d')}"
    
    class Meta:
        ordering = ['-created_at']

class SkillFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE)
    strengths = models.JSONField()  # ["Buena comunicación", "Confianza"]
    improvements = models.JSONField()  # ["Trabajar en postura", "Practicar más"]
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback for {self.user.name} - {self.session.session_type}"
    
    class Meta:
        ordering = ['-created_at']

class TrainingReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    report_html = models.TextField()  # Dashboard/reporte completo
    sessions_included = models.ManyToManyField(TrainingSession)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.name}"
    
    class Meta:
        ordering = ['-created_at']