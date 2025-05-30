from rest_framework import serializers


class ChatSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(allow_null=False, required=True)
    user_input = serializers.CharField(allow_blank=False, required=False)
    role_id = serializers.IntegerField(allow_null=False, required=True)

class ChatMessagesSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(allow_null=False, required=True)
    role_id = serializers.IntegerField(allow_null=False, required=True)
