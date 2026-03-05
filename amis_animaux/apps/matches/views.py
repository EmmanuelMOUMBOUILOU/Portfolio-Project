from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Match
from .serializers import MatchSerializer, MatchUpdateSerializer


class MatchListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MatchSerializer

    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(Q(sender=user) | Q(receiver=user)).order_by("-created_at")

    def perform_create(self, serializer):
        user = self.request.user
        receiver = self.request.data.get("receiver")

        if receiver is None:
            raise ValidationError({"receiver": "This field is required."})

        if str(user.id) == str(receiver):
            raise ValidationError({"receiver": "You cannot match with yourself."})

        serializer.save(sender=user, status="pending")


class MatchUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Match.objects.all()
    serializer_class = MatchUpdateSerializer

    def perform_update(self, serializer):
        match = self.get_object()
        user = self.request.user

        # Seul le receiver peut accepter/refuser
        if match.receiver != user:
            raise PermissionDenied("Only the receiver can update this match.")

        serializer.save()