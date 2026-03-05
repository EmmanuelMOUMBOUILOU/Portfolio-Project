from rest_framework import serializers
from .models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    participants_usernames = serializers.SerializerMethodField()
    participant_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Conversation
        fields = ("id", "participants", "participants_usernames", "participant_id", "created_at")
        read_only_fields = ("id", "participants", "participants_usernames", "created_at")

    def get_participants_usernames(self, obj):
        return [u.username for u in obj.participants.all()]


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model = Message
        fields = ("id", "conversation", "sender", "sender_username", "content", "timestamp")
        read_only_fields = ("id", "conversation", "sender", "timestamp")
