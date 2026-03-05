from rest_framework import serializers
from .models import Animal


class AnimalSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Animal
        fields = ("id", "owner", "owner_username", "name", "species", "age", "created_at")
        read_only_fields = ("id", "owner", "created_at")
