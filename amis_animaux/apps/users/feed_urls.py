from django.urls import path
from .feed_views import SuggestionsFeedView

urlpatterns = [
    path("suggestions/", SuggestionsFeedView.as_view(), name="feed_suggestions"),
]
