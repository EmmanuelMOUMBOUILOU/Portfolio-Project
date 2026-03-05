from django.urls import path
from .views import MatchListCreateView, MatchUpdateView

urlpatterns = [
    path("", MatchListCreateView.as_view(), name="match_list_create"),
    path("<int:pk>/", MatchUpdateView.as_view(), name="match_update"),
]
