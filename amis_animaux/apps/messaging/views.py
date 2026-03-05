from django.shortcuts import render
from django.db.models import Count
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


class ConversationListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        """
        Crée une conversation entre l'utilisateur connecté + un autre user (participant_id).
        Empêche de créer une conversation dupliquée à 2 participants.
        """
        user = self.request.user
        participant_id = serializer.validated_data.get("participant_id") or self.request.data.get("participant_id")

        if participant_id is None:
            raise ValidationError({"participant_id": "This field is required."})

        if str(user.id) == str(participant_id):
            raise ValidationError({"participant_id": "You cannot create a conversation with yourself."})

        # Vérifier si une conversation à 2 participants existe déjà
        existing = (
            Conversation.objects
            .filter(participants=user)
            .filter(participants__id=participant_id)
            .annotate(pcount=Count("participants"))
            .filter(pcount=2)
            .first()
        )
        if existing:
            # On renvoie l’existante en évitant la duplication
            # (Ici on peut lever une ValidationError avec l’ID existant)
            raise ValidationError({"detail": "Conversation already exists.", "conversation_id": existing.id})
        
        serializer.validated_data.pop("participant_id", None)

        convo = serializer.save()
        convo.participants.add(user, participant_id)


class MessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        conversation_id = self.kwargs["conversation_id"]
        convo = Conversation.objects.filter(id=conversation_id, participants=self.request.user).first()
        if not convo:
            raise PermissionDenied("You are not a participant of this conversation.")
        return Message.objects.filter(conversation=convo).order_by("timestamp")

    def perform_create(self, serializer):
        conversation_id = self.kwargs["conversation_id"]
        convo = Conversation.objects.filter(id=conversation_id, participants=self.request.user).first()
        if not convo:
            raise PermissionDenied("You are not a participant of this conversation.")
        serializer.save(conversation=convo, sender=self.request.user)
