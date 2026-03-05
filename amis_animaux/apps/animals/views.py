from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Animal
from .serializers import AnimalSerializer


class MyAnimalsListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AnimalSerializer

    def get_queryset(self):
        return Animal.objects.filter(owner=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
