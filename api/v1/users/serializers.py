from rest_framework import serializers
from apps.users.models import User

class UserSerializer(serializers.ModelSerializer):
    photo_url = serializers.CharField(allow_blank=True, required=False)
    
    class Meta:
        model = User
        fields = ('name', 'family_name', 'email', 'photo_url')
