from rest_framework import serializers
from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100)
    family_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    photo_url = serializers.URLField()

    class Meta:
        model = User
        fields = '__all__'