from django.contrib.auth.models import User
from rest_framework import serializers

from apps.animals.models import Animal
from apps.users.models import Profile


class AnimalPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Animal
        fields = ("id", "name", "species", "age")


class UserSuggestionSerializer(serializers.ModelSerializer):
    bio = serializers.CharField(source="profile.bio", read_only=True)
    location = serializers.CharField(source="profile.location", read_only=True)
    animals = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "bio", "location", "animals")

    def get_animals(self, obj):
        animals = Animal.objects.filter(owner=obj).order_by("-created_at")
        return AnimalPublicSerializer(animals, many=True).data
