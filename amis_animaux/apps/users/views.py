from django.shortcuts import render
from rest_framework import generics, permissions
from .serializers import RegisterSerializer, ProfileSerializer
from .models import Profile
from django.db.models import Q

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class MyProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return Profile.objects.get(user=self.request.user)
