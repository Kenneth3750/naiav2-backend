from rest_framework import serializers


class ChatSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    user_input = serializers.CharField()
    thread_id = serializers.CharField()
    assistant_id = serializers.CharField()