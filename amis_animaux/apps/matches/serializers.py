from rest_framework import serializers
from .models import Match


class MatchSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    receiver_username = serializers.CharField(source="receiver.username", read_only=True)

    class Meta:
        model = Match
        fields = (
            "id",
            "sender", "sender_username",
            "receiver", "receiver_username",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "sender", "status", "created_at")


class MatchUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ("status",)

    def validate_status(self, value):
        if value not in ("accepted", "rejected"):
            raise serializers.ValidationError("Status must be 'accepted' or 'rejected'.")
        return value
