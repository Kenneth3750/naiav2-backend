from rest_framework import serializers


class ChatSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(allow_null=False, required=True)
    user_input = serializers.CharField(allow_blank=False, required=False)
    thread_id = serializers.CharField(allow_blank=True, required=True)
    assistant_id = serializers.CharField(allow_blank=False, required=True)