from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination

from apps.animals.models import Animal
from apps.matches.models import Match
from .feed_serializers import UserSuggestionSerializer


class FeedPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 30


class SuggestionsFeedView(generics.ListAPIView):
    # ✅ RENDRE PUBLIC POUR TEST
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSuggestionSerializer
    pagination_class = FeedPagination

    def get_queryset(self):
        user = self.request.user
        qs = User.objects.exclude(id=user.id).order_by("-date_joined")

        # Option MVP : ne proposer que des users qui ont au moins 1 animal
        qs = qs.filter(animals__isnull=False).distinct()

        # Filtres simples via query params
        species = self.request.query_params.get("species")
        location = self.request.query_params.get("location")
        age_min = self.request.query_params.get("age_min")
        age_max = self.request.query_params.get("age_max")

        if location:
            qs = qs.filter(profile__location__icontains=location)

        if species:
            qs = qs.filter(animals__species__iexact=species)

        if age_min:
            qs = qs.filter(animals__age__gte=age_min)

        if age_max:
            qs = qs.filter(animals__age__lte=age_max)

        # Option avancée (recommandée) : exclure les users déjà "accepted" avec toi
        accepted = Match.objects.filter(
            Q(sender=user) | Q(receiver=user),
            status="accepted"
        ).values_list("sender_id", "receiver_id")

        # accepted est une liste de paires (sender, receiver)
        # On en extrait tous les IDs concernés sauf toi
        excluded_ids = set()
        for s_id, r_id in accepted:
            if s_id != user.id:
                excluded_ids.add(s_id)
            if r_id != user.id:
                excluded_ids.add(r_id)

        if excluded_ids:
            qs = qs.exclude(id__in=list(excluded_ids))

        return qs
