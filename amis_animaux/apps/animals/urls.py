from django.urls import path
from .views import MyAnimalsListCreateView

urlpatterns = [
    path("me/", MyAnimalsListCreateView.as_view(), name="my_animals"),
]
